"""主从引擎冒烟测试：chitchat 直答 + 专项路由两条路径。

用法:
    python scripts/smoke_graph.py [任意用户输入]
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.platform == "win32":
    # psycopg 异步连接池需要 Selector 事件循环（Windows 默认 Proactor 不支持）
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from services.agent.engine import AgentEngine
from services.governance.tools_impl import register_all
from services.streaming.hub import StreamEvent


async def main() -> None:
    register_all()
    text = sys.argv[1] if len(sys.argv) > 1 else "你好"
    engine = AgentEngine()
    print(f"--- 用户输入: {text}")
    async for ev in engine.run(session_id="smoke-1", user_input=text,
                               user_id=1, project_id=None):
        assert isinstance(ev, StreamEvent)
        if ev.type == "token":
            print(ev.payload, end="", flush=True)
        elif ev.type == "done":
            print("\n--- [done]")
        else:
            print(f"\n--- [{ev.type}] node={ev.node} payload={ev.payload}")


if __name__ == "__main__":
    asyncio.run(main())
