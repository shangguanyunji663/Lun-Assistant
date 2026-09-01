"""Query 改写规则层单测（jieba 本地，不调 LLM）。"""
from services.rag.query_rewrite import _rule_keywords, _rule_rewrite, _clean_keywords


def test_rule_rewrite_scene_prefix():
    out = _rule_rewrite("开题报告怎么写")
    assert out["strategy"] == "rule"
    assert out["rewritten"].startswith("开题报告")


def test_rule_rewrite_synonym_expansion():
    out = _rule_rewrite("大模型微调方法")
    assert "LLM" in out["rewritten"] or "fine-tuning" in out["rewritten"]


def test_rule_rewrite_plain_query_untouched():
    out = _rule_rewrite("机器学习")
    assert out["rewritten"] == "机器学习"


def test_rule_keywords_extracts_terms():
    kws = _rule_keywords("帮我检索大模型注意力机制的相关文献")
    assert 1 <= len(kws) <= 6


def test_clean_keywords_dedup_and_limit():
    out = _clean_keywords(["大模型", "大模型", "  RAG  ", "RAG", "x" * 40, "微调"], "q")
    assert out.count("大模型") == 1
    assert all(len(k) <= 32 for k in out)
    assert len(out) <= 6
