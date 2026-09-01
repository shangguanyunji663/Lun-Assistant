"""Redis 分布式锁：SET NX PX + Lua 校验持有者释放，保障多实例任务互斥。"""
import asyncio
import uuid

from infrastructure.config import get_value
from infrastructure.redis_client import get_redis

_RELEASE = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""

_RENEW = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('PEXPIRE', KEYS[1], ARGV[2])
end
return 0
"""


class LockNotAcquired(Exception):
    pass


class DistributedLock:
    """用法:
        async with DistributedLock("task:ingest:42"):
            ...
    """

    def __init__(self, name: str, ttl_seconds: int | None = None):
        self.name = name
        self.ttl_ms = int((ttl_seconds or get_value(
            "governance", "lock", "ttl_seconds", default=300)) * 1000)
        self.token = uuid.uuid4().hex

    @property
    def _key(self) -> str:
        return f"lock:{self.name}"

    async def acquire(self, blocking_timeout: float = 0.0) -> None:
        r = get_redis()
        deadline = blocking_timeout
        while True:
            ok = await r.set(self._key, self.token, nx=True, px=self.ttl_ms)
            if ok:
                return
            if deadline <= 0:
                raise LockNotAcquired(f"分布式锁 {self.name} 获取失败")
            await asyncio.sleep(0.1)
            deadline -= 0.1

    async def release(self) -> None:
        await get_redis().eval(_RELEASE, 1, self._key, self.token)

    async def renew(self) -> bool:
        return bool(await get_redis().eval(_RENEW, 1, self._key, self.token, self.ttl_ms))

    async def __aenter__(self) -> "DistributedLock":
        await self.acquire()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.release()
