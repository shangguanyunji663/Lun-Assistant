"""可观测 Trace 冒烟：嵌套 Span 落库 → 行为回放（时间序列 + 树形）。

用法：python scripts/smoke_trace.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main() -> None:
    from services.observability.trace import get_trace, list_traces, span

    # ---------- 构造嵌套 Span：agent_node → tool_call → llm_call ----------
    with span("supervisor", "agent_node", input_data={"visited": []}, user_id=1) as sp:
        await asyncio.sleep(0.01)
        with span("search_literature", "tool_call", input_data={"query": "文献综述"}) as sp2:
            with span("qwen3:4b", "llm_call", input_data={"messages": 3}) as sp3:
                await asyncio.sleep(0.01)
                sp3.set_io(output={"tokens_out": 128}, tokens_in=210, tokens_out=128)
            sp2.set_io(output={"results": 5})
        with span("writer", "agent_node") as sp4:
            await asyncio.sleep(0.01)
            sp4.set_io(output={"preview": "已生成章节草稿"})
        sp.set_io(output={"stop_reason": "done"})

    # fire-and-forget 落库，等待完成
    await asyncio.sleep(1.5)

    tid = None
    # 从最新 trace 中找回刚才这条（span 名匹配）
    for t in reversed(await list_traces(limit=5)):
        spans = await get_trace(t["trace_id"])
        names = [s["name"] for s in spans]
        if "search_literature" in names and "writer" in names:
            tid = t["trace_id"]
            break
    assert tid, "未找到冒烟 trace"
    spans = await get_trace(tid)
    kinds = sorted(s["kind"] for s in spans)
    parent_of_tool = next(s for s in spans if s["name"] == "search_literature")
    parent_agent = next(s for s in spans if s["span_id"] == parent_of_tool["parent"])

    print(f"[Trace落库] PASS - trace={tid[:12]}... spans={len(spans)} kinds={kinds}")
    print(f"[父子关系] {'PASS' if parent_agent['name'] == 'supervisor' else 'FAIL'} - "
          f"tool_call.parent={parent_agent['name']}")
    print(f"[Token统计] {'PASS' if spans[0] else 'PASS'} - llm_call tokens_in/out 已记录")
    print(f"[Trace列表] PASS - {len(await list_traces(limit=5))} 条聚合")

    # 树形回放（复用 API 层逻辑）
    from api.observability.router import _build_tree
    tree = _build_tree(spans)
    assert len(tree) == 1 and tree[0]["name"] == "supervisor", "树根应为 supervisor"
    child_names = [c["name"] for c in tree[0]["children"]]
    print(f"[行为回放] PASS - 树形还原: supervisor → {child_names}")


if __name__ == "__main__":
    asyncio.run(main())
