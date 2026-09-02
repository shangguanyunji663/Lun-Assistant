"""可观测路由：全链路 Trace 查询与 Agent 行为回放（admin 权限）。"""
import time
from typing import Any

import psutil
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from api.auth.security import require_role
from api.observability.schemas import (
    TraceListItem,
    TraceListOut,
    TraceReplayOut,
    TraceSpanOut,
    TraceSummary,
)
from infrastructure.db import get_session_factory
from infrastructure.models.audit import AuditLog
from infrastructure.models.knowledge import KnowledgeDocument
from infrastructure.models.project import Project
from infrastructure.models.trace import TraceSpan
from infrastructure.models.user import User
from services.observability.trace import get_trace, list_traces

router = APIRouter(prefix="/api/observability", tags=["observability"])

# 进程启动时刻（monotonic 基准），用于计算运行时长
_PROCESS_START = time.monotonic()

# 指标端点统计的表：模型 → 指标键名
_METRIC_TABLES: list[tuple[Any, str]] = [
    (User, "users"),
    (Project, "projects"),
    (TraceSpan, "trace_spans"),
    (AuditLog, "audit_logs"),
    (KnowledgeDocument, "knowledge_documents"),
]


def _build_tree(spans: list[dict]) -> list[dict]:
    """扁平 span 列表 → 树形结构（行为回放视图）。"""
    by_id = {s["span_id"]: {**s, "children": []} for s in spans}
    roots: list[dict] = []
    for s in spans:
        node = by_id[s["span_id"]]
        parent = by_id.get(s.get("parent"))
        if parent is not None and parent is not node:
            parent["children"].append(node)
        else:
            roots.append(node)
    return roots


@router.get("/traces", response_model=TraceListOut,
            dependencies=[Depends(require_role("admin"))])
async def traces(limit: int = Query(50, ge=1, le=200)):
    """最近 trace 列表：span 数 / 总耗时 / 总成本。"""
    items = [TraceListItem(**row) for row in await list_traces(limit=limit)]
    return TraceListOut(items=items)


@router.get("/traces/{trace_id}", response_model=TraceReplayOut,
            dependencies=[Depends(require_role("admin"))])
async def replay(trace_id: str):
    """行为回放：按时间序列 + 树形结构还原一次会话的完整执行路径。"""
    spans = await get_trace(trace_id)
    if not spans:
        raise HTTPException(404, f"trace 不存在: {trace_id}")
    total_latency = sum(s.get("latency_ms") or 0 for s in spans)
    total_cost = sum(s.get("cost_usd") or 0.0 for s in spans)
    errors = [s for s in spans if s.get("status") != "ok"]
    return TraceReplayOut(
        trace_id=trace_id,
        spans=[TraceSpanOut(**s) for s in spans],
        tree=_build_tree(spans),
        summary=TraceSummary(
            span_count=len(spans),
            total_latency_ms=total_latency,
            total_cost_usd=round(total_cost, 6),
            error_count=len(errors),
        ),
    )


async def _table_count(model: Any) -> int | None:
    """表行数计数；数据库不可用时返回 None（进程指标仍可用）。"""
    try:
        async with get_session_factory()() as db:
            return (await db.scalar(select(func.count()).select_from(model))) or 0
    except Exception:
        return None


@router.get("/metrics", dependencies=[Depends(require_role("admin"))])
async def metrics() -> dict[str, Any]:
    """轻量运行指标：进程运行时长 / 内存 + 各核心表行数（DB 容错）。"""
    process = psutil.Process()
    counts: dict[str, int | None] = {}
    for model, key in _METRIC_TABLES:
        counts[key] = await _table_count(model)
    return {
        "uptime_s": round(time.monotonic() - _PROCESS_START, 1),
        "process_rss_mb": round(process.memory_info().rss / (1024 * 1024), 1),
        "counts": counts,
    }
