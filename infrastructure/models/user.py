"""用户模型（原 Java 用户管理职责的 Python 化）。"""
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.models.base import Base, IdMixin, TimestampMixin


class User(Base, IdMixin, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    # 全局角色: student / admin（细粒度工具权限由 YAML RBAC 控制）
    role: Mapped[str] = mapped_column(String(32), default="student", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
