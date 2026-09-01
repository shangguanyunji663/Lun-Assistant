"""论文项目 CRUD 路由（网关基座：业务 API 与 AI 运行时解耦）。

知识库管理已拆分至 api/knowledge/router.py（独立聚合根）。
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_owned_project
from api.projects.schemas import (
    ProjectCreatedOut,
    ProjectDetailOut,
    ProjectIn,
    ProjectListItem,
    ProjectPatch,
    ProjectPatchedOut,
    DeletedOut,
)
from api.auth.security import get_current_user
from infrastructure.db import get_db
from infrastructure.models.project import Project
from infrastructure.models.user import User

router = APIRouter(prefix="/api/projects", tags=["projects"],
                   dependencies=[Depends(get_current_user)])


@router.post("", response_model=ProjectCreatedOut)
async def create_project(body: ProjectIn, user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    proj = Project(user_id=user.id, title=body.title, major=body.major,
                   requirement=body.requirement)
    db.add(proj)
    await db.commit()
    return {"id": proj.id, "title": proj.title, "status": proj.status}


@router.get("", response_model=list[ProjectListItem])
async def list_projects(user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(Project).where(Project.user_id == user.id).order_by(Project.id.desc())
    )).scalars().all()
    return [{"id": p.id, "title": p.title, "major": p.major, "status": p.status,
             "created_at": p.created_at.isoformat()} for p in rows]


@router.get("/{project_id}", response_model=ProjectDetailOut)
async def get_project(project_id: int, user: User = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    proj = await get_owned_project(db, project_id, user)
    return {"id": proj.id, "title": proj.title, "major": proj.major, "status": proj.status,
            "requirement": proj.requirement, "structured_memory": proj.structured_memory}


@router.patch("/{project_id}", response_model=ProjectPatchedOut)
async def patch_project(project_id: int, body: ProjectPatch,
                        user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    proj = await get_owned_project(db, project_id, user)
    for field in ("title", "major", "requirement", "status"):
        val = getattr(body, field)
        if val is not None:
            setattr(proj, field, val)
    await db.commit()
    return {"id": proj.id, "status": proj.status}


@router.delete("/{project_id}", response_model=DeletedOut)
async def delete_project(project_id: int, user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    proj = await get_owned_project(db, project_id, user)
    await db.delete(proj)
    await db.commit()
    return {"deleted": project_id}
