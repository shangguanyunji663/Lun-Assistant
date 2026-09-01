"""项目级私有知识库：文件级元数据模型。

设计（方案A落地）：
- 本表只存"一份上传文件"的元数据（文件名/格式/大小/MD5/状态）；
- 解析出的向量分块不入本表，而是复用 MemoryItem(kind="user_doc")
  + project_id/user_id，直接纳入现有 RAG 稠密/稀疏/精排链路。
- 该设计避免知识库与语料双轨并行两套向量检索代码。
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.models.base import Base, IdMixin, TimestampMixin


class KnowledgeDocument(Base, IdMixin, TimestampMixin):
    __tablename__ = "knowledge_documents"

    # 归属：知识库以项目为作用域，同时记录上传人便于审计
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # 文件基本信息
    filename: Mapped[str] = mapped_column(String(256))              # 原始文件名
    file_type: Mapped[str] = mapped_column(String(16))              # pdf / docx / txt / md
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)  # MD5，同项目内去重

    # 解析结果统计
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)    # 向量分块数
    word_count: Mapped[int] = mapped_column(Integer, default=0)     # 提取文本字数

    # 生命周期: parsing -> ready | failed
    status: Mapped[str] = mapped_column(String(16), default="parsing", index=True)
    error: Mapped[str] = mapped_column(Text, default="")            # 失败原因（如扫描件无文本）