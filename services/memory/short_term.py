"""第一层：短期对话记忆（Redis List，保留最近 N 轮）。"""
import json
import time

from infrastructure.config import get_value
from infrastructure.redis_client import get_redis

_KEY = "chat:{project_id}:{session_id}"


class ShortTermMemory:
    async def append(self, project_id: int, session_id: str, role: str, content: str) -> None:
        r = get_redis()
        max_turns = int(get_value("memory", "short_term_max_turns", default=20))
        key = _KEY.format(project_id=project_id, session_id=session_id)
        await r.rpush(key, json.dumps({"role": role, "content": content,
                                       "ts": time.time()}, ensure_ascii=False))
        await r.ltrim(key, -max_turns * 2, -1)   # 每轮 user+assistant 两条
        await r.expire(key, 7 * 24 * 3600)

    async def history(self, project_id: int, session_id: str, last_n: int | None = None) -> list[dict]:
        r = get_redis()
        key = _KEY.format(project_id=project_id, session_id=session_id)
        raw = await r.lrange(key, 0, -1)
        items = [json.loads(x) for x in raw]
        n = last_n or int(get_value("memory", "short_term_max_turns", default=20))
        return items[-n * 2:]

    async def total_chars(self, project_id: int, session_id: str) -> int:
        items = await self.history(project_id, session_id)
        return sum(len(x["content"]) for x in items)

    async def evict_compressed(self, project_id: int, session_id: str, keep_last: int) -> list[dict]:
        """窗口截断：仅保留最近 keep_last 条，返回被截断部分（供摘要归档）。"""
        r = get_redis()
        key = _KEY.format(project_id=project_id, session_id=session_id)
        raw = await r.lrange(key, 0, -1)
        if len(raw) <= keep_last:
            return []
        evicted = [json.loads(x) for x in raw[:-keep_last]]
        await r.ltrim(key, -keep_last, -1)
        return evicted


short_term_memory = ShortTermMemory()
