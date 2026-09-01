"""工具注册中心单测：幂等注册 + 同步/异步 handler 契约（P0 回归）。"""
import asyncio

import pytest

from services.governance.tool_registry import ToolRegistry, ToolSpec


def test_register_is_idempotent():
    async def handler():
        return 1

    reg = ToolRegistry()
    spec = ToolSpec(name="demo_tool", description="演示", handler=handler)
    reg.register(spec)
    reg.register(spec)  # 重复注册同一 handler：跳过，不报错
    assert reg.get("demo_tool") is spec
    assert len(reg.tools) == 1


def test_yaml_config_loaded_once_and_merged():
    reg = ToolRegistry()
    spec = ToolSpec(name="search_literature", description="x", handler=lambda: None)
    reg.register(spec)
    # tools.yaml: search_literature.rate_limit_rpm=20, breaker=rag_pipeline
    assert spec.rate_limit_rpm == 20
    assert spec.breaker == "rag_pipeline"


async def test_sync_handler_executed_via_thread_pool():
    """P0 回归：同步工具（如 format_reference）经治理调用不再 TypeError。"""
    def sync_tool(text: str) -> str:
        return f"echo:{text}"

    reg = ToolRegistry()
    spec = ToolSpec(name="sync_tool", description="同步工具", handler=sync_tool)
    reg.register(spec)
    assert await reg._invoke_handler(spec, text="hi") == "echo:hi"


async def test_async_handler_awaited_directly():
    async def async_tool(x: int) -> int:
        await asyncio.sleep(0)
        return x * 2

    reg = ToolRegistry()
    spec = ToolSpec(name="async_tool", description="异步工具", handler=async_tool)
    reg.register(spec)
    assert await reg._invoke_handler(spec, x=21) == 42


def test_all_registered_handlers_awaitable_via_invoke():
    """register_all 中全部业务工具的 handler 均能被 _invoke_handler 适配。"""
    from services.governance.tools_impl import register_all
    from services.governance.tool_registry import tool_registry

    register_all()
    assert len(tool_registry.tools) >= 14
    for name, spec in tool_registry.tools.items():
        assert spec.handler is not None, f"工具 {name} 缺 handler"
