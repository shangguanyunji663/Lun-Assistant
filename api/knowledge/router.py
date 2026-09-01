"""项目级私有知识库路由（上传/列表/删除/库内检索）。

入库流水线在 services/rag/ingest/pipeline.py；检索复用公共 RAG 管线。
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_owned_project
from api.knowledge.schemas import (
    KnowledgeDeletedOut,
    KnowledgeDocOut,
    KnowledgeHitOut,
    KnowledgeIngestResult,
    KnowledgeListOut,
    KnowledgeSearchIn,
    KnowledgeSearchOut,
    KnowledgeUploadOut,
)
from api.auth.security import get_current_user
from infrastructure.db import get_db
from infrastructure.models.knowledge import KnowledgeDocument
from infrastructure.models.user import User
from services.rag.ingest.pipeline import (
    count_documents,
    delete_document,
    ingest_document,
    list_documents,
)
from services.rag.pipeline import rag_pipeline

router = APIRouter(prefix="/api/projects/{project_id}/knowledge", tags=["knowledge"],
                   dependencies=[Depends(get_current_user)])


@router.post("", response_model=KnowledgeUploadOut)
async def upload_knowledge(project_id: int,
                           files: list[UploadFile] = File(...),
                           user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """上传多份文档（pdf/docx/txt/md）入库，逐个解析+分块+向量化。"""
    await get_owned_project(db, project_id, user)

    results: list[KnowledgeIngestResult] = []
    for f in files:
        data = await f.read()
        try:
            r = await ingest_document(db=db, project_id=project_id,
                                      user_id=user.id, filename=f.filename or "unnamed",
                                      data=data)
            results.append(KnowledgeIngestResult(**r, filename=f.filename or "unnamed"))
        except Exception as e:
            results.append(KnowledgeIngestResult(
                status="failed", filename=f.filename or "unnamed", error=str(e)[:200]))
    ready = sum(1 for r in results if r.status == "ready")
    return {"project_id": project_id, "uploaded": len(files), "ready": ready,
            "results": results}


@router.get("", response_model=KnowledgeListOut)
async def list_knowledge(project_id: int,
                         user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    """项目知识库文档列表（文件级元数据）。"""
    await get_owned_project(db, project_id, user)
    docs = await list_documents(db, project_id)
    return {"project_id": project_id, "count": len(docs), "documents": docs}


@router.delete("/{doc_id}", response_model=KnowledgeDeletedOut)
async def delete_knowledge(project_id: int, doc_id: int,
                           user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """删除知识库文档（向量分块 + 元数据 + 原始文件一并清理）。"""
    await get_owned_project(db, project_id, user)
    doc = await db.get(KnowledgeDocument, doc_id)
    if doc is None or doc.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "知识库文档不存在")

    await delete_document(db, doc)
    return KnowledgeDeletedOut(deleted=doc_id)


@router.post("/search", response_model=KnowledgeSearchOut)
async def search_knowledge(project_id: int, body: KnowledgeSearchIn,
                           user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """库内检索：mode=project 仅项目知识库；mode=hybrid 公共语料+项目知识库融合。"""
    await get_owned_project(db, project_id, user)
    # 校验项目知识库非空，空库直接返回空结果避免无意义检索
    if await count_documents(db, project_id) == 0:
        return {"query": body.query, "rewritten": body.query,
                "keywords": [], "results": []}

    out = await rag_pipeline.search(
        body.query, top_k=body.top_k, project_id=project_id,
        no_project_only=(body.mode == "project"))
    return KnowledgeSearchOut(
        query=body.query, rewritten=out["rewritten"],
        keywords=out.get("keywords", []),
        results=[KnowledgeHitOut(
            doc_id=(r.get("meta") or {}).get("doc_id"),
            filename=(r.get("meta") or {}).get("filename", ""),
            source=(r.get("meta") or {}).get("source", ""),
            content=r["content"],
            score=round(r.get("rerank_score", r.get("rrf_score", 0.0)), 4),
            noise_flag=r.get("noise_flag", "ok"))
            for r in out["results"]])
