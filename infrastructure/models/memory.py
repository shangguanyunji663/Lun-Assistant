"""长期记忆模型：pgvector 向量化条目（文献摘要/事实/对话摘要共用）。"""
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.config import get_embedding_dim
from infrastructure.models.base import Base


class MemoryItem(Base):
    __tablename__ = "memory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    # 类型: fact(事实) / summary(对话摘要) / document(文档块) / preference(用户偏好) / user_doc(项目知识库块)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    content: Mapped[str] = mapped_column(Text)
    # 维度跟随运行时 embedding_provider（见 infrastructure.config.get_embedding_dim），不硬编码具体底座
    embedding = mapped_column(Vector(get_embedding_dim()))
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    importance: Mapped[float] = mapped_column(default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
