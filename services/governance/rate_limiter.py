"""Redis 滑动窗口限流器（ZSET + Lua 原子执行）。"""
import time

from infrastructure.redis_client import get_redis

# KEYS[1]=zset key; ARGV: now_ms, window_ms, limit
_ALLOW_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)
if count < limit then
    redis.call('ZADD', key, now, now .. '-' .. math.random())
    redis.call('PEXPIRE', key, window)
    return {1, limit - count - 1}
end
local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
local retry_ms = window
if #oldest > 1 then
    retry_ms = math.max(1, math.ceil(tonumber(oldest[2]) + window - now))
end
return {0, retry_ms}
"""


class RateLimitExceeded(Exception):
    def __init__(self, retry_after_ms: int):
        self.retry_after_ms = retry_after_ms
        super().__init__(f"触发限流，请 {retry_after_ms}ms 后重试")


async def check_rate(key: str, rpm: int, window_ms: int = 60_000) -> None:
    """滑动窗口限流；超限抛 RateLimitExceeded。"""
    r = get_redis()
    allowed, info = await r.eval(
        _ALLOW_SCRIPT, 1, f"ratelimit:{key}", int(time.time() * 1000), window_ms, rpm
    )
    if not allowed:
        raise RateLimitExceeded(int(info))
