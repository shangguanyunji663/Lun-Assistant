"""RAG 阶段二：双路混合召回 —— 稠密向量(pgvector) + 稀疏 BM25(jieba分词)，RRF 融合。"""
import jieba
from rank_bm25 import BM25Okapi
from sqlalchemy import select

from app.db import get_session_factory
from app.models.memory import MemoryItem
from core.llm.provider import LLMProvider


class HybridRetriever:
    def __init__(self):
        self._provider = LLMProvider()
        self._bm25: BM25Okapi | None = None
        self._corpus_ids: list[int] = []
        self._corpus_meta: dict[int, dict] = {}

    # ---------- 稠密路 ----------
    async def dense_search(self, query: str, top_k: int = 20,
                           project_id: int | None = None) -> list[dict]:
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

    def sparse_search(self, query: str, top_k: int = 20) -> list[dict]:
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
