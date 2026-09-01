"""路由层共享依赖：项目归属校验。"""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.models.project import Project
from infrastructure.models.user import User


async def get_owned_project(db: AsyncSession, project_id: int, user: User) -> Project:
    """校验项目存在且属于当前用户（admin 放行），否则 404。"""
    proj = await db.get(Project, project_id)
    if proj is None or (proj.user_id != user.id and user.role != "admin"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "项目不存在或无权访问")
    return proj
