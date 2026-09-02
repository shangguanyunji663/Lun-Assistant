"""工具注册中心：治理栈统一编排入口。

调用任意工具必经的流水线（对应简历"工具调用治理与三级容错"）:
  1. YAML RBAC 鉴权 → 2. Redis 滑动窗口限流 → 3. 三态熔断检查（before_call）
  → 4. 三级容错执行（指数退避重试→默认参数降级→人机兜底）→ 5. 审计留痕 + 6. 行为观测

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

from infrastructure.audit import write_audit
from infrastructure.db import get_session_factory
from infrastructure.paths import PROJECT_ROOT
from infrastructure.rbac import policy as rbac_policy
from services.governance.circuit_breaker import CircuitBreaker, CircuitOpenError
from services.governance.dist_lock import DistributedLock, LockNotAcquired
from services.governance.rate_limiter import RateLimitExceeded, check_rate
from services.governance.retry import HumanInterventionRequired, resilient_call
from services.governance.skill import BehaviorTracker

logger = logging.getLogger("lunjiang.governance")


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
        spec = self.get(name)
        started = time.perf_counter()

        # 1-2. 鉴权 / 限流：被拒也统一写审计（安全相关事件，不可遗漏）
        try:
            if not rbac_policy.check_tool_permission(user_role, name):
                raise PermissionError(f"角色 {user_role} 无权调用工具 {name}")
            await check_rate(f"{name}:{user_id}", spec.rate_limit_rpm)
        except (PermissionError, RateLimitExceeded) as e:
            await self._finalize(name, user_id, user_role, call_context, started, False, spec, kwargs, error=str(e))
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
            await self._finalize(name, user_id, user_role, call_context, started, True, spec, kwargs)
            return result
        except (CircuitOpenError, HumanInterventionRequired, LockNotAcquired) as e:
            if isinstance(e, HumanInterventionRequired):
                await breaker.on_failure()
            await self._finalize(name, user_id, user_role, call_context, started, False, spec, kwargs, error=str(e))
            raise
        except Exception as e:
            await breaker.on_failure()
            await self._finalize(name, user_id, user_role, call_context, started, False, spec, kwargs, error=str(e))
            raise

    async def _finalize(self, name, user_id, user_role, call_context, started, ok, spec, kwargs, error=""):
        duration_ms = int((time.perf_counter() - started) * 1000)
        # 5. 审计留痕
        try:
            async with get_session_factory()() as db:
                await write_audit(
                    db, user_id=user_id, action="tool_call", resource=name,
                    detail={"ok": ok, "duration_ms": duration_ms, "role": user_role,
                            "args": kwargs, "error": error},
                )
        except Exception:
            logger.exception("工具审计写库失败")
        # 6. 行为观测（Skill 动态生成数据源）
        await self._tracker.observe(
            agent=call_context.get("agent", "system") if call_context else "system",
            tool=name, params=kwargs, ok=ok, user_id=user_id,
        )


# 全局单例
tool_registry = ToolRegistry()
