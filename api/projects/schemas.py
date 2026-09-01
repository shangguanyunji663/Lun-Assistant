"""论文项目 API 契约（Pydantic response_model）。

StatusLiteral 与 infrastructure/models/project.py 的 PROJECT_STATUSES 保持一致，
由 tests/test_project_status.py 断言两者同步。
"""
from typing import Literal

from pydantic import BaseModel, Field

# 与后端模型 PROJECT_STATUSES 单一真源对齐（测试强制同步）
StatusLiteral = Literal["created", "topic", "literature", "writing", "review", "finalize"]


class ProjectIn(BaseModel):
    title: str = Field(default="未命名论文", max_length=256)
    major: str = Field(default="", max_length=64)
    requirement: str = ""


class ProjectPatch(BaseModel):
    title: str | None = Field(default=None, max_length=256)
    major: str | None = Field(default=None, max_length=64)
    requirement: str | None = None
    status: StatusLiteral | None = None


class ProjectCreatedOut(BaseModel):
    id: int
    title: str
    status: str


class ProjectListItem(BaseModel):
    id: int
    title: str
    major: str
    status: str
    created_at: str


class ProjectDetailOut(BaseModel):
    id: int
    title: str
    major: str
    status: str
    requirement: str
    structured_memory: dict | None


class ProjectPatchedOut(BaseModel):
    id: int
    status: str


class DeletedOut(BaseModel):
    deleted: int
