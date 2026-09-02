"""第三层：长期向量记忆（pgvector 召回，覆盖事实/摘要/文档块）。"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.models.memory import MemoryItem
from services.llm.provider import LLMProvider


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
        """向量召回（pgvector cosine 距离）。"""
        qvec = (await self.provider.embed([query]))[0]
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
        rows = list((await db.execute(stmt)).scalars().all())
        # 距离与重要度加权排序
        rows.sort(key=lambda r: r.importance, reverse=True)
        return rows[:top_k]

    async def recall_text(self, db: AsyncSession, *, query: str, **kw) -> str:
        items = await self.recall(db, query=query, **kw)
        return "\n".join(f"- {x.content}" for x in items)


long_term_memory = LongTermMemory()
