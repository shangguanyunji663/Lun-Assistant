"""三态熔断器（CLOSED / OPEN / HALF_OPEN），依托 Redis Lua 原子切换状态。

- 连续失败达到阈值 → OPEN；等 recovery_timeout 后 → HALF_OPEN；
- HALF_OPEN 下连续 half_open_successes 次成功 → CLOSED，任一失败 → OPEN。
- 状态存 Redis Hash，多实例共享同一熔断视图。
"""
import time

from infrastructure.config import get_value
from infrastructure.redis_client import get_redis

_STATE_KEY = "breaker:{name}"

_BEFORE_CALL = """
local st = redis.call('HMGET', KEYS[1], 'state', 'opened_at')
local state = st[1] or 'CLOSED'
local opened_at = tonumber(st[2] or 0)
local timeout = tonumber(ARGV[1])
if state == 'OPEN' then
    if opened_at + timeout * 1000 <= tonumber(ARGV[2]) then
        redis.call('HSET', KEYS[1], 'state', 'HALF_OPEN', 'half_successes', 0)
        return 'HALF_OPEN'
    end
    return 'OPEN'
end
return state
"""

_ON_RESULT = """
local key = KEYS[1]
local is_success = tonumber(ARGV[1])
local fail_threshold = tonumber(ARGV[2])
local half_need = tonumber(ARGV[3])
local state = redis.call('HGET', key, 'state') or 'CLOSED'
if is_success == 1 then
    if state == 'HALF_OPEN' then
        local n = redis.call('HINCRBY', key, 'half_successes', 1)
        if n >= half_need then
            redis.call('HSET', key, 'state', 'CLOSED', 'failures', 0, 'half_successes', 0)
            return 'CLOSED'
        end
        return 'HALF_OPEN'
    end
    redis.call('HSET', key, 'failures', 0)
    return 'CLOSED'
else
    if state == 'HALF_OPEN' then
        redis.call('HSET', key, 'state', 'OPEN', 'opened_at', ARGV[4])
        return 'OPEN'
    end
    local f = redis.call('HINCRBY', key, 'failures', 1)
    if f >= fail_threshold then
        redis.call('HSET', key, 'state', 'OPEN', 'opened_at', ARGV[4])
        return 'OPEN'
    end
    return 'CLOSED'
end
"""


class CircuitOpenError(Exception):
    """熔断打开期间的快速失败。"""


class CircuitBreaker:
    def __init__(self, name: str):
        self.name = name
        self.failure_threshold = int(get_value(
            "governance", "circuit_breaker", "failure_threshold", default=5))
        self.recovery_timeout = float(get_value(
            "governance", "circuit_breaker", "recovery_timeout", default=30))
        self.half_open_successes = int(get_value(
            "governance", "circuit_breaker", "half_open_successes", default=2))

    @property
    def _key(self) -> str:
        return _STATE_KEY.format(name=self.name)

    async def before_call(self) -> None:
        r = get_redis()
        state = await r.eval(  # type: ignore[misc]
            _BEFORE_CALL, 1, self._key,
            self.recovery_timeout, int(time.time() * 1000),
        )
        if state == "OPEN":
            raise CircuitOpenError(f"[{self.name}] 熔断打开中，请求被快速失败")

    async def on_success(self) -> None:
        await get_redis().eval(_ON_RESULT, 1, self._key, 1,  # type: ignore[misc]
                               self.failure_threshold, self.half_open_successes, 0)

    async def on_failure(self) -> None:
        await get_redis().eval(_ON_RESULT, 1, self._key, 0,  # type: ignore[misc]
                               self.failure_threshold, self.half_open_successes,
                               int(time.time() * 1000))

    async def state(self) -> str:
        return await get_redis().hget(self._key, "state") or "CLOSED"  # type: ignore[misc]
