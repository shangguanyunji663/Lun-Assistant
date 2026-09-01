"""RAG 阶段二：双路混合召回 —— 稠密向量(pgvector) + 稀疏 BM25(jieba分词)，RRF 融合。

⚠️ BM25 索引管理：服务重启后 `_bm25` 为 None，必须重建。采用"启动期预加载 + 首查询懒重建"
双保险策略，避免 sparse_search 永远返回空列表造成召回率骤降。

存储说明：稠密路依赖 pgvector、相邻窗口路依赖 PostgreSQL 的
json_extract_path_text（JSON 列文本提取）——检索层与 PostgreSQL 强绑定。
"""
import asyncio
import logging
from collections import defaultdict

import jieba
from rank_bm25 import BM25Okapi
from sqlalchemy import select, and_, or_, func

from infrastructure.db import get_session_factory
from infrastructure.models.memory import MemoryItem
from services.llm.provider import LLMProvider

logger = logging.getLogger("lunjiang.rag")


class HybridRetriever:
    def __init__(self):
        self._provider = LLMProvider()
        self._bm25: BM25Okapi | None = None
        self._corpus_ids: list[int] = []
        self._corpus_meta: dict[int, dict] = {}
        self._rebuild_lock = asyncio.Lock()  # 防止并发重复重建

    # ---------- 稠密路 ----------
    async def dense_search(self, query: str, top_k: int = 20) -> list[dict]:
        """公共语料域稠密检索（document/fact/summary；BM25 索引同域，保证融合口径一致）。

        项目私有文档走 project_dense_search（kind="user_doc" + project_id 隔离）。
        """
        qvec = (await self._provider.embed([query]))[0]
        async with get_session_factory()() as db:
            rows = (await db.execute(
                select(MemoryItem)
                .where(MemoryItem.kind.in_(["document", "fact", "summary"]))
                .order_by(MemoryItem.embedding.cosine_distance(qvec))
                .limit(top_k)
            )).scalars().all()
        return [{"id": r.id, "content": r.content, "kind": r.kind, "meta": r.meta,
                 "dense_score": 1.0} for r in rows]

    async def project_dense_search(self, query: str, project_id: int,
                                   top_k: int = 20) -> list[dict]:
        """项目级私有知识库稠密检索（kind="user_doc" + project_id 隔离）。"""
        qvec = (await self._provider.embed([query]))[0]
        async with get_session_factory()() as db:
            rows = (await db.execute(
                select(MemoryItem)
                .where(MemoryItem.kind == "user_doc",
                       MemoryItem.project_id == project_id)
                .order_by(MemoryItem.embedding.cosine_distance(qvec))
                .limit(top_k)
            )).scalars().all()
        return [{"id": r.id, "content": r.content, "kind": r.kind, "meta": r.meta,
                 "dense_score": 1.0} for r in rows]

    # ---------- 稀疏路 ----------
    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [t for t in jieba.lcut(text) if t.strip()]

    async def rebuild_bm25(self) -> int:
        """全量重建 BM25 索引（语料入库后调用；语料量大时应改增量）。"""
        async with get_session_factory()() as db:
            rows = (await db.execute(
                select(MemoryItem).where(MemoryItem.kind == "document")
            )).scalars().all()
        self._corpus_ids = [r.id for r in rows]
        self._corpus_meta = {r.id: {"meta": r.meta, "content": r.content} for r in rows}
        if rows:
            corpus = [self._tokenize(r.content) for r in rows]
            self._bm25 = BM25Okapi(corpus)
        else:
            self._bm25 = None
        return len(self._corpus_ids)

    async def _ensure_bm25(self) -> None:
        """懒重建：sparse_search 首次调用或索引丢失时自动从 DB 恢复 BM25 索引。"""
        if self._bm25 is not None:
            return
        async with self._rebuild_lock:
            if self._bm25 is not None:  # double-check
                return
            count = await self.rebuild_bm25()
            logger.info("BM25 索引懒重建完成，文档数: %d", count)

    async def sparse_search(self, query: str, top_k: int = 20) -> list[dict]:
        """（异步化）稀疏 BM25 检索，首调用自动懒加载索引。"""
        await self._ensure_bm25()
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(self._tokenize(query))
        ranked = sorted(zip(self._corpus_ids, scores), key=lambda x: x[1], reverse=True)[:top_k]
        out = []
        for doc_id, score in ranked:
            if score <= 0:
                continue
            m = self._corpus_meta.get(doc_id, {})
            out.append({"id": doc_id, "content": m.get("content", ""), "kind": "document",
                        "meta": m.get("meta"), "sparse_score": float(score)})
        return out

    # ---------- 第三引擎：相邻窗口召回 ----------
    async def sibling_search(self, hits: list[dict], window: int = 1,
                             top_k: int = 20) -> list[dict]:
        """命中块的相邻窗口召回：取同一来源（语料文件/项目文档）内前后 window 个分块。

        定位方式：语料用 meta["file"]、项目文档用 meta["doc_key"]，chunk 序号在 meta["chunk"]。
        价值：命中段落在分块边缘时补齐上下文，避免截断信息；作为 RRF 第三路参与融合。
        """
        if not hits or window <= 0:
            return []
        # 汇总 (来源键, {目标chunk序号})
        wanted: dict[str, set[int]] = defaultdict(set)
        for h in hits:
            meta = h.get("meta") or {}
            src = meta.get("doc_key") or meta.get("file")
            ci = meta.get("chunk")
            if not src or ci is None:
                continue
            for d in range(ci - window, ci + window + 1):
                if d != ci and d >= 0:
                    wanted[src].add(d)
        if not wanted:
            return []

        # 语料: (kind=document AND meta->>'file'==src)；项目文档: (kind=user_doc AND meta->>'doc_key'==src)
        # memory_items.meta 为 JSON 列（非 JSONB），用 json_extract_path_text 提取文本值
        conds = []
        for src, idxs in wanted.items():
            src_cond = or_(
                and_(MemoryItem.kind == "document",
                     func.json_extract_path_text(MemoryItem.meta, "file") == src),
                and_(MemoryItem.kind == "user_doc",
                     func.json_extract_path_text(MemoryItem.meta, "doc_key") == src),
            )
            for i in sorted(idxs)[:64]:
                conds.append(and_(
                    src_cond,
                    func.json_extract_path_text(MemoryItem.meta, "chunk") == str(i)))
        if not conds:
            return []

        async with get_session_factory()() as db:
            rows = (await db.execute(
                select(MemoryItem).where(or_(*conds))
            )).scalars().all()
        return [{"id": r.id, "content": r.content, "kind": r.kind, "meta": r.meta,
                 "sibling_score": 1.0} for r in rows][:top_k]

    # ---------- RRF 融合 ----------
    @staticmethod
    def rrf_fuse(*result_lists: list[dict], k: int = 60, top_k: int = 20) -> list[dict]:
        """Reciprocal Rank Fusion 融合多路召回。"""
        fused: dict[int, dict] = {}
        for results in result_lists:
            for rank, item in enumerate(results):
                rrf = 1.0 / (k + rank + 1)
                if item["id"] not in fused:
                    fused[item["id"]] = {**item, "rrf_score": 0.0}
                fused[item["id"]]["rrf_score"] += rrf
        ranked = sorted(fused.values(), key=lambda x: x["rrf_score"], reverse=True)
        return ranked[:top_k]


hybrid_retriever = HybridRetriever()
