"""LangGraph 主从图编译：supervisor 星型调度 6 类专项 Agent。

结构:
    START → supervisor →(条件路由)→ 专项 Agent | END
    专项 Agent → supervisor（回环，由 supervisor 决定收尾）
"""
import logging

from langgraph.graph import END, START, StateGraph

logger = logging.getLogger("lunjiang.graph")


def build_graph(checkpointer=None):
    """编译主从图。checkpointer 传入三级降级 saver 以支持断点恢复与 interrupt/resume。"""
    from services.agent.specialists import SPECIALISTS, make_specialist_node
    from services.agent.state import AgentState
    from services.agent.supervisor import supervisor_node

    builder = StateGraph(AgentState)
    builder.add_node("supervisor", supervisor_node)
    for name, spec in SPECIALISTS.items():
        builder.add_node(name, make_specialist_node(spec))

    builder.add_edge(START, "supervisor")

    def route(state: dict) -> str:
        nxt = state.get("next_agent") or "__end__"
        return nxt if nxt in SPECIALISTS or nxt == "supervisor" else END

    builder.add_conditional_edges("supervisor", route,
                                  ["supervisor", *SPECIALISTS, END])
    for name in SPECIALISTS:
        builder.add_edge(name, "supervisor")

    return builder.compile(checkpointer=checkpointer)
