"""上下文压缩纯逻辑单测（分级留存 / 去重 / 压缩率，离线）。"""
from types import SimpleNamespace

from services.memory.compressor import CompressResult, _dedup, _is_high_value
from services.memory.long_term import hybrid_rank


def test_high_value_detection():
    assert _is_high_value({"role": "user", "content": "记住：我要用中文写作"})
    assert _is_high_value({"role": "user", "content": "这个很重要，别改"})
    assert not _is_high_value({"role": "user", "content": "帮我查点资料"})
    assert not _is_high_value({"role": "tool", "content": "记住"})  # 工具输出默认可压


# ---------- 2026-10-05 修复：高价值误判导致 66% 正文被强制保留 ----------
# 真实语料复测（evals/eval_compression_real.py）发现：原实现全篇裸子串匹配，
# 「要求/重要/必须」是论文正文高频词 → 8 条 assistant 正文（7775 字）被判高价值，
# 压缩率 0.767 FAIL。以下四个用例锁定修复后的判定边界。

def test_high_value_only_for_user_role():
    """assistant 正文即使含纠正词也不是"用户约束"，必须可压。"""
    assert not _is_high_value(
        {"role": "assistant", "content": "本实验必须采用对照实验，要求样本量不少于30。"})
    assert not _is_high_value({"role": "tool", "content": "重要：结果已保存"})
    # 同一句话，角色不同结论不同 —— 这正是原实现缺失的维度
    text = "要求：后续都按 GB/T 7714 引用"
    assert _is_high_value({"role": "user", "content": text})
    assert not _is_high_value({"role": "assistant", "content": text})


def test_generic_marker_alone_is_not_high_value():
    """泛化词单独出现不算用户约束 —— 论文正文里「要求/重要/必须」遍地都是。"""
    assert not _is_high_value({"role": "user", "content": "这篇论文有哪些格式要求"})
    assert not _is_high_value({"role": "user", "content": "这部分是不是很重要"})
    assert not _is_high_value({"role": "user", "content": "实验必须做几次"})
    # 但显式纠正词命中即保留
    assert _is_high_value({"role": "user", "content": "这段不对"})
    assert _is_high_value({"role": "user", "content": "改成实证研究路线"})


def test_generic_marker_with_persist_action_is_high_value():
    """泛化词 + 持久化动作（记住/别改/务必）= 用户约束，必须保留。"""
    assert _is_high_value({"role": "user", "content": "这个很重要，别改"})
    assert _is_high_value({"role": "user", "content": "要求：以后都按这个风格"})
    assert _is_high_value({"role": "user", "content": "务必记住我的写作偏好"})
    assert _is_high_value({"role": "user", "content": "后续都必须带上引用编号"})


def test_high_value_rejects_empty_and_malformed():
    assert not _is_high_value({})
    assert not _is_high_value({"role": "user"})
    assert not _is_high_value({"content": "记住这件事"})   # 缺 role 不当作 user


# ---------- 2026-10-05 修复：窗口大于内容时不应截断 ----------

def test_compress_keeps_all_when_window_exceeds_messages():
    """生产默认 keep_recent=375 远超对话长度：本轮应原样保留，不该压成摘要。

    原实现无 `len(rest) > keep_recent` 判断，24 条消息的会话被逐出 21 条、
    只保留 4 条（压缩率 0.029），近期上下文被无谓丢弃。
    """
    import asyncio

    from services.memory.compressor import ContextCompressor

    msgs = [{"role": "user" if i % 2 == 0 else "assistant",
             "content": f"第{i}轮内容" + "正文" * 50} for i in range(12)]
    out = asyncio.run(ContextCompressor().compress(msgs, keep_recent=375, force=True))
    assert out.removed == [], "窗口大于消息数时不应逐出任何消息"
    assert out.summary == "", "无逐出则无需 LLM 摘要"
    assert len(out.messages) == len(msgs)
    assert out.compressed_chars == out.original_chars   # 本轮无压缩


def test_compress_truncates_when_window_is_smaller():
    """窗口小于消息数时仍按 keep_recent 截断，且近期消息保序保留。"""
    import asyncio

    from services.memory.compressor import ContextCompressor

    msgs = [{"role": "user", "content": f"第{i}轮提问内容" + "正文" * 50} for i in range(10)]
    out = asyncio.run(ContextCompressor().compress(msgs, keep_recent=3, use_llm=False,
                                                   force=True))
    assert [m["content"][:3] for m in out.messages] == ["第7轮", "第8轮", "第9轮"]
    assert len(out.removed) == 7


def test_dedup_merges_near_identical():
    msgs = [
        {"role": "user", "content": "帮我写摘要"},
        {"role": "user", "content": "帮我写摘要。"},       # 仅标点差异
        {"role": "user", "content": "换个话题"},
    ]
    out = _dedup(msgs)
    assert len(out) == 2
    assert out[0]["content"] == "帮我写摘要"


def test_compress_result_ratio():
    r = CompressResult(messages=[], original_chars=100, compressed_chars=25)
    assert r.ratio == 0.25
    empty = CompressResult(messages=[], original_chars=0, compressed_chars=0)
    assert empty.ratio == 1.0


# ---------- R13：长期记忆召回 距离×重要度 加权排序 ----------

def _item(iid: int, importance: float) -> SimpleNamespace:
    return SimpleNamespace(id=iid, importance=importance)


def test_hybrid_rank_prefers_semantically_close_when_alpha_high():
    """α=0.7 时语义距离主导：距离近但重要性低 > 距离远但重要性高。"""
    rows = [
        (_item(1, 0.1), 0.2),   # 语义最近，重要性低
        (_item(2, 0.9), 0.8),   # 语义最远，重要性高
    ]
    out = hybrid_rank(rows, alpha=0.7, top_k=2)
    assert [r.id for r in out] == [1, 2]


def test_hybrid_rank_importance_as_tiebreak():
    """距离相同（跨度归一时同分）时 importance 更高者优先。"""
    rows = [
        (_item(1, 0.9), 0.5),
        (_item(2, 0.3), 0.5),
    ]
    out = hybrid_rank(rows, alpha=0.7, top_k=1)
    assert out[0].id == 1


def test_hybrid_rank_empty_and_bad_input():
    assert hybrid_rank([], alpha=0.7, top_k=5) == []
    assert hybrid_rank([(None, 0.1), (_item(9, 0.5), "no-dist")], alpha=0.7, top_k=5) == []
