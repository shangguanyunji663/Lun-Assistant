"""主控 Agent（Supervisor）：意图分类 → 专项调度 → 汇总收尾。

职责（对应简历"主控 Agent 调度 6 类专项 Agent 覆盖论文全流程"）:
- 首次进入: 调用三层意图预分类器（rule→vector→llm）识别意图，
  按意图路由至对应专项 Agent；chitchat 类直接作答，不进专项链路；
- 专项 Agent 执行完毕回到此处: 判定续链与否（max_hops 上限保护），
  无需续链则以专项产出作为最终输出收尾。
"""
import logging

from infrastructure.config import get_value
from services.agent.planner import is_complex_task
from services.agent.specialists import INTENT_TO_AGENT
from services.classifier.intent import INTENT_LABEL, intent_classifier
from services.llm.provider import LLMProvider
from services.observability.trace import span
from services.streaming.hub import current_hub

logger = logging.getLogger("lunjiang.graph")

DEFAULT_MAX_HOPS = 3


def _max_hops() -> int:
    return int(get_value("agent", "max_hops", default=DEFAULT_MAX_HOPS))


async def supervisor_node(state: dict) -> dict:
    hub = current_hub()
    visited = list(state.get("visited_agents", []))

    with span("agent.supervisor", "agent_node",
              input_data={"visited": visited, "intent": state.get("intent", "")},
              user_id=state.get("user_id")) as sp:
        await hub.emit("node_start", {"agent": "supervisor", "title": "主控Agent"},
                       node="supervisor")

        if not visited:
            # ---- 首次进入：意图预分类 + 路由 ----
            ir = await intent_classifier.classify(state.get("user_input", ""))
            sp.set_io(output={"intent": ir.intent, "confidence": ir.confidence,
                              "layer": ir.layer})
            await hub.emit("intent", {
                "intent": ir.intent, "label": INTENT_LABEL.get(ir.intent, ir.intent),
                "confidence": round(ir.confidence, 3), "layer": ir.layer,
            }, node="supervisor")

            if ir.intent == "chitchat":
                output = await _chitchat_reply(state, hub)
                await hub.emit("node_end", {"agent": "supervisor",
                                            "output_preview": output[:200]},
                               node="supervisor")
                return {"intent": ir.intent, "intent_layer": ir.layer,
                        "next_agent": "__end__", "final_output": output,
                        "stop_reason": "done"}

            if is_complex_task(state.get("user_input", ""), ir.intent):
                # 复合任务（多动作/目标词）：进入 Plan-Execute-Replan 规划器
                next_agent = "planner"
            else:
                next_agent = INTENT_TO_AGENT[ir.intent]
            await hub.emit("route", {"next": next_agent}, node="supervisor")
            await hub.emit("node_end", {"agent": "supervisor", "route": next_agent},
                           node="supervisor")
            return {"intent": ir.intent, "intent_layer": ir.layer,
                    "next_agent": next_agent}

        # ---- 专项执行完毕：收尾判定 ----
        hops = len(visited)
        stop_reason = "max_hops" if hops >= _max_hops() else "done"
        output = state.get("final_output", "")

        sp.set_io(output={"visited": visited, "stop_reason": stop_reason})
        await hub.emit("node_end", {"agent": "supervisor", "stop_reason": stop_reason},
                       node="supervisor")
        return {"next_agent": "__end__", "stop_reason": stop_reason}


async def _chitchat_reply(state: dict, hub) -> str:
    """闲聊直接作答：流式输出经 hub 下发，失败降级为非流式。"""
    history_text = state.get("history_text", "")
    system = ("你是毕业论文助手「论匠」。用户未提出论文相关请求时友好回应，"
              "简要介绍你可以帮助选题分析、文献检索、论文写作、格式校验、查重降重、AI检测。")
    messages = [{"role": "system", "content": system}]
    if history_text:
        messages.append({"role": "system", "content": f"[近期对话]\n{history_text}"})
    messages.append({"role": "user", "content": state.get("user_input", "")})

    provider = LLMProvider()
    chunks: list[str] = []
    try:
        async for delta in provider.chat_stream(messages, temperature=0.7):
            chunks.append(delta)
            await hub.emit_token(delta, node="supervisor")
    except Exception:
        logger.exception("闲聊流式回答失败，降级非流式")
        chunks = [await provider.chat(messages, max_tokens=300)]
        await hub.emit_token(chunks[0], node="supervisor")
    await hub.flush_tokens(node="supervisor")
    return "".join(chunks)
