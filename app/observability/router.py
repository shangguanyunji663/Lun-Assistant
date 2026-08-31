"""可观测路由：全链路 Trace 查询与 Agent 行为回放（admin 权限）。"""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.security import require_role
from observability.trace import get_trace, list_traces

router = APIRouter(prefix="/observability", tags=["observability"])


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


@router.get("/traces", dependencies=[Depends(require_role("admin"))])
async def traces(limit: int = Query(50, ge=1, le=200)):
    """最近 trace 列表：span 数 / 总耗时 / 总成本。"""
    return {"items": await list_traces(limit=limit)}


@router.get("/traces/{trace_id}", dependencies=[Depends(require_role("admin"))])
async def replay(trace_id: str):
    """行为回放：按时间序列 + 树形结构还原一次会话的完整执行路径。"""
    spans = await get_trace(trace_id)
    if not spans:
        raise HTTPException(404, f"trace 不存在: {trace_id}")
    total_latency = sum(s.get("latency_ms") or 0 for s in spans)
    total_cost = sum(s.get("cost_usd") or 0.0 for s in spans)
    errors = [s for s in spans if s.get("status") != "ok"]
    return {
        "trace_id": trace_id,
        "spans": spans,
        "tree": _build_tree(spans),
        "summary": {"span_count": len(spans), "total_latency_ms": total_latency,
                    "total_cost_usd": round(total_cost, 6),
                    "error_count": len(errors)},
    }
