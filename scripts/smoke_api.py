"""API 端到端冒烟：登录 → SSE 对话 → interrupt 续跑。

前置: uvicorn 已在 127.0.0.1:8010 运行。
用法:
    python scripts/smoke_api.py            # chitchat 路径
    python scripts/smoke_api.py --topic    # 选题路径（触发 interrupt + resume）
"""
import asyncio
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BASE = "http://127.0.0.1:8000"
USER, PWD = "smoke_user1", "smoke_pass_123"
SESSION = "smoke-sess-0001"


async def login(client: httpx.AsyncClient) -> str:
    r = await client.post(f"{BASE}/api/auth/register",
                          json={"username": USER, "password": PWD})
    if r.status_code not in (200, 409):
        print("register:", r.status_code, r.text)
    r = await client.post(f"{BASE}/api/auth/login",
                          json={"username": USER, "password": PWD})
    r.raise_for_status()
    return r.json()["access_token"]


async def stream_sse(client: httpx.AsyncClient, token: str, path: str, body: dict) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    interrupts = []
    async with client.stream("POST", f"{BASE}{path}", json=body, headers=headers,
                             timeout=httpx.Timeout(600.0, read=600.0)) as resp:
        print("HTTP", resp.status_code)
        async for line in resp.aiter_lines():
            if not line.startswith("data: "):
                continue
            ev = json.loads(line[6:])
            t, payload = ev["type"], ev.get("payload")
            if t == "token":
                print(payload, end="", flush=True)
            elif t == "interrupt":
                interrupts.append(payload)
                print(f"\n[interrupt] agent={payload.get('agent')} "
                      f"question={payload.get('question')}")
            elif t in ("intent", "route", "final", "error", "done"):
                print(f"\n[{t}] {json.dumps(payload, ensure_ascii=False)[:300]}")
    return interrupts


async def main() -> None:
    topic_mode = "--topic" in sys.argv
    async with httpx.AsyncClient() as client:
        token = await login(client)
        print("login OK, token len:", len(token))

        if not topic_mode:
            await stream_sse(client, token, "/api/agent/chat",
                             {"session_id": SESSION, "message": "你好",
                              "project_id": None})
            return

        # 选题路径: 产出后 interrupt 等确认 → resume 携带反馈
        intr = await stream_sse(client, token, "/api/agent/chat",
                                {"session_id": SESSION,
                                 "message": "我是计算机专业的，喜欢推荐系统，帮我选题",
                                 "project_id": None})
        if not intr:
            print("\n未触发 interrupt，跳过 resume 测试")
            return
        print("\n--- resume 续跑 ---")
        await stream_sse(client, token, "/api/agent/resume",
                         {"session_id": SESSION, "feedback": "第1个方向不错，就按它来",
                          "project_id": None})


if __name__ == "__main__":
    asyncio.run(main())
