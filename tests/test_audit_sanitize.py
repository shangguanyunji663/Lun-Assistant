"""审计 detail 净化单测（R13 合规硬约束：超 200 字符截断 + 哈希指纹 + 摘要）。

sanitize_detail 为纯函数（含配置后备默认 200），全离线可跑。
"""
from infrastructure.audit import _sanitize_value, sanitize_detail


def test_short_value_passthrough():
    out = sanitize_detail({"ok": True, "status": 200, "msg": "hello"})
    assert out == {"ok": True, "status": 200, "msg": "hello"}


def test_long_string_truncated_to_fingerprint_summary():
    long_text = "长" * 5000
    out = sanitize_detail({"args": {"text": long_text}})
    boxed = out["args"]["text"]
    assert set(boxed.keys()) == {"fp", "sum", "len"}
    assert boxed["len"] == 5000
    assert len(boxed["sum"]) == 200
    assert len(boxed["fp"]) == 16  # sha256 前 16 位


def test_fingerprint_reproducible():
    text = "x" * 300
    a = sanitize_detail({"t": text})["t"]
    b = sanitize_detail({"t": text})["t"]
    # 相同原文指纹可复现（人工审计对账能力）
    from hashlib import sha256
    assert a["fp"] == sha256(text.encode()).hexdigest()[:16] == b["fp"]


def test_nested_list_resursive():
    out = sanitize_detail({"batch": ["s" * 300, "short", {"deep": "d" * 201}]})
    assert set(out["batch"][0].keys()) == {"fp", "sum", "len"}
    assert out["batch"][1] == "short"
    assert set(out["batch"][2]["deep"].keys()) == {"fp", "sum", "len"}


def test_none_and_non_str_intact():
    assert sanitize_detail(None) is None
    out = _sanitize_value({"n": 1.5, "b": False, "none": None}, 200)
    assert out == {"n": 1.5, "b": False, "none": None}