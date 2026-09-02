"""上下文压缩纯逻辑单测（分级留存 / 去重 / 压缩率，离线）。"""
from types import SimpleNamespace

from services.memory.compressor import CompressResult, _dedup, _is_high_value
from services.memory.long_term import hybrid_rank


def test_high_value_detection():
    assert _is_high_value({"role": "user", "content": "记住：我要用中文写作"})
    assert _is_high_value({"role": "user", "content": "这个很重要，别改"})
    assert not _is_high_value({"role": "user", "content": "帮我查点资料"})
    assert not _is_high_value({"role": "tool", "content": "记住"})  # 工具输出默认可压


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
