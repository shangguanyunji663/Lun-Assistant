"""Redis 连接（治理层：限流/熔断/分布式锁/缓存共用）。"""
import redis.asyncio as aioredis

from infrastructure.config import get_value

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            get_value("storage", "redis", "url"),
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
