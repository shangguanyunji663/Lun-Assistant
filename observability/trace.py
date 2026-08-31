"""全链路 Trace：Agent 节点 / LLM 调用 / 工具调用 / 检索 统一 Span 记录。

- contextvars 传递 trace_id 与 parent_span_id，异步任务链路自动透传。
- Span 结束后异步落库（fire-and-forget），不阻塞主流程。
- 行为回放 = 按 trace_id 拉取全部 Span 按时间还原执行序列。
"""
import logging
import time
import uuid
from contextvars import ContextVar
from contextlib import contextmanager
from typing import Any

from sqlalchemy import select

from app.config import get_value
from app.db import get_session_factory
from app.models.trace import TraceSpan

logger = logging.getLogger("lunjiang.trace")

_current_trace: ContextVar[str | None] = ContextVar("trace_id", default=None)
_current_span: ContextVar[str | None] = ContextVar("span_id", default=None)


def current_trace_id() -> str | None:
    return _current_trace.get()


def _trace_enabled() -> bool:
    return bool(get_value("observability", "trace_enabled", default=True))


@contextmanager
def span(name: str, kind: str, input_data: dict | None = None, user_id: int | None = None):
    """同步风格上下文管理器（内部记录为异步落库任务）。"""
    if not _trace_enabled():
        yield _NoopSpan()
        return

    trace_id = _current_trace.get() or uuid.uuid4().hex
    parent = _current_span.get()
    span_id = uuid.uuid4().hex
    started = time.perf_counter()
    token_t = _current_trace.set(trace_id)
    token_s = _current_span.set(span_id)
    _sp = _SpanCtx(trace_id, span_id, parent, kind, name, input_data, user_id, started)
    try:
        yield _sp
        _sp.status = "ok"
    except Exception as e:
        _sp.status = "error"
        _sp.error = f"{type(e).__name__}: {e}"
        raise
    finally:
        _sp.latency_ms = int((time.perf_counter() - started) * 1000)
        _current_trace.reset(token_t)
        _current_span.reset(token_s)
        _persist(_sp)


class _NoopSpan:
    def set_io(self, **_):
        pass

    output = None
    tokens_in = 0
    tokens_out = 0


class _SpanCtx:
    def __init__(self, trace_id, span_id, parent, kind, name, input_data, user_id, started):
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent = parent
        self.kind = kind
        self.name = name
        self.input = input_data
        self.user_id = user_id
        self.status = "ok"
        self.output: Any = None
        self.error: str | None = None
        self.tokens_in = 0
        self.tokens_out = 0
        self.cost_usd = 0.0
        self.latency_ms = 0
        self._started = started

    def set_io(self, *, output=None, tokens_in=None, tokens_out=None, cost_usd=None):
        if output is not None:
            self.output = output
        if tokens_in is not None:
            self.tokens_in = tokens_in
        if tokens_out is not None:
            self.tokens_out = tokens_out
        if cost_usd is not None:
            self.cost_usd = cost_usd


def _persist(sp: _SpanCtx) -> None:
    async def _write():
        try:
            async with get_session_factory()() as db:
                db.add(TraceSpan(
                    trace_id=sp.trace_id, span_id=sp.span_id, parent_span_id=sp.parent,
                    kind=sp.kind, name=sp.name, status=sp.status,
                    input=_safe(sp.input), output=_safe(sp.output), error=sp.error,
                    tokens_in=sp.tokens_in, tokens_out=sp.tokens_out, cost_usd=sp.cost_usd,
                    latency_ms=sp.latency_ms, user_id=sp.user_id,
                ))
                await db.commit()
        except Exception:
            logger.exception("Trace 落库失败 span=%s", sp.name)

    import asyncio
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_write())
    except RuntimeError:
        pass  # 无事件循环时（脚本场景）跳过异步落库


def _safe(v: Any) -> dict | None:
    if v is None:
        return None
    try:
        import json
        return json.loads(json.dumps(v, ensure_ascii=False, default=str))
    except Exception:
        return {"repr": repr(v)}


# ---------------- 查询 / 回放 ----------------

async def get_trace(trace_id: str) -> list[dict]:
    """按 trace_id 还原执行序列（行为回放数据源）。"""
    async with get_session_factory()() as db:
        rows = (await db.execute(
            select(TraceSpan).where(TraceSpan.trace_id == trace_id).order_by(TraceSpan.id)
        )).scalars().all()
    return [
        {
            "span_id": r.span_id, "parent": r.parent_span_id, "kind": r.kind, "name": r.name,
            "status": r.status, "input": r.input, "output": r.output, "error": r.error,
            "tokens_in": r.tokens_in, "tokens_out": r.tokens_out, "cost_usd": r.cost_usd,
            "latency_ms": r.latency_ms, "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


async def list_traces(limit: int = 50) -> list[dict]:
    from sqlalchemy import func as f
    async with get_session_factory()() as db:
        rows = (await db.execute(
            select(TraceSpan.trace_id, f.count().label("spans"),
                   f.sum(TraceSpan.latency_ms).label("latency"),
                   f.sum(TraceSpan.cost_usd).label("cost"))
            .group_by(TraceSpan.trace_id).order_by(f.max(TraceSpan.id).desc()).limit(limit)
        )).all()
    return [
        {"trace_id": r.trace_id, "spans": r.spans, "total_latency_ms": int(r.latency or 0),
         "total_cost_usd": float(r.cost or 0.0)}
        for r in rows
    ]
