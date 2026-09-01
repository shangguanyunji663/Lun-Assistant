"""上下文压缩纯逻辑单测（分级留存 / 去重 / 压缩率，离线）。"""
from services.memory.compressor import CompressResult, _dedup, _is_high_value


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
