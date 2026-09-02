"""RAG 递进检索管线：Query改写 → 多路混合召回（稠密+稀疏+相邻窗口）→ 交叉编码器精排（含降噪对比）。

阶段拆解（企业级升级后）：
  S1  Query改写（LLM + 规则字典兜底，拒答/漂移回退原始查询）
  S2  多路召回并 RRF 融合：
      - 稠密路（公共语料 dense）
      - 稀疏路（BM25 公共语料）
      - 关键词路（改写关键词补一路 BM25，术语覆盖）
      - 原始语料路（改写生效时保留原查询稠密锚点，防语义漂移）
      - 项目知识库路（project_id 作用域下 user_doc 稠密检索，跨项目隔离）
      - 相邻窗口路（第三引擎：命中块前后邻块补全上下文，window 半径可配）
  S3  交叉编码器精排 + 降噪对比：
      - 主查询原文 + 改写查询双打分取 max
      - 仅被稀疏路命中的候选（dense 未命中）打软性噪声惩罚，抑制关键词重叠噪声
"""
import logging

from infrastructure.config import get_value
from services.rag.query_rewrite import rewrite_query
from services.rag.reranker import reranker
from services.rag.retriever import hybrid_retriever

logger = logging.getLogger("lunjiang.rag")

_REJECT_MARKERS = ("无法", "无关", "抱歉", "不能生成", "无法生成", "不适合", "非学术")
# 仅稀疏路命中（稠密路未命中）的候选：关键词重叠噪声软惩罚系数
_SPARSE_ONLY_PENALTY = 0.982
# 仅维度对比生效的窗口：稠密路 top 排名内视为"语义可信"
_DENSE_TRUST_RANK = 0.35


def _is_rejection(rewritten: str) -> bool:
    """识别改写器拒答：拒绝话术或空泛过短的无效改写。"""
    if not rewritten or len(rewritten) < 8:
        return True
    return any(m in rewritten[:60] for m in _REJECT_MARKERS)


def _noise_penalty(fused: list[dict], dense_ids: set[int], sparse_ids: set[int],
                   dense_rank: dict[int, int]) -> None:
    """精排降噪对比：为每个候选打标降噪因子。

    - 稠密语义路命中（dense 排名靠前）→ 语义可信，不惩罚；
    - 仅稀疏路命中 → 高概率关键词重叠噪声，软惩罚；
    - 稠密路命中但排名靠后（> trust_rank 阈值）→ 弱惩罚，避免完全压低合法术语命中。
    """
    for item in fused:
        rank = dense_rank.get(item["id"])
        if rank is None:
            # 稠密未命中：稀疏独有
            item["rerank_boost"] = _SPARSE_ONLY_PENALTY
            item["noise_flag"] = "sparse_only"
        elif rank > max(1, int(len(dense_rank) * _DENSE_TRUST_RANK)):
            item["rerank_boost"] = 0.995
            item["noise_flag"] = "weak"
        else:
            item["rerank_boost"] = 1.0
            item["noise_flag"] = "ok"
        item["in_dense"] = item["id"] in dense_ids
        item["in_sparse"] = item["id"] in sparse_ids


class RagPipeline:
    async def search(self, query: str, *, top_k: int | None = None,
                     use_rewrite: bool = True, use_rerank: bool = True,
                     project_id: int | None = None,
                     no_project_only: bool = False,
                     rewrite_mode: str | None = None) -> dict:
        """统一检索入口。

        - project_id: 传入后额外纳入该项目私有知识库（user_doc）检索；None 时仅公共语料。
        - no_project_only: 仅检索项目知识库（知识库管理页"库内检索"用），跳过公共语料。
        - rewrite_mode: "on/auto/off" 透传 Query 改写模式；None 时 use_rewrite=True 走
          配置 rag.rewrite_mode（默认 auto），use_rewrite=False 等效 off。
          评测脚本（ab.py/harness.py）显式传 on/off 保持 AB 组别口径不被 auto 污染。
        返回 {"rewritten", "keywords", "results": [{content, meta, scores...}]}
        """
        top_k = top_k or int(get_value("rag", "final_top_k", default=5))
        recall_k = int(get_value("rag", "recall_top_k", default=20))
        window = int(get_value("rag", "sibling_window", default=1))

        # S1: Query 改写（LLM + 规则兜底；拒答回退；auto 难度自适应）
        rewritten, keywords = query, []
        if use_rewrite and get_value("rag", "rewrite_enabled", default=True):
            rw = await rewrite_query(query, mode=rewrite_mode)
            rewritten, keywords = rw["rewritten"], rw["keywords"]
            if _is_rejection(rewritten):
                rewritten = query

        # S2: 多路召回
        roads: list[list[dict]] = []
        if not no_project_only:
            dense = await hybrid_retriever.dense_search(rewritten, top_k=recall_k)
            sparse = await hybrid_retriever.sparse_search(rewritten, top_k=recall_k)
            roads += [dense, sparse]
            if keywords:
                roads.append(await hybrid_retriever.sparse_search(
                    keywords[0], top_k=recall_k // 2))
            if use_rewrite and rewritten != query:
                roads.append(await hybrid_retriever.dense_search(query, top_k=recall_k))
        else:
            dense, sparse = [], []

        project_road: list[dict] = []
        if project_id is not None:
            project_road = await hybrid_retriever.project_dense_search(
                query, project_id, top_k=recall_k)
            if project_road:
                roads.append(project_road)

        fused = hybrid_retriever.rrf_fuse(*roads, top_k=recall_k) if roads else []

        # 第三引擎：相邻窗口路（对主路融合结果做上下文补全）
        if window > 0 and fused:
            siblings = await hybrid_retriever.sibling_search(fused, window=window,
                                                             top_k=recall_k)
            if siblings:
                fused = hybrid_retriever.rrf_fuse(fused, siblings, top_k=recall_k)

        # 项目知识库保底：RRF 二次融合的 top_k 截断可能压制"仅项目路命中"的强相关块，
        # 将项目路 Top-2 补入候选（标记 rrf 略高于融合下限），最终排序仍由精排裁决。
        if project_road:
            keep = {x["id"] for x in fused}
            floor = min((x.get("rrf_score", 0.0) for x in fused), default=0.0)
            for pr in project_road[:2]:
                if pr["id"] not in keep:
                    fused.append({**pr, "rrf_score": floor + 0.0001})
                    keep.add(pr["id"])
            fused.sort(key=lambda x: x.get("rrf_score", 0.0), reverse=True)
            fused = fused[:recall_k]

        # S3: 精排 + 降噪对比
        if use_rerank and fused:
            dense_ids = {r["id"] for r in dense + project_road}
            sparse_ids = {r["id"] for r in sparse}
            dense_rank = {r["id"]: i for i, r in enumerate(dense + project_road, 1)}
            _noise_penalty(fused, dense_ids, sparse_ids, dense_rank)

            alt = rewritten if use_rewrite and rewritten != query else None
            results = await reranker.rerank(query, fused, top_k=top_k, alt_query=alt)
            for r in results:  # 应用降噪因子后重新排序
                r["rerank_score"] = r.get("rerank_score", 0.0) * r.get("rerank_boost", 1.0)
            results = sorted(results, key=lambda x: x["rerank_score"], reverse=True)
        else:
            results = fused[:top_k]

        logger.info("RAG: project=%s roads=%d → fused=%d → final=%d",
                    project_id, len(roads), len(fused), len(results))
        return {"rewritten": rewritten, "keywords": keywords, "results": results}


rag_pipeline = RagPipeline()