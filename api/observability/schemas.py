"""可观测 API 契约（Trace 列表与行为回放的 response_model）。

span 的字段与 services/observability/trace.py::get_trace 的返回保持一致；
tree 为同一批 span 按 parent 关系还原的嵌套结构（节点为 span + children）。
"""
from typing import Any

from pydantic import BaseModel


class TraceSpanOut(BaseModel):
    span_id: str
    parent: str | None = None
    kind: str
    name: str
    status: str
    input: dict | None = None
    output: dict | None = None
    error: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    created_at: str | None = None


class TraceListItem(BaseModel):
    trace_id: str
    spans: int
    total_latency_ms: int
    total_cost_usd: float


class TraceListOut(BaseModel):
    items: list[TraceListItem]


class TraceSummary(BaseModel):
    span_count: int
    total_latency_ms: int
    total_cost_usd: float
    error_count: int


class TraceReplayOut(BaseModel):
    trace_id: str
    spans: list[TraceSpanOut]
    # 递归结构：每个节点为 span 字段 + children 同名节点列表
    tree: list[dict[str, Any]]
    summary: TraceSummary
