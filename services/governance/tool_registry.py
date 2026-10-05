"""工具注册中心：治理栈统一编排入口。

调用任意工具必经的七步流水线（对应简历"工具调用治理与三级容错"）:
  1. YAML RBAC 鉴权 → 2. Redis 滑动窗口限流 → 3. 三态熔断检查（before_call）
  → 4. 分布式锁（仅 lock_key 非空时启用）→ 5. 三级容错执行（指数退避重试→默认参数降级→人机兜底）
  → 6. 审计留痕 → 7. 行为观测

Redis 不可用时的策略（fail-closed，与登录限流的 fail-open 不同）：
- 限流 / 熔断 / 分布式锁无法履职时**拒绝**工具调用，抛 `GovernanceUnavailable`。
  三者的 fail-closed 恰好等价于「不超额 / 不打下游 / 不并发」，即保护生效的方向；
- 但审计**一定**落库（try/finally 保证），被拒事件同样留痕（ok=False），
  不因基础设施故障而丢失安全记录。

注册约定：
- handler 支持同步与异步两种实现；同步 handler 在线程池执行（规则型/CPU 密集
  工具不再阻塞事件循环）；
- tools.yaml 治理配置（限流/锁/降级参数/熔断分组）进程内一次性加载并缓存，
  register() 幂等：重复注册同一 handler 直接跳过，支持任意入口多次 register_all。
"""
import asyncio
import inspect
import logging
import time
from contextlib import nullcontext
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Callable, Coroutine, cast

import yaml
from redis.exceptions import RedisError

from infrastructure.audit import write_audit
from infrastructure.db import get_session_factory
from infrastructure.paths import PROJECT_ROOT
from infrastructure.rbac import policy as rbac_policy
from services.governance.circuit_breaker import CircuitBreaker, CircuitOpenError
from services.governance.dist_lock import DistributedLock, LockNotAcquired
from services.governance.rate_limiter import check_rate
from services.governance.retry import HumanInterventionRequired, resilient_call
from services.governance.skill import BehaviorTracker

logger = logging.getLogger("lunjiang.governance")


class GovernanceUnavailable(RuntimeError):
    """治理基础设施（Redis）不可用，工具调用按 fail-closed 策略被拒绝。

    与「工具自身执行失败」区分开：这表示限流 / 熔断 / 分布式锁无法履职，
    治理层选择不放行，而不是工具本身出问题。调用方可据此给出运维向的提示。
    """


_REDIS_HINT = ("[{name}] 限流 / 熔断 / 分布式锁依赖的 Redis 不可用，已按 fail-closed 拒绝本次调用。"
               "请确认 redis-server 已启动（端口见 .env 的 REDIS_PORT），"
               "或用 scripts/dev_up.ps1 -infra-only 拉起依赖")


@lru_cache(maxsize=1)
def _tools_yaml_config() -> dict:
    """tools.yaml 治理配置（进程内一次性加载，避免每次注册重复磁盘 IO）。"""
    path = PROJECT_ROOT / "configs" / "tools.yaml"
    with open(path, encoding="utf-8") as f:
        return (yaml.safe_load(f) or {}).get("tools", {}) or {}


@dataclass
class ToolSpec:
    name: str
    description: str
    handler: Callable[..., Coroutine[Any, Any, Any]] | Callable[..., Any] | None = None
    rate_limit_rpm: int = 30
    lock_key: str | None = None            # 需要互斥的工具填（如批量写库）
    fallback_kwargs: dict = field(default_factory=dict)  # 默认参数降级
    breaker: str = "default"


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}
        self._breakers: dict[str, CircuitBreaker] = {}
        self._tracker = BehaviorTracker()

    # ---------- 注册 ----------
    def register(self, spec: ToolSpec) -> None:
        """注册工具并合并 YAML 治理配置。幂等：同一 handler 重复注册直接跳过。"""
        existing = self._tools.get(spec.name)
        if existing is not None and existing.handler is spec.handler:
            return
        conf = _tools_yaml_config().get(spec.name, {})
        spec.rate_limit_rpm = conf.get("rate_limit_rpm", spec.rate_limit_rpm)
        spec.lock_key = conf.get("lock_key", spec.lock_key)
        spec.fallback_kwargs = conf.get("fallback_kwargs", spec.fallback_kwargs)
        spec.breaker = conf.get("breaker", spec.breaker)
        self._tools[spec.name] = spec
        if spec.breaker not in self._breakers:
            self._breakers[spec.breaker] = CircuitBreaker(spec.breaker)

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise KeyError(f"工具未注册: {name}")
        return self._tools[name]

    @property
    def tools(self) -> dict[str, ToolSpec]:
        return dict(self._tools)

    # ---------- handler 统一适配 ----------
    async def _invoke_handler(self, spec: ToolSpec, **kwargs: Any) -> Any:
        """异步 handler 直接 await；同步 handler 放线程池，避免冻结事件循环。"""
        if inspect.iscoroutinefunction(spec.handler):
            return await spec.handler(**kwargs)
        fn = cast(Callable[..., Any], spec.handler)
        return await asyncio.to_thread(fn, **kwargs)

    # ---------- 统一治理调用 ----------
    async def call(
        self, name: str, *, user_id: int | None, user_role: str,
        call_context: dict | None = None, **kwargs: Any
    ) -> Any:
        """治理流水线统一入口。

        失败语义（fail-closed）：限流 / 熔断 / 分布式锁任一环节因 Redis 不可用而失败时，
        **拒绝**本次调用——「限不住就不放行」是治理层既定立场。三者的 fail-closed 恰好
        等价于「不超额 / 不打下游 / 不并发」，即保护生效的方向，故不做 fail-open。

        留痕语义：无论成功、被拒还是失败，`_finalize()` 审计写库由 try/finally 保证
        **一定执行**。此前 Redis 故障会从三条路径绕过审计（限流异常直接逃逸、
        on_failure 二次抛、锁异常未被捕获），安全留痕丢失。
        """
        spec = self.get(name)
        started = time.perf_counter()
        ok, error = False, ""

        try:
            # 1-2. 鉴权 / 限流（被拒也统一写审计，安全相关事件不可遗漏）
            try:
                if not rbac_policy.check_tool_permission(user_role, name):
                    raise PermissionError(f"角色 {user_role} 无权调用工具 {name}")
                await check_rate(f"{name}:{user_id}", spec.rate_limit_rpm)
            except RedisError as e:
                error = f"限流不可用（Redis）：{e}"
                logger.warning("Redis 不可用，限流无法履职，按 fail-closed 拒绝: tool=%s", name)
                raise GovernanceUnavailable(_REDIS_HINT.format(name=name)) from e
            except Exception as e:
                error = str(e)
                raise

            breaker = self._breakers[spec.breaker]

            # 3-4. 熔断检查 + 三级容错执行（重试→降级→人机兜底），互斥工具加分布式锁
            try:
                await breaker.before_call()

                async def _run(**kw):
                    return await self._invoke_handler(spec, **kw)

                lock = DistributedLock(spec.lock_key) if spec.lock_key else None
                cm = lock if lock is not None else nullcontext()
                async with cm:
                    result = await resilient_call(
                        _run, tool_name=name,
                        fallback_kwargs=spec.fallback_kwargs or None,
                        **kwargs,
                    )
                await breaker.on_success()
                ok = True
                return result
            except RedisError as e:
                error = f"熔断/分布式锁不可用（Redis）：{e}"
                logger.warning("Redis 不可用，熔断或锁无法履职，按 fail-closed 拒绝: tool=%s", name)
                await self._breaker_fail(breaker)
                raise GovernanceUnavailable(_REDIS_HINT.format(name=name)) from e
            except (CircuitOpenError, HumanInterventionRequired, LockNotAcquired) as e:
                error = str(e)
                if isinstance(e, HumanInterventionRequired):
                    await self._breaker_fail(breaker)
                raise
            except Exception as e:
                error = str(e)
                await self._breaker_fail(breaker)
                raise
        finally:
            await self._finalize(name, user_id, user_role, call_context,
                                 started, ok, spec, kwargs, error=error)

    async def _breaker_fail(self, breaker: CircuitBreaker) -> None:
        """熔断失败记账：回写失败只记日志，绝不二次抛出。

        Redis 不可用时 on_failure 必然连不上；若在此抛出，既会顶掉真实异常，
        也会让 finally 中的审计语义失真（异常替换）。
        """
        try:
            await breaker.on_failure()
        except Exception:
            logger.warning("熔断状态回写失败（Redis 不可用时属预期行为）", exc_info=True)

    async def _finalize(self, name, user_id, user_role, call_context, started, ok, spec, kwargs, error=""):
        duration_ms = int((time.perf_counter() - started) * 1000)
        # 5. 审计留痕（写 PG，不受 Redis 故障影响）
        try:
            async with get_session_factory()() as db:
                await write_audit(
                    db, user_id=user_id, action="tool_call", resource=name,
                    detail={"ok": ok, "duration_ms": duration_ms, "role": user_role,
                            "args": kwargs, "error": error},
                )
        except Exception:
            logger.exception("工具审计写库失败")
        # 6. 行为观测（Skill 动态生成数据源，走 Redis；失败只记日志，不掩盖原始异常）
        try:
            await self._tracker.observe(
                agent=call_context.get("agent", "system") if call_context else "system",
                tool=name, params=kwargs, ok=ok, user_id=user_id,
            )
        except Exception:
            logger.warning("行为观测写入失败（Redis 不可用时属预期行为）", exc_info=True)


# 全局单例
tool_registry = ToolRegistry()
