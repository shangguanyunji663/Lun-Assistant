"""三级容错机制：指数退避重试 → 默认参数降级 → 人机交互兜底。

resilient_call() 依次执行:
1. 原参数 + 指数退避重试（带抖动）
2. 若提供 fallback_args，则以默认安全参数再试一轮（重试逻辑同上）
3. 仍失败 → 抛 HumanInterventionRequired，由上层 Agent 图转为 interrupt 人机介入

⚠️ 安全网：每次 attempt 都套 asyncio.wait_for 总超时天花板，
即使底层工具/API 遗漏了 timeout 配置也不会永久挂起。
"""
import asyncio
import logging
import random
from typing import Any, Callable, Coroutine

from infrastructure.config import get_value

logger = logging.getLogger("lunjiang.governance")


class HumanInterventionRequired(Exception):
    """三级容错耗尽，需要人工介入。"""

    def __init__(self, tool: str, last_error: Exception):
        self.tool = tool
        self.last_error = last_error
        super().__init__(f"工具 {tool} 多级容错后仍失败，需人工介入: {last_error}")


def _per_call_timeout() -> float:
    """单次工具调用超时天花板（秒）：覆盖 LLM 多轮 + 向量检索 + 精排的合计时间。"""
    return float(get_value("governance", "retry", "per_call_timeout_s", default=120))


async def resilient_call(
    fn: Callable[..., Coroutine[Any, Any, Any]],
    *args: Any,
    tool_name: str | None = None,
    fallback_args: tuple | None = None,
    fallback_kwargs: dict | None = None,
    max_attempts: int | None = None,
    base_delay: float | None = None,
    max_delay: float | None = None,
    **kwargs: Any,
) -> Any:
    fn_name = getattr(fn, "__name__", "unknown")
    assert isinstance(fn_name, str), "可调用对象 __name__ 应为字符串"
    tool_name = tool_name or fn_name
    cfg_max = int(get_value("governance", "retry", "max_attempts", default=3))
    cfg_base = float(get_value("governance", "retry", "base_delay", default=0.5))
    cfg_top = float(get_value("governance", "retry", "max_delay", default=8.0))
    max_attempts = max_attempts or cfg_max
    base_delay = base_delay if base_delay is not None else cfg_base
    max_delay = max_delay if max_delay is not None else cfg_top
    call_timeout = _per_call_timeout()

    last_error: Exception | None = None

    async def attempt(a: tuple, kw: dict) -> Any:
        nonlocal last_error
        for i in range(max_attempts):
            try:
                return await asyncio.wait_for(fn(*a, **kw), timeout=call_timeout)
            except asyncio.TimeoutError as e:
                last_error = TimeoutError(f"{tool_name} 单次调用超过 {call_timeout}s 天花板")
                logger.warning("[retry] %s 第%d次超时(>%ds)，%.2fs 后重试",
                               tool_name, i + 1, call_timeout,
                               min(max_delay, base_delay * (2 ** i)) * (0.5 + random.random()))
            except Exception as e:
                last_error = e
                if i == max_attempts - 1:
                    break
                delay = min(max_delay, base_delay * (2 ** i)) * (0.5 + random.random())
                logger.warning("[retry] %s 第%d次失败: %s，%.2fs 后重试", tool_name, i + 1, e, delay)
                await asyncio.sleep(delay)
        raise last_error  # type: ignore[misc]

    # 第一级：原参数重试
    try:
        return await attempt(args, kwargs)
    except Exception:
        pass

    # 第二级：默认参数降级
    if fallback_args is not None or fallback_kwargs is not None:
        logger.warning("[fallback] %s 降级为默认参数重试", tool_name)
        try:
            return await attempt(fallback_args if fallback_args is not None else args,
                                 fallback_kwargs if fallback_kwargs is not None else {})
        except Exception:
            pass

    # 第三级：人机兜底
    raise HumanInterventionRequired(tool_name, last_error or RuntimeError("unknown"))
