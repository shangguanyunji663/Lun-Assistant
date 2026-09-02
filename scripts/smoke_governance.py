"""工具治理与风控冒烟：RBAC → 限流 → 三级容错 → 熔断 → 分布式锁 → 审计 → Skill沉淀。

前置: Redis / 独立 PostgreSQL 实例（D:\Develop\DB\PostgreSQL16）已运行；ollama 可用（Skill 语义匹配用）。
用法：python scripts/smoke_governance.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main() -> None:
    from services.governance.tool_registry import ToolSpec, tool_registry

    # ---------- 注册冒烟专用工具 ----------
    async def ok_tool(query: str):
        return f"OK:{query}"

    async def flaky_tool(query: str):
        raise RuntimeError("模拟下游故障")

    async def degradable_tool(query: str):
        if query == "SAFE_DEFAULT":          # 仅默认参数可成功 → 模拟参数降级生效
            return "FALLBACK_OK"
        raise RuntimeError("原参数失败")

    tool_registry.register(ToolSpec(
        name="smoke_ok", description="冒烟-正常工具", handler=ok_tool,
        rate_limit_rpm=3, breaker="smoke_brk"))
    tool_registry.register(ToolSpec(
        name="smoke_fail", description="冒烟-总是失败", handler=flaky_tool,
        rate_limit_rpm=1000, breaker="smoke_brk2"))
    tool_registry.register(ToolSpec(
        name="smoke_degrade", description="冒烟-可降级", handler=degradable_tool,
        rate_limit_rpm=1000, breaker="smoke_brk3",
        fallback_kwargs={"query": "SAFE_DEFAULT"}))

    # ---------- 1. RBAC：student 禁调 admin_reindex ----------
    from services.governance.rate_limiter import RateLimitExceeded
    from services.governance.retry import HumanInterventionRequired
    tool_registry.register(ToolSpec(
        name="admin_reindex", description="冒烟-管理工具", handler=ok_tool,
        rate_limit_rpm=1000, breaker="smoke_brk4"))
    try:
        await tool_registry.call("admin_reindex", user_id=1, user_role="student")
        print("[RBAC] FAIL - 未拦截")
    except PermissionError as e:
        print(f"[RBAC] PASS - student 被拦截: {e}")

    # ---------- 2. 限流：smoke_ok rpm=3，第4次应拒绝 ----------
    ok_cnt = 0
    limited = False
    for i in range(4):
        try:
            await tool_registry.call("smoke_ok", user_id=900, user_role="student",
                                     query=f"q{i}")
            ok_cnt += 1
        except RateLimitExceeded as e:
            limited = True
            print(f"[限流] PASS - 第{i + 1}次触发: {e}")
            break
    if not limited:
        print(f"[限流] FAIL - 连续{ok_cnt}次未触发（rpm=3）")

    # ---------- 3. 三级容错：降级成功 ----------
    r = await tool_registry.call("smoke_degrade", user_id=900, user_role="student",
                                 query="BAD_PARAM")
    print(f"[降级] {'PASS' if r == 'FALLBACK_OK' else 'FAIL'} - 结果={r}")

    # 三级容错：彻底失败 → 人机兜底
    try:
        await tool_registry.call("smoke_fail", user_id=900, user_role="student", query="x")
        print("[人机兜底] FAIL - 未抛出")
    except HumanInterventionRequired as e:
        print(f"[人机兜底] PASS - {e}")

    # ---------- 4. 熔断：手动打满失败阈值 → OPEN 快速失败 ----------
    from services.governance.circuit_breaker import CircuitBreaker, CircuitOpenError
    brk = CircuitBreaker("smoke_brk2")
    for _ in range(5):
        await brk.on_failure()
    state = await brk.state()
    t0 = asyncio.get_event_loop().time()
    try:
        await tool_registry.call("smoke_fail", user_id=900, user_role="student", query="x")
        print("[熔断] FAIL - OPEN 期间未快速失败")
    except CircuitOpenError:
        fast = asyncio.get_event_loop().time() - t0
        print(f"[熔断] PASS - state={state}, OPEN 期快速失败耗时 {fast * 1000:.0f}ms")

    # 恢复：回拨 opened_at 模拟等待超时 → HALF_OPEN 失败 → 再次 OPEN
    import time as _t

    from infrastructure.redis_client import get_redis
    rds = get_redis()
    await rds.hset("breaker:smoke_brk2", "opened_at", int((_t.time() - 999) * 1000))
    try:
        await tool_registry.call("smoke_fail", user_id=900, user_role="student", query="x")
    except Exception:
        pass
    state2 = await brk.state()
    print(f"[熔断恢复] {'PASS' if state2 == 'OPEN' else 'FAIL'} - HALF_OPEN 失败后 state={state2}")

    # ---------- 5. 分布式锁：互斥 ----------
    from services.governance.dist_lock import DistributedLock, LockNotAcquired
    lock = DistributedLock("smoke:mutex")
    await lock.acquire()
    try:
        async with DistributedLock("smoke:mutex"):
            print("[分布式锁] FAIL - 第二次获取未阻塞")
    except LockNotAcquired:
        print("[分布式锁] PASS - 并发互斥生效")
    await lock.release()
    async with DistributedLock("smoke:mutex"):
        print("[分布式锁] PASS - 释放后可重入")

    # ---------- 6. 审计留痕 ----------
    from sqlalchemy import func, select

    from infrastructure.db import get_session_factory
    from infrastructure.models.audit import AuditLog
    async with get_session_factory()() as db:
        n = await db.scalar(select(func.count()).select_from(AuditLog)
                            .where(AuditLog.action == "tool_call",
                                   AuditLog.resource == "smoke_ok"))
    print(f"[审计] {'PASS' if n and n >= 3 else 'FAIL'} - smoke_ok 审计记录 {n} 条")

    # ---------- 7. Skill 自动沉淀：同模式3次成功 ----------
    from infrastructure.models.skill import Skill
    tracker = tool_registry._tracker
    for i in range(3):
        await tracker.observe(agent="smoke_agent", tool="smoke_ok",
                              params={"query": f"p{i}"}, ok=True, user_id=1)
    async with get_session_factory()() as db:
        sk = (await db.execute(select(Skill).where(Skill.agent == "smoke_agent"))).scalars().first()
    print(f"[Skill] {'PASS' if sk else 'FAIL'} - 沉淀: {sk.name if sk else '无'}")

    # Skill 三维匹配
    if sk:
        hits = await tracker.match_skills("smoke_agent", "帮我执行 smoke_ok 查询")
        print(f"[Skill匹配] {'PASS' if hits else 'FAIL'} - 召回 {len(hits)} 条, "
              f"TOP1={hits[0].name if hits else '-'}")


if __name__ == "__main__":
    asyncio.run(main())
