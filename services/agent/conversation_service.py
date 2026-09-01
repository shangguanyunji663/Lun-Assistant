"""应用层：一轮对话的完整编排（路由层只做协议适配，不承载业务规则）。

职责（自 api/agent/router.py 下沉）：
- 对话前后双写短期记忆（用户输入前置 / 助手终稿收尾）；
- 会话收尾的记忆维护：窗口压缩（后台）、偏好沉淀（关键词触发）、
  interrupt 续跑后的决策归档（长期记忆 + 项目结构化选题区）；
- 事件流直接透传 AgentEngine.run 的 StreamEvent，不做加工。
"""
import asyncio
import logging

from services.agent.engine import AgentEngine
from services.memory.compressor import compress_window_if_needed
from services.memory.long_term import long_term_memory
from services.memory.preference import preference_memory
from services.memory.short_term import short_term_memory
from services.memory.structured import structured_memory
from services.streaming.hub import StreamEvent

logger = logging.getLogger("lunjiang.conversation")

# 偏好沉淀触发词：命中任一即视为用户在表达长期写作偏好
PREFERENCE_MARKERS = ("记住", "以后都", "以后请", "必须", "我要求", "请用", "请勿")

_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no",
                "Connection": "keep-alive"}


def _fire(coro) -> None:
    """记忆维护类任务后台执行，不阻塞 SSE 收尾，失败仅记日志。"""
    async def runner():
        try:
            await coro
        except Exception:
            logger.warning("记忆维护任务失败", exc_info=True)
    asyncio.get_running_loop().create_task(runner())


async def _compress_window(project_id: int, session_id: str) -> None:
    await compress_window_if_needed(project_id, session_id)


async def _learn_preference(user_id: int, content: str) -> None:
    from infrastructure.db import get_session_factory
    async with get_session_factory()() as db:
        await preference_memory.learn(db, user_id=user_id, content=content)


async def _archive_decision(user_id: int, project_id: int | None, output: str) -> None:
    """interrupt 续跑产出归档：长期决策记忆 + 项目结构化选题区。"""
    from infrastructure.db import get_session_factory
    async with get_session_factory()() as db:
        await long_term_memory.remember(
            db, content=output[:600], kind="decision",
            project_id=project_id, user_id=user_id, importance=0.8)
        if project_id is not None:
            title = output.strip().splitlines()[0][:120] if output.strip() else ""
            await structured_memory.update(
                db, project_id, "topic",
                {"title": title, "rationale": output[:300]})


class ConversationService:
    """单例无状态服务：编排一轮对话（chat / resume）。"""

    async def stream_chat(
        self, *, session_id: str, message: str,
        user_id: int, user_role: str, project_id: int | None,
    ):
        """发起一轮对话：事件流透传 + 会话记忆维护。"""
        pid = project_id or 0
        engine = AgentEngine()
        try:
            await short_term_memory.append(pid, session_id, "user", message)
        except Exception:
            logger.warning("短期记忆写入失败（用户侧）", exc_info=True)

        final_text = ""
        async for ev in engine.run(session_id=session_id, user_input=message,
                                   user_id=user_id, user_role=user_role,
                                   project_id=project_id):
            if ev.type == "final" and isinstance(ev.payload, dict):
                final_text = ev.payload.get("output", "")
            yield ev

        try:
            if final_text:
                await short_term_memory.append(pid, session_id,
                                               "assistant", final_text)
        except Exception:
            logger.warning("短期记忆写入失败（助手侧）", exc_info=True)

        # 记忆维护：窗口压缩 + 偏好沉淀（后台）
        _fire(_compress_window(pid, session_id))
        if any(m in message for m in PREFERENCE_MARKERS):
            _fire(_learn_preference(user_id, message[:300]))

    async def stream_resume(
        self, *, session_id: str, feedback: str,
        user_id: int, user_role: str, project_id: int | None,
    ):
        """interrupt 续跑：feedback 作为 resume 值注入图（选题确认等）。"""
        engine = AgentEngine()
        final_text = ""
        async for ev in engine.run(session_id=session_id,
                                   user_id=user_id, user_role=user_role,
                                   project_id=project_id, resume=feedback):
            if ev.type == "final" and isinstance(ev.payload, dict):
                final_text = ev.payload.get("output", "")
            yield ev

        try:
            if final_text:
                pid = project_id or 0
                await short_term_memory.append(pid, session_id,
                                               "assistant", final_text)
        except Exception:
            logger.warning("短期记忆写入失败（续跑侧）", exc_info=True)

        # 记忆维护：压缩触发 + 决策归档（后台）
        _fire(_compress_window(project_id or 0, session_id))
        if final_text:
            _fire(_archive_decision(user_id, project_id, final_text))


conversation_service = ConversationService()
