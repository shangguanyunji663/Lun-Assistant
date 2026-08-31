"""论文项目管理路由（网关基座：业务 API 与 AI 运行时解耦）。"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.security import get_current_user
from infrastructure.db import get_db
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
