"""LangGraph 主从图编译：supervisor 星型调度 6 类专项 Agent。

结构:
    START → supervisor →(条件路由)→ 专项 Agent | END
    专项 Agent → supervisor（回环，由 supervisor 决定收尾）
"""
import logging

from langgraph.graph import END, START, StateGraph

from services.agent.planner import planner_node
from services.agent.specialists import SPECIALISTS, make_specialist_node
from services.agent.state import AgentState
from services.agent.supervisor import supervisor_node

logger = logging.getLogger("lunjiang.graph")


def build_graph(checkpointer=None):
    """编译主从图。checkpointer 传入三级降级 saver 以支持断点恢复与 interrupt/resume。"""
    builder = StateGraph(AgentState)
    builder.add_node("supervisor", supervisor_node)
    for name, spec in SPECIALISTS.items():
        builder.add_node(name, make_specialist_node(spec))
    builder.add_node("planner", planner_node)

    builder.add_edge(START, "supervisor")

    def route(state: dict) -> str:
        nxt = state.get("next_agent") or "__end__"
        if nxt in SPECIALISTS or nxt in ("supervisor", "planner"):
            return nxt
        return END

    builder.add_conditional_edges("supervisor", route,
                                  ["supervisor", "planner", *SPECIALISTS, END])
    for name in SPECIALISTS:
        builder.add_edge(name, "supervisor")
    builder.add_edge("planner", "supervisor")

    return builder.compile(checkpointer=checkpointer)
