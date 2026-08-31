"""AI 运行时路由：SSE 流式对话 + interrupt 续跑（人机介入）。

- POST /api/agent/chat  → text/event-stream，事件协议见 core/streaming/hub.py
  （token / node_start / node_end / intent / route / interrupt / final / done / error）
- POST /api/agent/resume → 图在选题确认等 interrupt 点挂起后，携带用户反馈续跑
- 对话双写短期记忆（Redis），供下一轮记忆装配
"""
import asyncio
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.auth.security import get_current_user
from infrastructure.models.user import User
from services.agent.engine import AgentEngine
from services.memory.short_term import short_term_memory

logger = logging.getLogger("lunjiang.api")

router = APIRouter(prefix="/api/agent", tags=["agent"])

_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no",
                "Connection": "keep-alive"}

_PREF_MARKERS = ("记住", "以后都", "以后请", "必须", "我要求", "请用", "请勿")


def _fire(coro) -> None:
    """记忆维护类任务后台执行，不阻塞 SSE 收尾，失败仅记日志。"""
    async def runner():
        try:
            await coro
        except Exception:
            logger.warning("记忆维护任务失败", exc_info=True)
    asyncio.get_running_loop().create_task(runner())


async def _compress_window(project_id: int, session_id: str) -> None:
    from services.memory.compressor import compress_window_if_needed
    await compress_window_if_needed(project_id, session_id)


async def _learn_preference(user_id: int, content: str) -> None:
    from infrastructure.db import get_session_factory
    from services.memory.preference import preference_memory
    async with get_session_factory()() as db:
        await preference_memory.learn(db, user_id=user_id, content=content)


async def _archive_decision(user_id: int, project_id: int | None, output: str) -> None:
    """interrupt 续跑产出归档：长期决策记忆 + 项目结构化选题区。"""
    from infrastructure.db import get_session_factory
    from services.memory.long_term import long_term_memory
    async with get_session_factory()() as db:
        await long_term_memory.remember(
            db, content=output[:600], kind="decision",
            project_id=project_id, user_id=user_id, importance=0.8)
        if project_id is not None:
            from services.memory.structured import structured_memory
            title = output.strip().splitlines()[0][:120] if output.strip() else ""
            await structured_memory.update(
                db, project_id, "topic",
                {"title": title, "rationale": output[:300]})


class ChatIn(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    message: str = Field(min_length=1, max_length=8000)
    project_id: int | None = None


class ResumeIn(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    feedback: str = Field(min_length=1, max_length=4000,
                          description="用户对 interrupt 事项的反馈/确认/调整意见")
    project_id: int | None = None


def _sse(engine_gen) -> StreamingResponse:
    return StreamingResponse(engine_gen, media_type="text/event-stream",
                             headers=_SSE_HEADERS)


@router.post("/chat", dependencies=[Depends(get_current_user)])
async def chat(body: ChatIn, user: User = Depends(get_current_user)):
    pid = body.project_id or 0

    async def gen():
        engine = AgentEngine()
        try:
            await short_term_memory.append(pid, body.session_id, "user", body.message)
        except Exception:
            logger.warning("短期记忆写入失败（用户侧）", exc_info=True)

        final_text = ""
        async for ev in engine.run(session_id=body.session_id, user_input=body.message,
                                   user_id=user.id, user_role=user.role,
                                   project_id=body.project_id):
            if ev.type == "final" and isinstance(ev.payload, dict):
                final_text = ev.payload.get("output", "")
            yield ev.to_sse()

        try:
            if final_text:
                await short_term_memory.append(pid, body.session_id,
                                               "assistant", final_text)
        except Exception:
            logger.warning("短期记忆写入失败（助手侧）", exc_info=True)

        # 记忆维护：窗口压缩 + 偏好沉淀（后台）
        _fire(_compress_window(pid, body.session_id))
        if any(m in body.message for m in _PREF_MARKERS):
            _fire(_learn_preference(user.id, body.message[:300]))

    return _sse(gen())


@router.post("/resume", dependencies=[Depends(get_current_user)])
async def resume(body: ResumeIn, user: User = Depends(get_current_user)):
    """interrupt 续跑：feedback 作为 resume 值注入图（选题确认等）。"""

    async def gen():
        engine = AgentEngine()
        final_text = ""
        async for ev in engine.run(session_id=body.session_id,
                                   user_id=user.id, user_role=user.role,
                                   project_id=body.project_id, resume=body.feedback):
            if ev.type == "final" and isinstance(ev.payload, dict):
                final_text = ev.payload.get("output", "")
            yield ev.to_sse()

        try:
            if final_text:
                pid = body.project_id or 0
                await short_term_memory.append(pid, body.session_id,
                                               "assistant", final_text)
        except Exception:
            logger.warning("短期记忆写入失败（续跑侧）", exc_info=True)

        # 记忆维护：压缩触发 + 决策归档（后台）
        _fire(_compress_window(body.project_id or 0, body.session_id))
        if final_text:
            _fire(_archive_decision(user.id, body.project_id, final_text))

    return _sse(gen())
