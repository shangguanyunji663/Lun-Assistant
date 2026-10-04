"""LLM 统一接入层。

- 所有 provider 走 OpenAI 兼容协议，切换 configs/settings.yaml 的 llm.default_provider 即可换底座。
- 全项目统一使用 LLMProvider（openai 官方异步 SDK 直连）：
  轻量调用（意图分类/Query 改写/摘要）、流式对话、Function-Calling 循环、嵌入均走此类。
  LangGraph 图内节点同样直接使用 LLMProvider，不经过 langchain 的 ChatModel 适配层。

⚠️ 超时保护：所有 API 调用均注入 timeout（读取 llm.timeout 配置），避免 Ollama 卡顿/模型忙时
请求无限挂起，导致前端 SSE 连接"卡死"。
"""
import json
from collections.abc import Awaitable, Callable
from typing import Any, AsyncIterator, Iterable, cast
from uuid import uuid4

from openai import AsyncOpenAI

from infrastructure.config import get_embedding_dim, get_value

# 客户端缓存：按 (provider名, base_url, api_key) 复用连接池，避免每次调用重建 TCP/TLS
_client_cache: dict[tuple[str, str, str], AsyncOpenAI] = {}


def _get_client(provider_name: str, cfg: dict) -> AsyncOpenAI:
    key = (provider_name, cfg["base_url"], cfg.get("api_key") or "EMPTY")
    if key not in _client_cache:
        _client_cache[key] = AsyncOpenAI(base_url=cfg["base_url"], api_key=cfg.get("api_key") or "EMPTY")
    return _client_cache[key]


def _provider_cfg(name: str | None = None) -> tuple[str, dict]:
    cfg = get_value("llm", "providers")
    name = name or get_value("llm", "default_provider")
    if name not in cfg:
        raise ValueError(f"未知 LLM provider: {name}，可选: {list(cfg)}")
    return name, cfg[name]


def _timeout(kind: str) -> float:
    """读取 LLM 超时配置（秒）。kind: chat / chat_stream / embedding"""
    default_map = {"chat": 60, "chat_stream": 90, "embedding": 45}
    return float(get_value("llm", "timeout", kind, default=default_map.get(kind, 30)))


class LLMProvider:
    """异步轻量客户端：chat / chat_stream / embed。

    对话与嵌入可分离底座：chat 走 llm.default_provider，embed 走
    llm.embedding_provider（默认同 default_provider）。典型组合：
    本地开源对话/嵌入(ollama qwen3:4b-ctx4096 + bge-m3)，或云端对话(agnes/deepseek) + 本地嵌入(bge-m3)。
    """

    def __init__(self, provider: str | None = None):
        self.name, cfg = _provider_cfg(provider)
        self.chat_model: str = cfg["chat_model"]
        self.temperature: float = cfg.get("temperature", 0.7)
        self._client = _get_client(self.name, cfg)

        # 嵌入底座独立解析：<default|embedding_provider> 内取 embedding_model
        self.embedding_model: str = ""
        self._embed_client = None
        emb_name = get_value("llm", "embedding_provider", default=None) or self.name
        providers = get_value("llm", "providers")
        emb_cfg = providers.get(emb_name, {})
        self.embedding_model = emb_cfg.get("embedding_model") or ""
        if self.embedding_model:
            self._embed_client = _get_client(emb_name, emb_cfg)

    # ---------- 对话 ----------
    async def chat(
        self,
        messages: Iterable[dict],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
        extra: dict | None = None,
    ) -> str:
        """非流式对话，返回文本。json_mode=True 时解析并返回 JSON 对象。"""
        kwargs = self._extra()
        if extra:
            kwargs.update(extra)
        create_kw: dict = {
            "model": self.chat_model,
            "messages": list(messages),
            "temperature": temperature if temperature is not None else self.temperature,
            "timeout": _timeout("chat"),
        }
        if max_tokens is not None:
            create_kw["max_tokens"] = max_tokens
        resp = await self._client.chat.completions.create(**create_kw, **kwargs)
        text = resp.choices[0].message.content or ""
        if not text and max_tokens is not None:
            # 思考型模型（qwen3 等）可能将预算耗尽在 reasoning 上，去掉上限重试一次
            create_kw.pop("max_tokens")
            resp = await self._client.chat.completions.create(**create_kw, **kwargs)
            text = resp.choices[0].message.content or ""
        if json_mode:
            return self._extract_json(text)
        return text

    async def chat_stream(
        self,
        messages: Iterable[dict],
        *,
        temperature: float | None = None,
        extra: dict | None = None,
    ) -> AsyncIterator[str]:
        """流式对话，逐段 yield 增量文本。"""
        kwargs = self._extra()
        if extra:
            kwargs.update(extra)
        stream = await self._client.chat.completions.create(
            model=self.chat_model,
            messages=cast(Any, list(messages)),
            temperature=temperature if temperature is not None else self.temperature,
            stream=True,
            timeout=_timeout("chat_stream"),
            **kwargs,
        )
        async for chunk in cast(Any, stream):
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta

    # ---------- 向量 ----------
    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.embedding_model or self._embed_client is None:
            raise ValueError(
                f"嵌入底座 {get_value('llm', 'embedding_provider', default=self.name)} "
                f"未配置 embedding_model（见 settings.yaml llm.embedding_provider）")
        resp = await self._embed_client.embeddings.create(
            model=self.embedding_model, input=texts, timeout=_timeout("embedding"))
        vectors = [d.embedding for d in resp.data]
        if vectors:
            expected = get_embedding_dim()
            actual = len(vectors[0])
            if actual != expected:
                raise RuntimeError(
                    f"嵌入维度不一致: 底座 {self.embedding_model} 返回 {actual} 维，"
                    f"但配置/向量列期望 {expected} 维（get_embedding_dim）。"
                    "请核对 settings.yaml llm.embedding_provider 与 providers.*.embedding_dim，"
                    "维度变更需重建 memory_items 表或迁移数据")
        return vectors

    # ---------- Function Calling 循环 ----------
    async def chat_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        tool_executor,
        *,
        max_rounds: int = 3,
        temperature: float | None = None,
        on_token: Callable[[str], Awaitable[None]] | None = None,
    ) -> dict:
        """带工具调用的多轮对话（流式）。

        每一轮都以流式发起：增量文本经 on_token 逐字上报（未传则不上报），
        tool_calls 增量块在本地拼装、轮末统一执行。最终答案在生成的同时
        就逐字下发——此前整段非流式等待（生成完才返回 + 60s 总超时）是
        工具循环期间 SSE 长时间「零输出」的直接原因。

        tool_executor(name, args_json) -> Any：由调用方提供（通常接 ToolRegistry 治理栈）。
        返回 {"content": 最终文本, "tool_calls": [{name, args, result}], "rounds": int}
        """
        all_calls: list[dict] = []
        msgs = list(messages)
        for round_i in range(max_rounds):
            content, tool_deltas = await self._stream_round(
                msgs, tools, temperature, on_token)
            if not tool_deltas:
                return {"content": content, "tool_calls": all_calls,
                        "rounds": round_i + 1}
            msgs.append(_assistant_tool_msg(content, tool_deltas))
            for tc in tool_deltas:
                # 兼容缺失 function 段的分片（理论上 name 会先到，防御一下）
                if not tc["name"]:
                    continue
                name = tc["name"]
                try:
                    args = self._extract_json(tc["args"]) \
                        if tc["args"].strip().startswith("{") else {}
                    args = args if isinstance(args, dict) else {}
                except Exception:
                    args = {}
                result = await tool_executor(name, args)
                all_calls.append({"name": name, "args": args, "result": result})
                msgs.append({"role": "tool", "tool_call_id": tc["id"],
                             "content": _stringify(result)})
        # 超出轮次：不带工具流式收尾
        content, _ = await self._stream_round(msgs, None, temperature, on_token)
        return {"content": content, "tool_calls": all_calls, "rounds": max_rounds}

    async def _stream_round(
        self,
        msgs: list[dict],
        tools: list[dict] | None,
        temperature: float | None,
        on_token: Callable[[str], Awaitable[None]] | None,
    ) -> tuple[str, list[dict]]:
        """流式执行一轮对话：文本增量经 on_token 上报，tool_calls 增量拼装。

        返回 (完整文本, 工具调用列表)。工具调用形如 {"id", "name", "args"}，
        args 是尚未解析的原始 JSON 字符串——流式协议按分片下发，必须
        累积完毕后才能一次性解析。
        """
        kwargs = self._extra()
        create_kw: dict = {
            "model": self.chat_model,
            "messages": cast(Any, msgs),
            "temperature": temperature if temperature is not None else self.temperature,
            "stream": True,
            "timeout": _timeout("chat_stream"),
        }
        if tools:
            create_kw["tools"] = cast(Any, tools)
        stream = await self._client.chat.completions.create(**create_kw, **kwargs)
        parts: list[str] = []
        acc: dict[int, dict] = {}
        async for chunk in cast(Any, stream):
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            text = getattr(delta, "content", None)
            if text:
                parts.append(text)
                if on_token is not None:
                    await on_token(text)
            for tcd in (getattr(delta, "tool_calls", None) or []):
                slot = acc.setdefault(tcd.index or 0, {"id": "", "name": "", "args": ""})
                if tcd.id and not slot["id"]:
                    slot["id"] = tcd.id
                fn = getattr(tcd, "function", None)
                if fn is None:
                    continue
                if fn.name:
                    slot["name"] += fn.name
                if fn.arguments:
                    slot["args"] += fn.arguments
        tool_calls = [acc[i] for i in sorted(acc)]
        for i, tc in enumerate(tool_calls):
            if not tc["id"]:
                tc["id"] = f"call_{uuid4().hex[:8]}{i}"
        return "".join(parts), tool_calls

    # ---------- 内部 ----------
    def _extra(self) -> dict:
        """provider 特定参数：本地 ollama 关闭 qwen3 思考模式 + 限制上下文避免 OOM。"""
        if self.name == "ollama":
            return {"extra_body": {"think": False, "options": {"num_ctx": 4096}}}
        return {}

    @staticmethod
    def _extract_json(text: str):
        """容错提取 JSON：剥掉 markdown 代码块或前后缀文本。"""
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"LLM 未返回 JSON: {text[:200]}")
        return json.loads(text[start:end + 1])


def _assistant_tool_msg(content: str, tool_calls: list[dict]) -> dict:
    """流式轮次拼装出的 assistant 消息（带 tool_calls），回填对话历史用。"""
    msg: dict = {"role": "assistant", "tool_calls": [
        {"id": tc["id"], "type": "function",
         "function": {"name": tc["name"], "arguments": tc["args"]}}
        for tc in tool_calls]}
    if content:
        msg["content"] = content
    return msg


def _stringify(result) -> str:
    """工具调用结果序列化给 LLM（超长截断，避免撑爆上下文）。"""
    try:
        return json.dumps(result, ensure_ascii=False, default=str)[:3000]
    except Exception:
        return str(result)[:3000]
