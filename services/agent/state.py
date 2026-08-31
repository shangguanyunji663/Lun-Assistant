"""LangGraph 全局状态定义（TypedDict，全链路共享）。"""
from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    # ---- 会话身份 ----
    project_id: int
    session_id: str
    user_id: int
    user_role: str

    # ---- 对话与意图 ----
    messages: Annotated[list, add_messages]     # LangGraph 标准消息流
    user_input: str
    intent: str                                  # 6类意图 + chitchat
    intent_layer: str                            # rule / vector / llm

    # ---- 调度 ----
    next_agent: str                              # supervisor 决策
    visited_agents: list[str]                    # 本轮已执行的专项Agent
    agent_results: dict[str, Any]                # 各专项Agent产出

    # ---- 记忆装配（引擎注入，降级为空） ----
    memory_brief: str                            # 项目结构化记忆摘要
    history_text: str                            # 近期对话文本

    # ---- 人机介入 ----
    interrupt_reason: str
    human_feedback: str

    # ---- 产出 ----
    final_output: str
    stop_reason: str                             # max_hops / done / error
