"""四级上下文压缩体系：分级留存 → 冗余去重 → 窗口截断 → LLM 摘要。

目标：10+ 轮长对话的状态体积压至原始 30% 以内（可验证）。
"""
import logging
import re
from dataclasses import dataclass, field

from infrastructure.config import get_value
from services.llm.provider import LLMProvider

logger = logging.getLogger("lunjiang.memory")

# 分级留存：包含这些标记的内容视为高价值，全量保留
_HIGH_VALUE_MARKERS = ("纠正", "不对", "改成", "记住", "重要", "必须", "要求")
_TOOL_ROLES = ("tool", "function")

_SUMMARY_SYSTEM = "你是论文助手的上下文压缩器。把对话历史压缩为要点摘要，保留:任务目标、已确定的结论、用户要求与纠正、未完成事项。直接输出摘要正文，不超过300字。"


@dataclass
class CompressResult:
    messages: list[dict]                  # 压缩后的消息序列（含摘要占位）
    summary: str = ""
    original_chars: int = 0
    compressed_chars: int = 0
    removed: list[dict] = field(default_factory=list)

    @property
    def ratio(self) -> float:
        return self.compressed_chars / self.original_chars if self.original_chars else 1.0


def _is_high_value(msg: dict) -> bool:
    content = msg.get("content", "")
    if msg.get("role") in _TOOL_ROLES:
        return False  # 工具输出默认可压缩，除非带高价值标记
    return any(m in content for m in _HIGH_VALUE_MARKERS)


def _dedup(messages: list[dict]) -> list[dict]:
    """冗余去重：完全相同或仅标点差异的相邻消息合并。"""
    seen: set[str] = set()
    out: list[dict] = []
    for m in messages:
        key = re.sub(r"[\s\W_]+", "", m.get("content", ""))
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        out.append(m)
    return out


class ContextCompressor:
    def __init__(self):
        self._provider: LLMProvider | None = None

    @property
    def provider(self) -> LLMProvider:
        if self._provider is None:
            self._provider = LLMProvider()
        return self._provider

    async def compress(self, messages: list[dict], *, keep_recent: int | None = None,
                       use_llm: bool = True, force: bool = False) -> CompressResult:
        cfg_keep = int(get_value("memory", "compress_trigger_tokens", default=3000)) // 8
        keep_recent = keep_recent or max(6, cfg_keep)
        original_chars = sum(len(m.get("content", "")) for m in messages)
        result = CompressResult(messages=[], original_chars=original_chars)

        # 第0层：体积已达标则不压缩（force=True 供窗口维护调用，片段必压）
        if not force and original_chars <= int(get_value("memory", "compress_trigger_tokens", default=3000)):
            result.messages = messages
            result.compressed_chars = original_chars
            return result

        # 1. 分级留存：高价值消息全保留，其余进入候选压缩区
        high_value = [m for m in messages if _is_high_value(m)]
        rest = [m for m in messages if not _is_high_value(m)]

        # 2. 冗余去重
        rest = _dedup(rest)

        # 3. 窗口截断：rest 仅保留最近 keep_recent 条（keep_recent=0 表示整段压缩）
        if keep_recent and len(rest) > keep_recent:
            evicted = rest[:-keep_recent]
            kept_recent = rest[-keep_recent:]
        else:
            evicted = rest
            kept_recent = []

        # 4. LLM 摘要被逐出的内容
        summary = ""
        if evicted and use_llm:
            transcript = "\n".join(f"[{m.get('role')}] {m.get('content', '')[:400]}"
                                   for m in evicted[-12:])
            try:
                summary = await self.provider.chat(
                    [{"role": "system", "content": _SUMMARY_SYSTEM},
                     {"role": "user", "content": transcript}],
                    temperature=0.2, max_tokens=400,
                )
            except Exception:
                logger.exception("上下文摘要失败，退化为截断式首尾保留")
                summary = evicted[0].get("content", "")[:150] + " ……（后续已截断）"

        # 摘要放最前，随后高价值消息，最后近期窗口
        compressed: list[dict] = []
        if summary:
            compressed.append({"role": "system", "content": f"[历史摘要] {summary}"})
        compressed.extend(high_value)
        compressed.extend(kept_recent)

        result.messages = compressed
        result.summary = summary
        result.removed = evicted
        result.compressed_chars = sum(len(m.get("content", "")) for m in compressed)
        return result


context_compressor = ContextCompressor()


async def compress_window_if_needed(project_id: int, session_id: str):
    """短期记忆窗口维护（对话结束后调用）。

    体积超阈值 → 截断旧消息 → LLM 摘要 → 摘要归档长期向量记忆。
    返回 CompressResult（未触发时为 None）。
    """
    from services.memory.long_term import long_term_memory
    from services.memory.short_term import short_term_memory

    trigger = int(get_value("memory", "compress_trigger_tokens", default=3000))
    if await short_term_memory.total_chars(project_id, session_id) <= trigger:
        return None

    # 窗口截断：保留最近一半窗口，旧消息被逐出
    keep_last = max(6, int(get_value("memory", "short_term_max_turns", default=20)) // 2)
    evicted = await short_term_memory.evict_compressed(project_id, session_id,
                                                       keep_last=keep_last)
    if not evicted:
        return None

    # 分级留存+去重+LLM 摘要（被逐出消息整体压缩，keep_recent=0）
    result = await context_compressor.compress(evicted, keep_recent=0, force=True)
    if result.summary:
        try:
            from infrastructure.db import get_session_factory
            async with get_session_factory()() as db:
                await long_term_memory.remember(
                    db, content=result.summary, kind="summary",
                    project_id=project_id or None, importance=0.6,
                    meta={"session_id": session_id, "source": "window_compress"})
        except Exception:
            logger.exception("压缩摘要归档长期记忆失败")
    logger.info("窗口压缩完成: 原始%d字 → %d字 (ratio=%.2f)",
                result.original_chars, result.compressed_chars, result.ratio)
    return result
