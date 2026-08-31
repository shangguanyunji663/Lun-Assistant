"""工具参数 Schema 生成：从工具注册表生成 OpenAI function-calling schema。"""
from services.governance.tool_registry import tool_registry


def build_tool_schemas(names: list[str]) -> list[dict]:
    """从工具注册表生成 OpenAI tools schema（参数取 YAML 降级参数做示例）。"""
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