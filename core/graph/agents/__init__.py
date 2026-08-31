"""专项 Agent 包：规格定义 + 节点工厂。"""
from core.graph.agents.specialists import (
    AI_DETECT_AGENT,
    FORMAT_AGENT,
    LITERATURE_AGENT,
    PLAGIARISM_AGENT,
    SPECIALISTS,
    TOPIC_AGENT,
    WRITING_AGENT,
    INTENT_TO_AGENT,
    SpecialistSpec,
    build_tool_schemas,
    make_specialist_node,
)

__all__ = [
    "TOPIC_AGENT", "LITERATURE_AGENT", "WRITING_AGENT", "FORMAT_AGENT",
    "PLAGIARISM_AGENT", "AI_DETECT_AGENT", "SPECIALISTS", "INTENT_TO_AGENT",
    "SpecialistSpec", "build_tool_schemas", "make_specialist_node",
]
