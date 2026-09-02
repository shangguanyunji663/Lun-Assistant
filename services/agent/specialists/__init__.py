"""专项 Agent 包：规格 + Schema + 节点工厂，对外统一聚合导出。"""
from services.agent.specialists.node_factory import make_specialist_node
from services.agent.specialists.schemas import build_tool_schemas
from services.agent.specialists.specs import (
    AI_DETECT_AGENT,
    FORMAT_AGENT,
    INTENT_TO_AGENT,
    LITERATURE_AGENT,
    PLAGIARISM_AGENT,
    SPECIALISTS,
    TOPIC_AGENT,
    WRITING_AGENT,
    SpecialistSpec,
)

__all__ = [
    "AI_DETECT_AGENT",
    "FORMAT_AGENT",
    "INTENT_TO_AGENT",
    "LITERATURE_AGENT",
    "PLAGIARISM_AGENT",
    "SPECIALISTS",
    "TOPIC_AGENT",
    "WRITING_AGENT",
    "SpecialistSpec",
    "build_tool_schemas",
    "make_specialist_node",
]