"""6 类专项 Agent 定义与节点工厂。

每个专项 Agent = 系统提示词 + 工具子集 + Function-Calling 循环
（工具执行统一经 ToolRegistry 治理栈: RBAC→限流→熔断→容错→审计→行为观测）。
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from langgraph.types import interrupt

from observability.trace import span

logger = logging.getLogger("lunjiang.graph")


@dataclass
class SpecialistSpec:
    name: str                 # 节点名, 如 "topic_agent"
    intent: str               # 负责的意图
    title: str                # 中文名
    system: str
    tools: list[str] = field(default_factory=list)     # 允许的工具名
    needs_confirmation: bool = False                   # 产出后是否人机确认


TOPIC_AGENT = SpecialistSpec(
    name="topic_agent", intent="topic_analysis", title="选题分析Agent",
    system="你是毕业论文选题分析专家。结合用户专业、兴趣与要求，产出可执行的选题建议。"
           "先调用 topic_analysis 工具生成候选，可用 search_literature 检验方向热度。",
    tools=["topic_analysis", "search_literature"],
    needs_confirmation=True,
)

LITERATURE_AGENT = SpecialistSpec(
    name="literature_agent", intent="literature_search", title="文献检索Agent",
    system="你是学术文献检索专家。对用户的研究主题执行递进式检索并归纳综述。"
           "先调用 rewrite_query 优化查询，再调用 search_literature 获取文献，"
           "输出按主题聚类的文献综述（含出处）。",
    tools=["rewrite_query", "search_literature"],
)

WRITING_AGENT = SpecialistSpec(
    name="writing_agent", intent="writing", title="论文写作Agent",
    system="你是学术论文写作专家。根据用户要求撰写/润色指定章节，"
           "可先用 search_literature 检索支撑材料，再调用 generate_section 产出正文。"
           "遵循学术语言规范，引用检索到的文献。",
    tools=["search_literature", "generate_section"],
)

FORMAT_AGENT = SpecialistSpec(
    name="format_agent", intent="format_check", title="格式校验Agent",
    system="你是论文格式审查专家。调用 check_format 对文本做规则+语义双通道校验，"
           "汇总问题清单并给出修复建议。",
    tools=["check_format"],
)

PLAGIARISM_AGENT = SpecialistSpec(
    name="plagiarism_agent", intent="plagiarism_reduce", title="查重降重Agent",
    system="你是查重与降重专家。先调用 check_plagiarism 定位高重复片段，"
           "对高重复部分给出同义改写版本，保持学术含义不变。",
    tools=["check_plagiarism"],
)

AI_DETECT_AGENT = SpecialistSpec(
    name="ai_detect_agent", intent="ai_detect", title="AI检测Agent",
    system="你是AI文本痕迹检测专家。调用 detect_ai_text 检测AI痕迹，"
           "输出AI概率、判定信号与降低AI味的具体改写建议。",
    tools=["detect_ai_text"],
)

SPECIALISTS: dict[str, SpecialistSpec] = {
    s.name: s for s in (TOPIC_AGENT, LITERATURE_AGENT, WRITING_AGENT,
                        FORMAT_AGENT, PLAGIARISM_AGENT, AI_DETECT_AGENT)
}

INTENT_TO_AGENT = {s.intent: s.name for s in SPECIALISTS.values()}


def build_tool_schemas(names: list[str]) -> list[dict]:
    """从工具注册表生成 OpenAI tools schema（参数取 YAML 降级参数做示例）。"""
    from governance.tool_registry import tool_registry
    schemas = []
    for name in names:
        spec = tool_registry.get(name)
        schemas.append({
            "type": "function",
            "function": {
                "name": name,
                "description": spec.description,
                "parameters": {
                    "type": "object",
                    "properties": _param_hints(name),
                    "required": _required_hints(name),
                },
            },
        })
    return schemas


_PARAM_HINTS: dict[str, dict] = {
    "search_literature": {"query": {"type": "string", "description": "检索查询"},
                          "top_k": {"type": "integer", "description": "返回条数, 默认5"}},
    "rewrite_query": {"query": {"type": "string"}},
    "topic_analysis": {"major": {"type": "string"}, "interest": {"type": "string"},
                       "requirement": {"type": "string"}},
    "generate_section": {"section": {"type": "string", "description": "章节名或写作指令"},
                         "outline": {"type": "string"}, "references": {"type": "string"}},
    "check_format": {"text": {"type": "string"}},
    "check_plagiarism": {"text": {"type": "string"}},
    "detect_ai_text": {"text": {"type": "string"}},
}

_REQUIRED_HINTS: dict[str, list[str]] = {
    "search_literature": ["query"], "rewrite_query": ["query"],
    "topic_analysis": ["major", "interest"], "generate_section": ["section"],
    "check_format": ["text"], "check_plagiarism": ["text"], "detect_ai_text": ["text"],
}


def _param_hints(name: str) -> dict:
    return _PARAM_HINTS.get(name, {})


def _required_hints(name: str) -> list[str]:
    return _REQUIRED_HINTS.get(name, [])


def make_specialist_node(spec: SpecialistSpec) -> Callable:
    """生成 LangGraph 节点函数。"""

    async def node(state: dict) -> dict:
        from core.streaming.hub import current_hub
        from governance.tool_registry import tool_registry

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

            provider = _provider()
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


def _provider():
    from core.llm.provider import LLMProvider
    return LLMProvider()
