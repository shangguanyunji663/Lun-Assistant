"""专项 Agent 节点工厂：函数调用循环 + 人机确认中断 + 事件发布。

每个节点 = 系统提示词 + 工具子集 + Function-Calling 循环
（工具执行统一经 ToolRegistry 治理栈: RBAC→限流→熔断→容错→审计→行为观测）。
"""
import logging
from typing import Any, Callable

from langgraph.types import interrupt

from services.agent.specialists.schemas import build_tool_schemas
from services.agent.specialists.specs import SpecialistSpec
from services.governance.tool_registry import tool_registry
from services.llm.provider import LLMProvider
from services.observability.trace import span
from services.streaming.hub import current_hub

logger = logging.getLogger("lunjiang.graph")


def make_specialist_node(spec: SpecialistSpec) -> Callable:
    """生成 LangGraph 节点函数。"""

    async def node(state: dict) -> dict:
        hub = current_hub()
        user_input = state.get("user_input", "")
        visited = list(state.get("visited_agents", []))
        visited.append(spec.name)

        with span(f"agent.{spec.name}", "agent_node",
                  input_data={"input": user_input[:200]},
                  user_id=state.get("user_id")) as sp:
            await hub.emit("node_start", {"agent": spec.name, "title": spec.title},
                           node=spec.name)

            # ---- 组装提示 ----
            memory_brief = state.get("memory_brief", "")
            history_text = state.get("history_text", "")
            messages = [
                {"role": "system", "content": spec.system},
            ]
            if memory_brief:
                messages.append({"role": "system",
                                 "content": f"[项目结构化记忆]\n{memory_brief}"})
            if history_text:
                messages.append({"role": "system",
                                 "content": f"[近期对话]\n{history_text}"})
            messages.append({"role": "user", "content": user_input})

            # ---- 治理栈托管的工具执行器 ----
            async def executor(name: str, args: dict) -> Any:
                return await tool_registry.call(
                    name, user_id=state.get("user_id"), user_role=state.get("user_role", "student"),
                    call_context={"agent": spec.name}, **args)

            provider = LLMProvider()
            result = await provider.chat_tools(
                messages, build_tool_schemas(spec.tools), executor, max_rounds=3)

            output = result["content"]
            sp.set_io(output={"tools": [c["name"] for c in result["tool_calls"]],
                              "rounds": result["rounds"], "output": output[:400]})

            # ---- 人机介入：选题确认 ----
            if spec.needs_confirmation:
                feedback = interrupt({
                    "type": "confirm", "agent": spec.name,
                    "question": "请确认选题方案，或提出调整意见",
                    "proposal": output,
                })
                # resume 后携带用户反馈，综合产出最终结论
                if feedback:
                    final = await provider.chat([
                        {"role": "system", "content": spec.system},
                        {"role": "user", "content":
                            f"原方案:\n{output}\n\n用户反馈:\n{feedback}\n\n"
                            "请根据反馈输出最终选题结论（保留被认可部分）。"}],
                        max_tokens=1200)
                    output = final

            await hub.flush_tokens(spec.name)
            await hub.emit("node_end", {"agent": spec.name, "title": spec.title,
                                        "output_preview": output[:200]}, node=spec.name)

        results = dict(state.get("agent_results", {}))
        results[spec.name] = {"output": output,
                              "tools": [c["name"] for c in result["tool_calls"]]}
        return {"visited_agents": visited, "agent_results": results,
                "final_output": output, "next_agent": "supervisor"}

    return node
