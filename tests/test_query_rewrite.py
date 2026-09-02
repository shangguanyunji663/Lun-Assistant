"""Query 改写规则层单测（jieba 本地，不调 LLM）。"""
from services.rag.query_rewrite import (
    _clean_keywords,
    _rule_keywords,
    _rule_rewrite,
    is_rewrite_worthwhile,
)


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


# ---------- R13：按难度自适应（is_rewrite_worthwhile） ----------

def test_hard_colloquial_queries_need_rewrite():
    """长尾口语化查询（retrieval_hard.jsonl 特征）应判定为值得 LLM 改写。"""
    hard = [
        "综述部分总被导师说像流水账一样罗列怎么破",
        "开题答辩被老师质疑创新点站不住脚该怎么提前准备",
        "论文里那段话跟网上找到的太像了怕过不了",
        "快答辩了心里没底想提前演练一下老师会问什么",
        "导师嫌我实验单薄让我补充实验增强说服力",
        "我的助手两路检索结果乱七八糟怎么合并排序",
        "聊天窗口关了再开它就忘了我说过的写作要求",
        "怎么让程序自动管住智能体别乱调外部接口",
    ]
    assert all(is_rewrite_worthwhile(q) for q in hard)


def test_simple_queries_skip_rewrite():
    """简单术语查询（retrieval.jsonl 特征）应判定为无需 LLM 改写（规则关键词兜底）。"""
    simple = [
        "如何写好文献综述",
        "开题报告有哪些常见问题",
        "混合检索为什么用RRF融合",
        "查重降重的合规做法",
        "答辩怎么准备问答环节",
    ]
    assert all(not is_rewrite_worthwhile(q) for q in simple)


def test_empty_query_not_worthwhile():
    assert is_rewrite_worthwhile("") is False
    assert is_rewrite_worthwhile("   ") is False
