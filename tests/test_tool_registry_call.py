"""工具治理调用流水线单测：call() 在 mock 外部依赖下验证六步治理契约。

设计要点（T2 测试骨架）：
- 外部依赖（Redis / Postgres）全部以 unittest.mock 在模块边界隔离，整套用例全离线可跑，
  不依赖任何运行中的 Redis / DB 实例，可在 CI 与本地无环境一键执行。
- 覆盖治理契约的关键分支：RBAC 拒绝、限流拒绝、熔断打开、三级容错耗尽（人机兜底）、
  通用异常、同步/异步 handler 接入、分布式锁装配、行为观测上下文透传、审计留痕 ok 标志。
- 不重复验证 resilient_call 自身的重试/降级逻辑（由 services/governance/tests 单独覆盖），
  这里只验证 call() 对各环节的「编排与异常传播」是否正确。

治理补全（第六轮）：RBAC 拒绝与限流拒绝现已统一走 `_finalize()` 审计通道，
被拒调用（安全相关事件）也会落审计日志（ok=False），与执行成功/失败走同一审计。
相关用例改为 `write_audit.assert_awaited_once()` + `detail["ok"] is False` 锁定该行为。

被 mock 的模块边界（均在 services/governance/tool_registry.py 命名空间内）：
- rbac_policy.check_tool_permission          （YAML RBAC 鉴权）
- check_rate                                （Redis 滑动窗口限流）
- CircuitBreaker                           （三态熔断 before/success/failure）
- DistributedLock                          （Redis 分布式锁）
- resilient_call                           （三级容错执行）
- get_session_factory + write_audit        （审计落库）
- BehaviorTracker.observe                  （行为观测 / Skill 沉淀数据源）
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.governance.circuit_breaker import CircuitOpenError
from services.governance.dist_lock import LockNotAcquired
from services.governance.rate_limiter import RateLimitExceeded
from services.governance.retry import HumanInterventionRequired
from services.governance.tool_registry import ToolRegistry, ToolSpec


@pytest.fixture
def reg():
    """隔离的 ToolRegistry，外部依赖默认全部 mock 为「放行 / 无副作用」。"""
    registry = ToolRegistry()

    with patch("services.governance.tool_registry.rbac_policy") as rbac, \
         patch("services.governance.tool_registry.check_rate") as check_rate, \
         patch("services.governance.tool_registry.CircuitBreaker") as CBCls, \
         patch("services.governance.tool_registry.DistributedLock") as LockCls, \
         patch("services.governance.tool_registry.resilient_call") as resilient, \
         patch("services.governance.tool_registry.get_session_factory") as get_sf, \
         patch("services.governance.tool_registry.write_audit") as write_audit:

        # 1) RBAC：默认放行
        rbac.check_tool_permission.return_value = True

        # 2) 限流：默认放行（协程，返回 None 即不抛异常）
        check_rate.return_value = None

        # 3) 熔断器 fake：before/success/failure 均为 AsyncMock
        breaker = AsyncMock()
        breaker.before_call = AsyncMock()
        breaker.on_success = AsyncMock()
        breaker.on_failure = AsyncMock()
        CBCls.return_value = breaker  # register() 内构造的也是这个 fake

        # 4) 分布式锁 fake：充当 async context manager（无真实 Redis 交互）
        lock = AsyncMock()
        LockCls.return_value = lock

        # 5) 三级容错 fake：直接调用内部 fn（等价于「首轮即成功」）
        async def _direct(fn, *, tool_name=None, fallback_kwargs=None, **kwargs):
            return await fn(**kwargs)
        resilient.side_effect = _direct

        # 6) 审计落库：get_session_factory()() 返回 async CM；write_audit 为 AsyncMock
        db_cm = AsyncMock()
        get_sf.return_value.return_value = db_cm
        write_audit.return_value = None

        # 行为观测：直接替换实例，避免触及真实 Redis / skills 表
        tracker = MagicMock()
        tracker.observe = AsyncMock()
        registry._tracker = tracker

        registry._mocks = SimpleNamespace(
            rbac=rbac, check_rate=check_rate, breaker=breaker,
            lock_cls=LockCls, lock=lock,
            resilient=resilient, get_sf=get_sf, write_audit=write_audit, tracker=tracker,
        )
        yield registry


def _register(reg, name, handler, **spec_kw):
    spec = ToolSpec(name=name, description="x", handler=handler, **spec_kw)
    reg.register(spec)
    return spec


# ---------- 1. 成功主路径 ----------

async def test_call_happy_path_returns_result_and_signals_success(reg):
    async def tool(x: int) -> int:
        return x + 1

    _register(reg, "t_happy", tool)
    out = await reg.call("t_happy", user_id=1, user_role="student", x=41)

    assert out == 42
    reg._mocks.breaker.on_success.assert_awaited_once()
    reg._mocks.breaker.on_failure.assert_not_awaited()
    reg._mocks.tracker.observe.assert_awaited_once()
    reg._mocks.write_audit.assert_awaited_once()
    detail = reg._mocks.write_audit.call_args.kwargs["detail"]
    assert detail["ok"] is True


# ---------- 2. RBAC 拒绝 ----------

async def test_call_rbac_denied_raises_and_skips_execution(reg):
    ran = False
    async def tool():
        nonlocal ran
        ran = True
        return 1
    _register(reg, "t_rbac", tool)

    reg._mocks.rbac.check_tool_permission.return_value = False
    with pytest.raises(PermissionError):
        await reg.call("t_rbac", user_id=1, user_role="student")

    assert ran is False                       # handler 未被执行
    reg._mocks.resilient.assert_not_awaited()  # 未进入执行阶段
    reg._mocks.breaker.on_failure.assert_not_awaited()
    # 治理补全（第六轮）：RBAC 拒绝现统一写审计，被拒属安全相关事件不再遗漏
    reg._mocks.write_audit.assert_awaited_once()
    assert reg._mocks.write_audit.call_args.kwargs["detail"]["ok"] is False


# ---------- 3. 限流拒绝 ----------

async def test_call_rate_limit_raises_before_execution(reg):
    async def tool():
        return 1
    _register(reg, "t_rl", tool)

    reg._mocks.check_rate.side_effect = RateLimitExceeded(1234)
    with pytest.raises(RateLimitExceeded):
        await reg.call("t_rl", user_id=1, user_role="student")

    reg._mocks.resilient.assert_not_awaited()
    # 治理补全（第六轮）：限流拒绝同样统一写审计（ok=False）
    reg._mocks.write_audit.assert_awaited_once()
    assert reg._mocks.write_audit.call_args.kwargs["detail"]["ok"] is False


# ---------- 4. 熔断打开（快速失败） ----------

async def test_call_circuit_open_raises_without_execution(reg):
    async def tool():
        return 1
    _register(reg, "t_cb", tool)

    reg._mocks.breaker.before_call.side_effect = CircuitOpenError("fused")
    with pytest.raises(CircuitOpenError):
        await reg.call("t_cb", user_id=1, user_role="student")

    reg._mocks.resilient.assert_not_awaited()  # 熔断在 before_call 阶段即拦截
    reg._mocks.breaker.on_failure.assert_not_awaited()  # 仅 HumanInterventionRequired 触发失败计数
    assert reg._mocks.write_audit.call_args.kwargs["detail"]["ok"] is False


# ---------- 5. 三级容错耗尽 → 人机兜底 ----------

async def test_call_resilient_exhaustion_triggers_human_intervention(reg):
    async def tool():
        return 1
    _register(reg, "t_hi", tool)

    reg._mocks.resilient.side_effect = HumanInterventionRequired("t_hi", RuntimeError("all retries failed"))
    with pytest.raises(HumanInterventionRequired):
        await reg.call("t_hi", user_id=1, user_role="student")

    reg._mocks.breaker.on_failure.assert_awaited_once()  # HumanInterventionRequired 分支记账失败
    assert reg._mocks.write_audit.call_args.kwargs["detail"]["ok"] is False


# ---------- 6. 通用异常传播 + 失败记账 ----------

async def test_call_generic_exception_propagates_and_records_failure(reg):
    async def tool():
        return 1
    _register(reg, "t_err", tool)

    reg._mocks.resilient.side_effect = ValueError("boom")
    with pytest.raises(ValueError):
        await reg.call("t_err", user_id=1, user_role="student")

    reg._mocks.breaker.on_failure.assert_awaited_once()
    assert reg._mocks.write_audit.call_args.kwargs["detail"]["ok"] is False


# ---------- 7. 同步 handler 经治理流水线执行 ----------

async def test_call_sync_handler_via_pipeline(reg):
    def tool(text: str) -> str:
        return text.upper()

    _register(reg, "t_sync", tool)
    out = await reg.call("t_sync", user_id=1, user_role="student", text="abc")
    assert out == "ABC"
    reg._mocks.tracker.observe.assert_awaited_once()


# ---------- 8. 分布式锁装配（互斥工具） ----------

async def test_call_distributed_lock_assembled_for_locked_tool(reg):
    async def tool():
        return "ok"
    _register(reg, "t_lock", tool, lock_key="task:ingest:42")

    out = await reg.call("t_lock", user_id=1, user_role="student")
    assert out == "ok"
    # DistributedLock 以 spec.lock_key 构造，并实际进入 async with（acquire）
    reg._mocks.lock_cls.assert_called_once_with("task:ingest:42")
    reg._mocks.lock.__aenter__.assert_awaited()


# ---------- 9. 行为观测上下文透传（agent 来源 call_context） ----------

async def test_call_observes_agent_from_call_context(reg):
    async def tool():
        return 1
    _register(reg, "t_ctx", tool)

    await reg.call("t_ctx", user_id=7, user_role="student",
                   call_context={"agent": "planner"})
    reg._mocks.tracker.observe.assert_awaited_once()
    kw = reg._mocks.tracker.observe.call_args.kwargs
    assert kw["agent"] == "planner"
    assert kw["tool"] == "t_ctx"
    assert kw["user_id"] == 7
    assert kw["ok"] is True
