"""项目级知识库入库流水线：上传 → 解析 → 分块 → 向量化 → 入库。

数据流（方案A）：
    KnowledgeDocument(文件元数据, knowledge_documents 表)
    MemoryItem(kind="user_doc", 向量分块, memory_items 表) ← 复用现有 RAG 全链路

要点：
- MD5 内容去重（同项目内重复文件直接跳过）；
- 分块复用 corpus_loader.chunk_text，保证与语料同一分块口径；
- 批量 embedding（32/批）减少 LLM 调用次数；
- 原始文件落盘 data/uploads/{project_id}/，供溯源与删除；
- 任一环节失败 → 文档记 status=failed + error，不污染检索结果。
"""
import asyncio
import logging
from pathlib import Path

from sqlalchemy import and_, delete, func, select

from infrastructure.config import get_value
from infrastructure.db import get_session_factory
from infrastructure.models.knowledge import KnowledgeDocument
from infrastructure.models.memory import MemoryItem
from services.llm.provider import LLMProvider
from services.rag.ingest.corpus_loader import chunk_text
from services.rag.ingest.parsers import (
    DocumentParseError,
    infer_type,
    parse_document,
    sha256_fingerprint,
)

logger = logging.getLogger("lunjiang.ingest")

from infrastructure.paths import PROJECT_ROOT
_BATCH = 32  # 每批向量化条数


def _upload_root() -> Path:
    rel = get_value("rag", "knowledge", "upload_dir", default="data/uploads")
    root = Path(rel)
    return root if root.is_absolute() else PROJECT_ROOT / root


def _cfg(*keys, default=None):
    v = get_value(*keys, default=default)
    return v if v is not None else default


def _save_raw_file(project_id: int, doc_id: int, filename: str, data: bytes) -> Path:
    """原始文件落盘（目录按项目隔离）。"""
    folder = _upload_root() / str(project_id)
    folder.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._-") or "doc"
    path = folder / f"{doc_id}_{safe_name}"
    path.write_bytes(data)
    return path


# ---------------------------------------------------------------
# 单文件入库
# ---------------------------------------------------------------
async def ingest_document(*, db, project_id: int, user_id: int,
                          filename: str, data: bytes) -> dict:
    """单文档入库。返回 {"skipped"|"ready"|"failed", id, ...}

    调用方负责把解析的 CPU 密集段放进 to_thread（见 api 层封装）。
    """
    # 0. 类型推断 + 大小上限
    try:
        file_type = infer_type(filename, data)
    except DocumentParseError as e:
        return {"status": "failed", "error": str(e), "filename": filename}

    max_mb = int(get_value("rag", "max_upload_size_mb", default=20))
    if len(data) > max_mb * 1024 * 1024:
        return {"status": "failed",
                "error": f"文件超过 {max_mb}MB 上限", "filename": filename}

    content_hash = sha256_fingerprint(data)

    # 1. MD5 去重：同项目已有相同内容直接跳过
    dup = await db.scalar(
        select(KnowledgeDocument).where(
            KnowledgeDocument.project_id == project_id,
            KnowledgeDocument.content_hash == content_hash))
    if dup is not None:
        return {"status": "skipped", "id": dup.id, "filename": filename,
                "reason": "同项目已存在相同内容文件"}

    # 2. 建文件名记录（parsing 态）
    doc = KnowledgeDocument(project_id=project_id, user_id=user_id,
                            filename=filename, file_type=file_type,
                            size_bytes=len(data), content_hash=content_hash)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # 3. 解析（同步 CPU 密集，转入线程池避免阻塞事件循环；任何解析错误都转为 failed）
    try:
        parsed = await asyncio.to_thread(
            parse_document, file_type=file_type, data=data, filename=filename)
    except Exception as e:
        msg = str(e)[:300] if not isinstance(e, DocumentParseError) else str(e)
        doc.status, doc.error = "failed", msg
        await db.commit()
        return {"status": "failed", "id": doc.id, "filename": filename, "error": msg}

    # 4. 分块 + 批量向量化入库
    try:
        chunk_size = int(_cfg("rag", "chunk_size", default=512))
        overlap = int(_cfg("rag", "chunk_overlap", default=64))
        chunks = chunk_text(parsed.text, chunk_size, overlap)
        if not chunks:
            raise DocumentParseError("分块结果为空")
        await _embed_chunks(db=db, project_id=project_id, user_id=user_id,
                            doc_id=doc.id, filename=filename, chunks=chunks)
    except Exception as e:
        logger.exception("知识库文档向量化失败 doc=%s", filename)
        doc.status, doc.error = "failed", str(e)[:500]
        await db.commit()
        return {"status": "failed", "id": doc.id, "filename": filename,
                "error": str(e)[:200]}

    # 5. 收尾：原文件落盘 + 元数据定版
    _save_raw_file(project_id, doc.id, filename, data)
    doc.status = "ready"
    doc.chunk_count = len(chunks)
    doc.word_count = parsed.word_count
    await db.commit()
    logger.info("知识库入库成功 project=%s file=%s chunks=%d word=%d",
                project_id, filename, len(chunks), parsed.word_count)
    return {"status": "ready", "id": doc.id, "filename": filename,
            "chunks": len(chunks), "word_count": parsed.word_count,
            "title": parsed.title}


async def _embed_chunks(*, db, project_id: int, user_id: int, doc_id: int,
                        filename: str, chunks: list[str]) -> None:
    """分块批量向量化并写入 MemoryItem(kind="user_doc")。"""
    provider = LLMProvider()
    doc_key = f"udoc:{doc_id}"  # 相邻窗口/删除时定位同一来源
    for i in range(0, len(chunks), _BATCH):
        batch = chunks[i:i + _BATCH]
        embeddings = await provider.embed(batch)
        rows = [
            MemoryItem(
                project_id=project_id, user_id=user_id, kind="user_doc",
                content=text, embedding=vec, importance=0.6,
                meta={"filename": filename, "doc_id": doc_id, "chunk": i + j,
                      "doc_key": doc_key, "title": filename.rsplit('.', 1)[0]},
            )
            for j, (text, vec) in enumerate(zip(batch, embeddings))
        ]
        db.add_all(rows)
        await db.commit()


# ---------------------------------------------------------------
# 文档管理
# ---------------------------------------------------------------
async def list_documents(db, project_id: int) -> list[dict]:
    rows = (await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.project_id == project_id)
        .order_by(KnowledgeDocument.id.desc()))).scalars().all()
    return [{
        "id": d.id, "filename": d.filename, "file_type": d.file_type,
        "size_bytes": d.size_bytes, "status": d.status, "error": d.error,
        "chunk_count": d.chunk_count, "word_count": d.word_count,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    } for d in rows]


async def delete_document(db, doc: KnowledgeDocument) -> None:
    """删除文档：向量分块（按 doc_key 定位）+ 文件元数据 + 原始文件。"""
    doc_key = f"udoc:{doc.id}"

    await db.execute(delete(MemoryItem).where(and_(
        MemoryItem.kind == "user_doc",
        MemoryItem.project_id == doc.project_id,
        func.json_extract_path_text(MemoryItem.meta, "doc_key") == doc_key)))
    await db.delete(doc)
    await db.commit()
    raw = _upload_root() / str(doc.project_id)
    try:
        for fp in raw.glob(f"{doc.id}_*"):
            fp.unlink(missing_ok=True)
    except OSError:
        logger.warning("原始文件清理失败 doc=%s", doc.id, exc_info=True)


async def count_documents(db, project_id: int) -> int:
    return int(await db.scalar(
        select(func.count()).select_from(KnowledgeDocument)
        .where(KnowledgeDocument.project_id == project_id)) or 0)