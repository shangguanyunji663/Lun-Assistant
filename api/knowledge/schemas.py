"""项目级私有知识库 API 契约（Pydantic response_model）。"""
from pydantic import BaseModel, Field


class KnowledgeSearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    # mode: hybrid 公共语料+项目知识库 / project 仅项目知识库
    mode: str = Field(default="hybrid", pattern="^(hybrid|project)$")


class KnowledgeIngestResult(BaseModel):
    status: str                      # ready / skipped / failed
    filename: str = ""
    id: int | None = None
    error: str | None = None
    reason: str | None = None
    chunks: int | None = None
    word_count: int | None = None
    title: str | None = None


class KnowledgeUploadOut(BaseModel):
    project_id: int
    uploaded: int
    ready: int
    results: list[KnowledgeIngestResult]


class KnowledgeDocOut(BaseModel):
    id: int
    filename: str
    file_type: str
    size_bytes: int
    status: str
    error: str
    chunk_count: int
    word_count: int
    created_at: str | None


class KnowledgeListOut(BaseModel):
    project_id: int
    count: int
    documents: list[KnowledgeDocOut]


class KnowledgeHitOut(BaseModel):
    doc_id: int | None
    filename: str
    source: str
    content: str
    score: float
    noise_flag: str


class KnowledgeSearchOut(BaseModel):
    query: str
    rewritten: str
    keywords: list[str]
    results: list[KnowledgeHitOut]


class KnowledgeDeletedOut(BaseModel):
    deleted: int
