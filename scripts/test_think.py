"""验证 qwen3 思考模式关闭的三种方式，选定 provider 的最终策略。"""
import asyncio
import time

from openai import AsyncOpenAI

BASE = "http://127.0.0.1:11434/v1"
MODEL = "qwen3:4b"


async def trial(name: str, **kwargs) -> None:
    client = AsyncOpenAI(base_url=BASE, api_key="x")
    msgs = [{"role": "user", "content": "只回复: OK"}]
    if kwargs.pop("no_think_prompt", False):
        msgs[0]["content"] += " /no_think"
    t0 = time.perf_counter()
    r = await client.chat.completions.create(model=MODEL, messages=msgs,
                                             max_tokens=200, **kwargs)
    dt = time.perf_counter() - t0
    print(f"--- {name} ({dt:.1f}s) ---")
    print(repr((r.choices[0].message.content or "")[:120]))
    extra = getattr(r.choices[0].message, "reasoning_content", None) or getattr(
        r.choices[0].message, "reasoning", None)
    if extra:
        print(f"[reasoning field]: {str(extra)[:80]!r}")


async def main() -> None:
    await trial("A: 默认（无控制）")
    await trial("B: extra_body think=false", extra_body={"think": False})
    await trial("C: /no_think 提示词", no_think_prompt=True)
    await trial("D: extra_body think=false + /no_think", extra_body={"think": False},
                no_think_prompt=True)


asyncio.run(main())
