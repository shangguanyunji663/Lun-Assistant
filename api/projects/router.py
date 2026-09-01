"""论文项目管理路由（网关基座：业务 API 与 AI 运行时解耦）+ 项目级私有知识库管理。"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.security import get_current_user
from infrastructure.db import get_db
from infrastructure.models.knowledge import KnowledgeDocument
from infrastructure.models.project import Project
from infrastructure.models.user import User

router = APIRouter(prefix="/api/projects", tags=["projects"], dependencies=[Depends(get_current_user)])


class ProjectIn(BaseModel):
    title: str = Field(default="未命名论文", max_length=256)
    major: str = Field(default="", max_length=64)
    requirement: str = ""


class ProjectPatch(BaseModel):
    title: str | None = None
    major: str | None = None
    requirement: str | None = None
    status: str | None = None


class KnowledgeSearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    # mode: hybrid 公共语料+项目知识库 / project 仅项目知识库
    mode: str = Field(default="hybrid", pattern="^(hybrid|project)$")


async def _get_owned(db: AsyncSession, project_id: int, user: User) -> Project:
    proj = await db.get(Project, project_id)
    if proj is None or (proj.user_id != user.id and user.role != "admin"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "项目不存在或无权访问")
    return proj


@router.post("")
async def create_project(body: ProjectIn, user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    proj = Project(user_id=user.id, title=body.title, major=body.major,
                   requirement=body.requirement)
    db.add(proj)
    await db.commit()
    return {"id": proj.id, "title": proj.title, "status": proj.status}


@router.get("")
async def list_projects(user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(Project).where(Project.user_id == user.id).order_by(Project.id.desc())
    )).scalars().all()
    return [{"id": p.id, "title": p.title, "major": p.major, "status": p.status,
             "created_at": p.created_at.isoformat()} for p in rows]


@router.get("/{project_id}")
async def get_project(project_id: int, user: User = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    proj = await _get_owned(db, project_id, user)
    return {"id": proj.id, "title": proj.title, "major": proj.major, "status": proj.status,
            "requirement": proj.requirement, "structured_memory": proj.structured_memory}


@router.patch("/{project_id}")
async def patch_project(project_id: int, body: ProjectPatch,
                        user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    proj = await _get_owned(db, project_id, user)
    for field in ("title", "major", "requirement", "status"):
        val = getattr(body, field)
        if val is not None:
            setattr(proj, field, val)
    await db.commit()
    return {"id": proj.id, "status": proj.status}


@router.delete("/{project_id}")
async def delete_project(project_id: int, user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    proj = await _get_owned(db, project_id, user)
    await db.delete(proj)
    await db.commit()
    return {"deleted": project_id}


# ============================================================
# 项目级私有知识库（企业 RAG 核心：上传→解析→分块→入库）
# ============================================================

@router.post("/{project_id}/knowledge")
async def upload_knowledge(project_id: int,
                           files: list[UploadFile] = File(...),
                           user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """上传多份文档（pdf/docx/txt/md）入库，逐个解析+分块+向量化。"""
    await _get_owned(db, project_id, user)
    from services.rag.ingest.pipeline import ingest_document

    results = []
    for f in files:
        data = await f.read()
        try:
            r = await ingest_document(db=db, project_id=project_id,
                                      user_id=user.id, filename=f.filename or "unnamed",
                                      data=data)
            results.append(r)
        except Exception as e:
            results.append({"status": "failed", "filename": f.filename, "error": str(e)[:200]})
    ready = sum(1 for r in results if r.get("status") == "ready")
    return {"project_id": project_id, "uploaded": len(files), "ready": ready,
            "results": results}


@router.get("/{project_id}/knowledge")
async def list_knowledge(project_id: int,
                         user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    """项目知识库文档列表（文件级元数据）。"""
    await _get_owned(db, project_id, user)
    from services.rag.ingest.pipeline import list_documents

    docs = await list_documents(db, project_id)
    return {"project_id": project_id, "count": len(docs), "documents": docs}


@router.delete("/{project_id}/knowledge/{doc_id}")
async def delete_knowledge(project_id: int, doc_id: int,
                           user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """删除知识库文档（向量分块 + 元数据 + 原始文件一并清理）。"""
    await _get_owned(db, project_id, user)
    doc = await db.get(KnowledgeDocument, doc_id)
    if doc is None or doc.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "知识库文档不存在")
    from services.rag.ingest.pipeline import delete_document

    await delete_document(db, doc)
    return {"deleted": doc_id}


@router.post("/{project_id}/knowledge/search")
async def search_knowledge(project_id: int, body: KnowledgeSearchIn,
                           user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """库内检索：mode=project 仅项目知识库；mode=hybrid 公共语料+项目知识库融合。"""
    await _get_owned(db, project_id, user)
    # 校验项目知识库非空，空库直接返回空结果避免无意义检索
    from services.rag.ingest.pipeline import count_documents

    if await count_documents(db, project_id) == 0:
        return {"query": body.query, "results": [], "note": "项目知识库为空"}

    from services.rag.pipeline import rag_pipeline

    out = await rag_pipeline.search(
        body.query, top_k=body.top_k, project_id=project_id,
        no_project_only=(body.mode == "project"))
    return {
        "query": body.query, "rewritten": out["rewritten"],
        "keywords": out.get("keywords", []),
        "results": [
            {"doc_id": (r.get("meta") or {}).get("doc_id"),
             "filename": (r.get("meta") or {}).get("filename", ""),
             "source": (r.get("meta") or {}).get("source", ""),
             "content": r["content"], "score": round(
                 r.get("rerank_score", r.get("rrf_score", 0.0)), 4),
             "noise_flag": r.get("noise_flag", "ok")}
            for r in out["results"]
        ],
    }
