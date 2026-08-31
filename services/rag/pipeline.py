"""RAG 三阶段递进检索管线：Query改写 → 双路混合召回 → 交叉编码器精排。"""
import logging

from services.rag.query_rewrite import rewrite_query
from services.rag.reranker import reranker
from services.rag.retriever import hybrid_retriever

logger = logging.getLogger("lunjiang.rag")

_REJECT_MARKERS = ("无法", "无关", "抱歉", "不能生成", "无法生成", "不适合", "非学术")


def _is_rejection(rewritten: str) -> bool:
    """识别改写器拒答：拒绝话术或空泛过短的无效改写。"""
    if not rewritten or len(rewritten) < 8:
        return True
    return any(m in rewritten[:60] for m in _REJECT_MARKERS)


class RagPipeline:
    async def search(self, query: str, *, top_k: int | None = None,
                     use_rewrite: bool = True, use_rerank: bool = True) -> dict:
        """返回 {"rewritten", "keywords", "results": [{content, meta, scores...}]}"""
        from infrastructure.config import get_value
        top_k = top_k or int(get_value("rag", "final_top_k", default=5))
        recall_k = int(get_value("rag", "recall_top_k", default=20))

        # 阶段1: Query 改写
        rewritten, keywords = query, []
        if use_rewrite and get_value("rag", "rewrite_enabled", default=True):
            rw = await rewrite_query(query)
            rewritten, keywords = rw["rewritten"], rw["keywords"]

        # 阶段1.5: 改写失效模式兜底
        # a) 改写器拒答: LLM 判定查询超出检索域时返回拒绝文本，回退原始查询，避免污染检索
        if use_rewrite and _is_rejection(rewritten):
            rewritten = query
        # b) 语义漂移: 原始查询单独补一路稠密召回，保留原始语义锚点（A/B 实验结论落地）

        # 阶段2: 双路混合召回（RRF 融合）
        dense = await hybrid_retriever.dense_search(rewritten, top_k=recall_k)
        sparse = hybrid_retriever.sparse_search(rewritten, top_k=recall_k)
        # 关键词路: 用首个关键词再补一路 BM25，提升术语覆盖
        extra = hybrid_retriever.sparse_search(keywords[0], top_k=recall_k // 2) if keywords else []
        if use_rewrite and rewritten != query:
            dense_orig = await hybrid_retriever.dense_search(query, top_k=recall_k)
            fused = hybrid_retriever.rrf_fuse(dense, dense_orig, sparse, extra, top_k=recall_k)
        else:
            fused = hybrid_retriever.rrf_fuse(dense, sparse, extra, top_k=recall_k)

        # 阶段3: 交叉编码器精排 —— 主查询用原始 query（忠实用户意图），改写查询作为备选打分
        if use_rerank and fused:
            alt = rewritten if use_rewrite and rewritten != query else None
            results = reranker.rerank(query, fused, top_k=top_k, alt_query=alt)
        else:
            results = fused[:top_k]

        logger.info("RAG: recall(dense=%d, sparse=%d) → fused=%d → final=%d",
                    len(dense), len(sparse), len(fused), len(results))
        return {"rewritten": rewritten, "keywords": keywords, "results": results}


rag_pipeline = RagPipeline()
