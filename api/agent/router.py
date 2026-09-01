"""AI 运行时路由：SSE 流式对话 + interrupt 续跑（人机介入）。

- POST /api/agent/chat  → text/event-stream，事件协议见 services/streaming/hub.py
  （token / node_start / node_end / intent / route / plan / step_event /
    interrupt / final / done / error）
- POST /api/agent/resume → 图在选题确认等 interrupt 点挂起后，携带用户反馈续跑

本路由只做参数校验与 SSE 序列化；对话编排（记忆双写/压缩/偏好/归档）
统一在应用层 services/agent/conversation_service.py。
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.auth.security import get_current_user
from infrastructure.models.user import User
from services.agent.conversation_service import conversation_service

router = APIRouter(prefix="/api/agent", tags=["agent"])

_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no",
                "Connection": "keep-alive"}


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
    async def gen():
        async for ev in conversation_service.stream_chat(
                session_id=body.session_id, message=body.message,
                user_id=user.id, user_role=user.role,
                project_id=body.project_id):
            yield ev.to_sse()

    return _sse(gen())


@router.post("/resume", dependencies=[Depends(get_current_user)])
async def resume(body: ResumeIn, user: User = Depends(get_current_user)):
    async def gen():
        async for ev in conversation_service.stream_resume(
                session_id=body.session_id, feedback=body.feedback,
                user_id=user.id, user_role=user.role,
                project_id=body.project_id):
            yield ev.to_sse()

    return _sse(gen())
