"""四级上下文压缩体系：分级留存 → 冗余去重 → 窗口截断 → LLM 摘要。

目标：10+ 轮长对话的状态体积压至原始 30% 以内（可验证）。
"""
import logging
import re
from dataclasses import dataclass, field

from infrastructure.config import get_value
from infrastructure.db import get_session_factory
from services.llm.provider import LLMProvider
from services.memory.long_term import long_term_memory
from services.memory.short_term import short_term_memory

logger = logging.getLogger("lunjiang.memory")

# 分级留存：纠正类词表 —— **仅在用户消息中**判定，且分为三档严密程度。
#
# 为什么改成这样（2026-10-05 审计修复）：
#   原实现是 `any(m in content for m in ("纠正","不对","改成","记住","重要","必须","要求"))`
#   的**全篇裸子串匹配**，而「要求 / 重要 / 必须」是中文论文正文的高频词。
#   用真实语料 fixture 复测（evals/eval_compression_real.py）暴露：
#     高价值消息 11/24 条、7903 字 = 占全文 66.2%，全部强制保留、永不压缩；
#     其中 8 条（7775 字）是 assistant 正文因含「要求/重要/必须」被**误判**，
#     真实用户纠正只有 3 条（284 字）。
#   → 压缩率从结构上不可能达到 0.3（实测 0.767 FAIL）。
#   合成 fixture 用「背景填充」重复文本，一个标记词都不含，恰好绕过了该瓶颈。
#
# 新判定规则（三档，从严到宽）：
#   1. 非 user 角色 → 一律可压（assistant 正文不是"用户纠正"）；
#   2. 显式纠正词（纠正/不对/改成/改为）→ 命中即高价值；
#   3. 泛化词（重要/必须/要求/记住）单独命中**不算**，必须与"持久化动作"同现
#      （如「这个很重要，别改」），避免把论文正文里的普通用词判成用户约束。
_CORRECTION_MARKERS = ("纠正", "不对", "改成", "改为")
_GENERIC_MARKERS = ("重要", "必须", "要求", "记住")
_PERSIST_MARKERS = ("别改", "不要改", "别忘", "务必", "一定", "以后都", "后续都")
# 「记住/别忘」的常见变体（"别改了" 也属持久化动作）
_PERSIST_PATTERN = re.compile(r"别[改忘]|不要改|记(住|好)|务必|一定")

# 向后兼容：旧名保留为三档词表的并集，供诊断脚本枚举用
_HIGH_VALUE_MARKERS = _CORRECTION_MARKERS + _GENERIC_MARKERS

_SUMMARY_SYSTEM = "你是论文助手的上下文压缩器。把对话历史压缩为要点摘要，保留:任务目标、已确定的结论、用户要求与纠正、未完成事项。直接输出摘要正文，不超过300字。"

# 摘要硬上限：max_tokens 限制不到中文（1 token 可能落成 1 个汉字甚至更多），
# 故再按字符数硬截断 —— 让压缩率只由 keep_recent 与内容决定，不随模型漂移。
_SUMMARY_MAX_CHARS = 300
_SUMMARY_MAX_TOKENS = 400


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
    """判断消息是否承载"用户约束/纠正"，必须全量保留。

    三档判定见上方 `_CORRECTION_MARKERS` 注释。核心变化：**只有用户消息**才可能
    是高价值约束；assistant 正文即使含「要求/重要/必须」也可正常压缩。
    """
    if msg.get("role") != "user":
        return False          # assistant / tool 输出默认可压缩
    content = msg.get("content", "")
    if any(m in content for m in _CORRECTION_MARKERS):
        return True           # 显式纠正：命中即保留
    # 泛化词需与"持久化动作"同现，避免误判论文正文里的普通用词
    has_generic = any(m in content for m in _GENERIC_MARKERS)
    has_persist = any(m in content for m in _PERSIST_MARKERS) \
        or bool(_PERSIST_PATTERN.search(content))
    return has_generic and has_persist


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
        # 必须用 `is None` 而非 `or`（2026-10-05 修复）：
        #   生产路径 compress_window_if_needed 传 keep_recent=0，语义是"被逐出消息整体压缩"。
        #   原先写作 `keep_recent or max(6, cfg_keep)`，0 是 falsy → 被静默替换成 375，
        #   生产意图"整段压缩"被改写为"保留最近 375 条"，压缩路径实际上从未压缩。
        if keep_recent is None:
            keep_recent = max(6, cfg_keep)
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

        # 3. 窗口截断：rest 仅保留最近 keep_recent 条。
        #
        # keep_recent 语义（三者互斥，2026-10-05 修正）：
        #   keep_recent is None → 未指定，取配置默认 max(6, 触发阈值//8)（已在上方归一）
        #   keep_recent == 0    → **整段压缩**，全部逐出交给 LLM 摘要（生产路径用它）
        #   keep_recent > 0     → 保留最近 N 条，其余逐出
        #
        # 原实现是 `if keep_recent and len(rest) > keep_recent:` —— 0 为 falsy，
        # 于是"整段压缩"被解释成"全部保留（不压缩）"，加上上方 `or` 的二次改写，
        # 导致生产压缩链路实际从未压缩过（实测 ratio=1.0、摘要 0 字）。
        # 同时 len(rest) > keep_recent 这个条件也不可少：窗口大于内容时应原样保留，
        # 而非把整段对话压成摘要（生产默认 375 远超 24 条消息的会话）。
        if keep_recent == 0:
            evicted, kept_recent = rest, []
        elif len(rest) > keep_recent:
            evicted, kept_recent = rest[:-keep_recent], rest[-keep_recent:]
        else:
            evicted, kept_recent = [], rest

        # 4. LLM 摘要被逐出的内容
        summary = ""
        if evicted and use_llm:
            transcript = "\n".join(f"[{m.get('role')}] {m.get('content', '')[:400]}"
                                   for m in evicted[-12:])
            try:
                summary = await self.provider.chat(
                    [{"role": "system", "content": _SUMMARY_SYSTEM},
                     {"role": "user", "content": transcript}],
                    temperature=0.2, max_tokens=_SUMMARY_MAX_TOKENS,
                )
            except Exception:
                logger.exception("上下文摘要失败，退化为截断式首尾保留")
                summary = evicted[0].get("content", "")[:150] + " ……（后续已截断）"
            # 硬上限：提示词里的「不超过300字」是软约束，实测会超（19:12 那轮 400 字）。
            # 不加硬截断则压缩率随模型状态漂移，指标不可复现。
            summary = summary.strip()[:_SUMMARY_MAX_CHARS]

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
