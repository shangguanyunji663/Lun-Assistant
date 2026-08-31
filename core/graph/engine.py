"""主从引擎运行入口：单例图 + 三级 Checkpointer + EventHub 事件流 + interrupt/resume。

每次 run():
- 组装记忆上下文（短期对话 + 项目结构化摘要，降级为空不影响主流程）
- 生产者协程驱动 graph.astream（节点内部自行向 hub emit 事件），
  消费端从 hub 顺序读取 StreamEvent（token / node / intent / interrupt / final / done / error）
- 图因 interrupt 挂起时提取中断载荷下发 interrupt 事件；
  再次调用 run(resume=...) 携带用户反馈续跑
"""
import asyncio
import contextlib
import logging
from typing import Any, AsyncIterator

from core.checkpoint.tiered import TieredCheckpointer
from core.streaming.hub import EventHub, StreamEvent

logger = logging.getLogger("lunjiang.engine")


class AgentEngine:
    _graph = None
    _tier: str | None = None
    _lock = asyncio.Lock()

    # ---------- 图单例 ----------
    @classmethod
    async def get_graph(cls):
        if cls._graph is None:
            async with cls._lock:
                if cls._graph is None:
                    saver, tier = await TieredCheckpointer.create()
                    from core.graph.builder import build_graph
                    cls._graph = build_graph(checkpointer=saver)
                    cls._tier = tier
                    logger.info("LangGraph 编译完成, checkpointer=%s", tier)
        return cls._graph

    # ---------- 运行 ----------
    @classmethod
    async def run(
        cls,
        *,
        session_id: str,
        user_input: str = "",
        user_id: int,
        user_role: str = "student",
        project_id: int | None = None,
        resume: Any = None,
        hub: EventHub | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """执行一轮对话。resume 非 None 时为 interrupt 续跑（user_input 被忽略）。

        用法:
            engine = AgentEngine()
            async for ev in engine.run(session_id=..., user_input=..., user_id=...):
                ...
        """
        hub = hub or EventHub()
        graph = await cls.get_graph()
        config = {"configurable": {"thread_id": session_id}}

        if resume is not None:
            from langgraph.types import Command
            invoke_input: Any = Command(resume=resume)
        else:
            history_text, memory_brief = await cls._assemble_memory(
                project_id=project_id, session_id=session_id,
                user_id=user_id, user_input=user_input)
            invoke_input = {
                "user_input": user_input, "user_id": user_id,
                "user_role": user_role, "project_id": project_id,
                "session_id": session_id,
                "history_text": history_text, "memory_brief": memory_brief,
                "visited_agents": [], "agent_results": {},
            }

        async def produce() -> None:
            from core.streaming.hub import bind_hub
            with bind_hub(hub):
                try:
                    async for _ in graph.astream(invoke_input, config=config,
                                                 stream_mode="updates"):
                        pass  # 节点内部已向 hub emit 事件
                    snap = await graph.aget_state(config)
                    if snap.next:
                        # interrupt 挂起：下发中断载荷等待 resume
                        payload = _interrupt_payload(snap)
                        if payload is not None:
                            await hub.emit("interrupt", payload)
                    else:
                        await hub.emit("final", {
                            "output": (snap.values or {}).get("final_output", ""),
                            "intent": (snap.values or {}).get("intent", ""),
                            "visited_agents": (snap.values or {}).get("visited_agents", []),
                        })
                except Exception as e:
                    logger.exception("图执行失败 session=%s", session_id)
                    await hub.emit("error", {"message": str(e)})
                finally:
                    await hub.close()

        task = asyncio.create_task(produce())
        try:
            async for ev in hub.stream():
                yield ev
        finally:
            if not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

    # ---------- 记忆装配（四层，降级安全） ----------
    @staticmethod
    async def _assemble_memory(*, project_id, session_id, user_id=None,
                               user_input="") -> tuple[str, str]:
        """短期对话 + 项目结构化 + 长期向量召回 + 用户偏好，任一层失败跳过。"""
        history_text, brief_parts = "", []

        # L1 短期对话
        try:
            from memory.short_term import short_term_memory
            msgs = await short_term_memory.history(project_id, session_id)
            history_text = "\n".join(
                f"{'用户' if m.get('role') == 'user' else '助手'}: {m.get('content', '')}"
                for m in msgs[-8:])
        except Exception:
            logger.warning("短期记忆不可用，跳过历史装配", exc_info=True)

        try:
            from app.db import get_session_factory
            factory = get_session_factory()
            async with factory() as db:
                # L2 项目结构化
                if project_id is not None:
                    from memory.structured import structured_memory
                    mem = await structured_memory.get(db, project_id)
                    brief = structured_memory.render_brief(mem)
                    if brief:
                        brief_parts.append(brief)
                # L3 长期向量召回（摘要/事实/决策）
                if user_input:
                    from memory.long_term import long_term_memory
                    recalled = await long_term_memory.recall_text(
                        db, query=user_input, project_id=project_id,
                        user_id=user_id, kinds=["summary", "decision", "fact"],
                        top_k=3)
                    if recalled:
                        brief_parts.append(f"[相关历史记忆]\n{recalled}")
                # L4 用户偏好
                if user_id is not None:
                    from memory.preference import preference_memory
                    prefs = await preference_memory.recall(db, user_id, top_k=5)
                    if prefs:
                        brief_parts.append("[用户偏好]\n" + "\n".join(f"- {p}" for p in prefs))
        except Exception:
            logger.warning("DB 记忆层不可用，跳过装配", exc_info=True)

        return history_text, "\n".join(brief_parts)


def _interrupt_payload(snap) -> dict | None:
    """从状态快照提取首个 interrupt 载荷。"""
    for task in snap.tasks or ():
        for intr in getattr(task, "interrupts", None) or ():
            value = getattr(intr, "value", None)
            if value is not None:
                return value
    return None
