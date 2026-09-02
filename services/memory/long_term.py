"""第三层：长期向量记忆（pgvector 召回，覆盖事实/摘要/文档块）。

R13 排序修复：召回改为「语义距离 × 重要度」加权混合排序。
旧实现仅按 importance 重排（语义只能粗筛 top_k*2 候选），语义最相关但
重要性低的记忆会被重要性高却跑题的项顶掉。现保留余弦距离值，在候选集内
先 min-max 归一，再 hybrid = α·距离分 + (1-α)·重要度 混合排序。
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.config import get_value
from infrastructure.models.memory import MemoryItem
from services.llm.provider import LLMProvider


def hybrid_rank(rows_dists: list[tuple["MemoryItem", float]],
                alpha: float, top_k: int) -> list["MemoryItem"]:
    """距离×重要度加权排序（纯函数，便于单测）。

    rows_dists: [(MemoryItem, 余弦距离)]；
    alpha ∈ [0,1]: 语义距离权重（默认 0.7），importance 为次因子。
    """
    rows_dists = [(r, d) for r, d in rows_dists if r is not None and isinstance(d, (int, float))]
    if not rows_dists:
        return []
    dists = [d for _, d in rows_dists]
    d_min, d_max = min(dists), max(dists)
    span = (d_max - d_min) or 1.0
    scored = [
        (alpha * (1 - (d - d_min) / span) + (1 - alpha) * float(r.importance or 0.5), r)
        for r, d in rows_dists
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:top_k]]


class LongTermMemory:
    def __init__(self):
        self._provider: LLMProvider | None = None

    @property
    def provider(self) -> LLMProvider:
        if self._provider is None:
            self._provider = LLMProvider()
        return self._provider

    async def remember(self, db: AsyncSession, *, content: str, kind: str,
                       project_id: int | None = None, user_id: int | None = None,
                       meta: dict | None = None, importance: float = 0.5) -> int:
        emb = (await self.provider.embed([content]))[0]
        item = MemoryItem(project_id=project_id, user_id=user_id, kind=kind,
                          content=content, embedding=emb, meta=meta, importance=importance)
        db.add(item)
        await db.commit()
        return item.id

    async def recall(self, db: AsyncSession, *, query: str, project_id: int | None = None,
                     user_id: int | None = None, kinds: list[str] | None = None,
                     top_k: int = 5) -> list[MemoryItem]:
        """向量召回（pgvector cosine 距离 + 重要度加权混合排序）。"""
        qvec = (await self.provider.embed([query]))[0]
        dist_col = MemoryItem.embedding.cosine_distance(qvec).label("dist")
        stmt = (select(MemoryItem)
                .order_by(MemoryItem.embedding.cosine_distance(qvec))
                .limit(top_k * 2))
        if project_id is not None:
            stmt = stmt.where((MemoryItem.project_id == project_id)
                              | (MemoryItem.project_id.is_(None)))
        if user_id is not None:
            stmt = stmt.where((MemoryItem.user_id == user_id)
                              | (MemoryItem.user_id.is_(None)))
        if kinds:
            stmt = stmt.where(MemoryItem.kind.in_(kinds))
        # .all() 保留 (MemoryItem, dist)；.scalars() 只取单列，取不到距离
        raw = (await db.execute(stmt.add_columns(dist_col))).all()
        rows = [(r, float(d)) for r, d in raw if isinstance(d, (int, float))]
        alpha = float(get_value("memory", "recall_semantic_weight", default=0.7))
        return hybrid_rank(rows, alpha=alpha, top_k=top_k)

    async def recall_text(self, db: AsyncSession, *, query: str, **kw) -> str:
        items = await self.recall(db, query=query, **kw)
        return "\n".join(f"- {x.content}" for x in items)


long_term_memory = LongTermMemory()
