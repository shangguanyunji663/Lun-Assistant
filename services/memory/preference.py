"""第四层：用户偏好记忆（写作风格/格式习惯，召回 top_k 注入提示词）。"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.config import get_value
from infrastructure.models.memory import MemoryItem
from services.llm.provider import LLMProvider


class PreferenceMemory:
    def __init__(self):
        self._provider: LLMProvider | None = None

    @property
    def provider(self) -> LLMProvider:
        if self._provider is None:
            self._provider = LLMProvider()
        return self._provider

    async def learn(self, db: AsyncSession, *, user_id: int, content: str,
                    source: str = "interaction") -> int:
        """从交互中沉淀偏好（LLM 抽取后的结论由调用方传入）。"""
        emb = (await self.provider.embed([content]))[0]
        item = MemoryItem(user_id=user_id, kind="preference", content=content,
                          embedding=emb, importance=0.8, meta={"source": source})
        db.add(item)
        await db.commit()
        return item.id

    async def recall(self, db: AsyncSession, user_id: int, top_k: int | None = None) -> list[str]:
        top_k = top_k or int(get_value("memory", "preference_top_k", default=10))
        rows = (await db.execute(
            select(MemoryItem).where(MemoryItem.kind == "preference", MemoryItem.user_id == user_id)
            .order_by(MemoryItem.importance.desc(), MemoryItem.id.desc()).limit(top_k)
        )).scalars().all()
        return [r.content for r in rows]


preference_memory = PreferenceMemory()
