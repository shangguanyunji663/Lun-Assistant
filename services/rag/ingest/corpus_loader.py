"""语料入库：模拟文献库构建 + 分块 + 向量化 + BM25 索引重建。"""
import logging
import re
from pathlib import Path

from sqlalchemy import delete, func, select

from infrastructure.db import get_session_factory
from infrastructure.models.memory import MemoryItem
from services.llm.provider import LLMProvider
from services.rag.retriever import hybrid_retriever

logger = logging.getLogger("lunjiang.ingest")

from infrastructure.paths import PROJECT_ROOT
CORPUS_DIR = PROJECT_ROOT / "data" / "corpus"


def chunk_text(text: str, size: int = 512, overlap: int = 64) -> list[str]:
    """按句边界的滑动窗口分块。"""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= size:
        return [text] if text else []
    sentences = re.split(r"(?<=[。！？.!?)])", text)
    chunks, buf = [], ""
    for s in sentences:
        if len(buf) + len(s) > size and buf:
            chunks.append(buf)
            buf = buf[-overlap:] if overlap < len(buf) else ""
        buf += s
    if buf:
        chunks.append(buf)
    return chunks


async def ingest_corpus(force: bool = False) -> dict:
    """读取 data/corpus/*.txt（每篇格式: 首行#标题, 次行#作者 来源, 正文），入库。"""
    provider = LLMProvider()
    async with get_session_factory()() as db:
        existing = await db.scalar(
            select(func.count()).select_from(MemoryItem).where(MemoryItem.kind == "document"))
        if existing and not force:
            return {"skipped": True, "documents": existing}
        if force:
            await db.execute(delete(MemoryItem).where(MemoryItem.kind == "document"))
            await db.commit()

    files = sorted(CORPUS_DIR.glob("*.txt"))
    if not files:
        return {"skipped": False, "documents": 0, "chunks": 0, "note": "语料目录为空"}

    total_chunks = 0
    batch_docs, batch_embs = [], []
    for fp in files:
        raw = fp.read_text(encoding="utf-8", errors="ignore")
        lines = raw.splitlines()
        title = lines[0].lstrip("# ").strip() if lines else fp.stem
        source = lines[1].lstrip("# ").strip() if len(lines) > 1 else ""
        body = "\n".join(lines[2:])
        for i, chunk in enumerate(chunk_text(body, int(_cfg("rag", "chunk_size", default=512)),
                                            int(_cfg("rag", "chunk_overlap", default=64)))):
            meta = {"title": title, "source": source, "file": fp.name, "chunk": i}
            batch_docs.append(MemoryItem(kind="document", content=chunk, meta=meta,
                                         importance=0.5, embedding=[0.0]))
            total_chunks += 1
            if len(batch_docs) >= 32:
                await _flush(db, provider, batch_docs, batch_embs)
                batch_docs.clear()
    if batch_docs:
        await _flush(db, provider, batch_docs, batch_embs)
        batch_docs.clear()

    await hybrid_retriever.rebuild_bm25()
    return {"skipped": False, "documents": len(files), "chunks": total_chunks}


async def _flush(db, provider, docs, embs):
    embs = await provider.embed([d.content for d in docs])
    for d, e in zip(docs, embs):
        d.embedding = e
    db.add_all(docs)
    await db.commit()
    docs.clear()


def _cfg(*keys, default=None):
    from infrastructure.config import get_value
    v = get_value(*keys, default=default)
    return v if v is not None else default
