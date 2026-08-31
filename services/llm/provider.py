"""LLM 统一接入层。

- 所有 provider 走 OpenAI 兼容协议，切换 configs/settings.yaml 的 llm.default_provider 即可换底座。
- 提供两类入口：
  1. LLMProvider: 轻量异步客户端（意图分类/Query改写/摘要等工具型调用）
  2. get_chat_model: langchain-openai 的 ChatOpenAI（LangGraph 图内节点使用）
"""
import json
from typing import AsyncIterator, Iterable

from openai import AsyncOpenAI

from infrastructure.config import get_value

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


class LLMProvider:
    """异步轻量客户端：chat / chat_stream / embed。"""

    def __init__(self, provider: str | None = None):
        self.name, cfg = _provider_cfg(provider)
        self.chat_model: str = cfg["chat_model"]
        self.embedding_model: str = cfg.get("embedding_model") or ""
        self.temperature: float = cfg.get("temperature", 0.7)
        self._client = _get_client(self.name, cfg)

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
            messages=list(messages),
            temperature=temperature if temperature is not None else self.temperature,
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta

    # ---------- 向量 ----------
    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.embedding_model:
            raise ValueError(f"provider {self.name} 未配置 embedding_model")
        resp = await self._client.embeddings.create(model=self.embedding_model, input=texts)
        return [d.embedding for d in resp.data]

    # ---------- Function Calling 循环 ----------
    async def chat_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        tool_executor,
        *,
        max_rounds: int = 3,
        temperature: float | None = None,
    ) -> dict:
        """带工具调用的多轮对话。

        tool_executor(name, args_json) -> Any：由调用方提供（通常接 ToolRegistry 治理栈）。
        返回 {"content": 最终文本, "tool_calls": [{name, args, result}], "rounds": int}
        """
        all_calls: list[dict] = []
        msgs = list(messages)
        for round_i in range(max_rounds):
            kwargs = self._extra()
            resp = await self._client.chat.completions.create(
                model=self.chat_model, messages=msgs, tools=tools,
                temperature=temperature if temperature is not None else self.temperature,
                **kwargs,
            )
            msg = resp.choices[0].message
            if not msg.tool_calls:
                return {"content": msg.content or "", "tool_calls": all_calls,
                        "rounds": round_i + 1}
            msgs.append(msg.model_dump(exclude_none=True))
            for tc in msg.tool_calls:
                name = tc.function.name
                try:
                    args = self._extract_json(tc.function.arguments) \
                        if tc.function.arguments.strip().startswith("{") else {}
                    args = args if isinstance(args, dict) else {}
                except Exception:
                    args = {}
                result = await tool_executor(name, args)
                all_calls.append({"name": name, "args": args, "result": result})
                msgs.append({"role": "tool", "tool_call_id": tc.id,
                             "content": _stringify(result)})
        # 超出轮次：不带工具再收尾一次
        final = await self.chat(msgs, temperature=temperature, max_tokens=1500)
        return {"content": final, "tool_calls": all_calls, "rounds": max_rounds}

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


def get_chat_model(temperature: float | None = None, streaming: bool = False):
    """LangGraph 节点用的 ChatOpenAI 实例。"""
    from langchain_openai import ChatOpenAI

    name, cfg = _provider_cfg()
    kwargs = dict(
        model=cfg["chat_model"],
        base_url=cfg["base_url"],
        api_key=cfg.get("api_key") or "EMPTY",
        temperature=temperature if temperature is not None else cfg.get("temperature", 0.7),
        streaming=streaming,
    )
    if name == "ollama":
        kwargs["model_kwargs"] = {"think": False, "options": {"num_ctx": 4096}}
    return ChatOpenAI(**kwargs)


def _stringify(result) -> str:
    import json
    try:
        return json.dumps(result, ensure_ascii=False, default=str)[:3000]
    except Exception:
        return str(result)[:3000]
