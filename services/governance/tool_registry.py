"""工具注册中心：治理栈统一编排入口。

调用任意工具必经的流水线（对应简历"工具调用治理与三级容错"）:
  YAML RBAC 鉴权 → Redis 滑动窗口限流 → 三态熔断检查
  → 三级容错执行（指数退避重试→默认参数降级→人机兜底）→ 审计留痕 + 行为观测
"""
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine
from contextlib import nullcontext

import yaml

from infrastructure.audit import write_audit
from infrastructure.db import get_session_factory
from infrastructure.rbac import policy as rbac_policy

from services.governance.circuit_breaker import CircuitBreaker, CircuitOpenError
from services.governance.dist_lock import DistributedLock, LockNotAcquired
from services.governance.rate_limiter import RateLimitExceeded, check_rate
from services.governance.retry import HumanInterventionRequired, resilient_call
from services.governance.skill import BehaviorTracker
from pathlib import Path

logger = logging.getLogger("lunjiang.governance")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class ToolSpec:
    name: str
    description: str
    handler: Callable[..., Coroutine[Any, Any, Any]] | None = None
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
        with open(PROJECT_ROOT / "configs" / "tools.yaml", encoding="utf-8") as f:
            cfg = yaml.safe_load(f).get("tools", {})
        conf = cfg.get(spec.name, {})
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

    # ---------- 统一治理调用 ----------
    async def call(
        self, name: str, *, user_id: int | None, user_role: str,
        call_context: dict | None = None, **kwargs: Any
    ) -> Any:
        spec = self.get(name)

        # 1. YAML RBAC
        if not rbac_policy.check_tool_permission(user_role, name):
            raise PermissionError(f"角色 {user_role} 无权调用工具 {name}")

        # 2. 滑动窗口限流
        await check_rate(f"{name}:{user_id}", spec.rate_limit_rpm)

        breaker = self._breakers[spec.breaker]

        # 4. 三级容错执行（内含指数退避重试→默认参数降级→人机兜底），互斥工具加分布式锁
        started = time.perf_counter()
        try:
            await breaker.before_call()

            async def _run(**kw):
                return await spec.handler(**kw)

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
