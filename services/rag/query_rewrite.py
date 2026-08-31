"""RAG 阶段一：Query 改写（扩写检索意图 + 提取关键词，提升召回覆盖）。"""
import json
import logging

from services.llm.provider import LLMProvider

logger = logging.getLogger("lunjiang.rag")

_SYSTEM = (
    "你是学术检索查询改写器。将用户的论文相关请求改写为适合学术文献检索的查询。"
    "输出JSON: {\"rewritten\": \"改写后的完整查询(中英混合均可, 补全学科术语)\", "
    "\"keywords\": [\"3-6个检索关键词\"]}"
)


async def rewrite_query(query: str, provider: LLMProvider | None = None) -> dict:
    provider = provider or LLMProvider()
    try:
        data = await provider.chat(
            [{"role": "system", "content": _SYSTEM},
             {"role": "user", "content": query}],
            json_mode=True, temperature=0.1, max_tokens=200,
        )
        return {"rewritten": data.get("rewritten") or query,
                "keywords": data.get("keywords") or []}
    except Exception:
        logger.warning("Query改写失败，使用原始查询")
        return {"rewritten": query, "keywords": []}
