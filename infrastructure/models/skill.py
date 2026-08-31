"""Skill 模型：BehaviorTracker 沉淀的可复用操作模式。"""
from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.models.base import Base, IdMixin, TimestampMixin


class Skill(Base, IdMixin, TimestampMixin):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(128))
    agent: Mapped[str] = mapped_column(String(64), index=True)
    # 模式签名: agent + tool + 参数形状的规范化指纹
    pattern: Mapped[dict] = mapped_column(JSON)
    # 参数模板（可带占位符）
    params_template: Mapped[dict] = mapped_column(JSON)
    description: Mapped[str] = mapped_column(Text, default="")
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    # 三维匹配用缓存分：意图相似度/参数相似度/成功率加权
    score: Mapped[float] = mapped_column(default=0.0)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
