"""流式输出与异步调度核心：asyncio.Queue Token 缓冲区。

解决的问题（对应简历亮点）:
- LangGraph 的 token 流（细粒度）与节点生命周期事件（粗粒度）时序错乱，
  通过统一的 EventHub 缓冲区串行化，保证前端按序渲染；
- 分层事件协议: token（字符增量）/ node_start / node_end / interrupt / done / error，
  消费端（SSE）按事件类型分层推送。
"""
import asyncio
import json
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, AsyncIterator

logger = logging.getLogger("lunjiang.stream")


@dataclass
class StreamEvent:
    type: str                    # token / node_start / node_end / intent / route / interrupt / final / done / error
    payload: Any = None
    node: str | None = None
    seq: int = 0

    def to_sse(self) -> str:
        data = {"type": self.type, "seq": self.seq,
                "node": self.node, "payload": self.payload}
        return f"data: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


class EventHub:
    """每个 Agent 会话一个 Hub；生产者（graph astream / 工具事件）写入，SSE 消费。"""

    def __init__(self, maxsize: int = 0):
        self._queue: asyncio.Queue[StreamEvent] = asyncio.Queue(maxsize=maxsize)
        self._seq = 0
        self._closed = False
        self._buffer: list[str] = []  # token 级微缓冲

    # ---------- 生产端 ----------
    async def emit(self, type: str, payload: Any = None, node: str | None = None) -> None:
        if self._closed:
            return
        self._seq += 1
        await self._queue.put(StreamEvent(type=type, payload=payload, node=node, seq=self._seq))

    async def emit_token(self, chunk: str, node: str | None = None) -> None:
        """token 微缓冲: 攒 4 个或 32 字符再入队，降低队列压力。"""
        self._buffer.append(chunk)
        joined = "".join(self._buffer)
        if len(self._buffer) >= 4 or len(joined) >= 32:
            self._buffer.clear()
            await self.emit("token", joined, node=node)

    async def flush_tokens(self, node: str | None = None) -> None:
        if self._buffer:
            await self.emit("token", "".join(self._buffer), node=node)
            self._buffer.clear()

    async def close(self) -> None:
        await self.flush_tokens()
        self._closed = True
        self._seq += 1
        await self._queue.put(StreamEvent(type="done", seq=self._seq))

    # ---------- 消费端 ----------
    async def stream(self) -> AsyncIterator[StreamEvent]:
        while True:
            ev = await self._queue.get()
            if ev.type == "done":
                yield ev
                return
            yield ev


class _NullHub:
    """无流环境兜底：节点在无 hub 上下文时事件静默丢弃，保证可独立运行/测试。"""

    async def emit(self, type: str, payload: Any = None, node: str | None = None) -> None: ...
    async def emit_token(self, chunk: str, node: str | None = None) -> None: ...
    async def flush_tokens(self, node: str | None = None) -> None: ...
    async def close(self) -> None: ...


_NULL_HUB = _NullHub()
_hub_var: ContextVar[EventHub | None] = ContextVar("lunjiang_hub", default=None)


def current_hub():
    """获取当前任务绑定的 EventHub；无绑定时返回 NullHub（事件丢弃）。"""
    return _hub_var.get() or _NULL_HUB


@contextmanager
def bind_hub(hub: EventHub):
    """在当前协程上下文中绑定 hub（同一 asyncio 任务内的节点均可见）。"""
    token = _hub_var.set(hub)
    try:
        yield hub
    finally:
        _hub_var.reset(token)
