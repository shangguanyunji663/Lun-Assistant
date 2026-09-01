"""论文项目模型：一个用户毕业论文 = 一个项目（记忆体系/RAG 均以项目为作用域）。"""
from sqlalchemy import ForeignKey, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.models.base import Base, IdMixin, TimestampMixin

# 项目生命周期（单一真源：API 校验与前端 STATUS_LABEL 均以此为准）
# created(立项) -> topic(选题) -> literature(文献) -> writing(写作) -> review(校验) -> finalize(定稿)
PROJECT_STATUSES = ("created", "topic", "literature", "writing", "review", "finalize")


class Project(Base, IdMixin, TimestampMixin):
    __tablename__ = "projects"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(256), default="未命名论文")
    major: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(32), default="created", index=True)
    # 项目结构化记忆：大纲/选题结论/研究问题等
    structured_memory: Mapped[dict | None] = mapped_column(JSON, default=None)
    requirement: Mapped[str] = mapped_column(Text, default="")
