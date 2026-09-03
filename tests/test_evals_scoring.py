"""评测 Harness 纯评分函数单测 + 数据集完整性校验（离线，不触 PG/LLM）。

harness.py 的评分算术抽为纯函数后，指标口径本身（而不只是"能跑通"）可以被回归：
- score_intent / score_rag / build_compression_fixture 的算术与边界；
- 数据集口径锁定：intent 22 条与文档一致、检索集 expected 文件真实存在于语料库，
  防止"评测集悄悄腐烂"（改了语料文件名但没人发现 Recall 虚降）。
"""
from evals.harness import _load, build_compression_fixture, score_intent, score_rag

# ---------------- score_intent：Top-1 准确率 + 分层统计 ----------------

def test_score_intent_accuracy_layers_and_misses():
    predictions = [
        {"text": "a", "expected": "literature_search", "got": "literature_search", "layer": "rule"},
        {"text": "b", "expected": "writing", "got": "writing", "layer": "rule"},
        {"text": "c", "expected": "writing", "got": "chitchat", "layer": "vector"},
        {"text": "d", "expected": "topic_analysis", "got": "chitchat", "layer": "llm"},
    ]
    r = score_intent(predictions, elapsed_s=0.2)
    assert r["suite"] == "intent" and r["cases"] == 4
    assert r["accuracy"] == 0.5                     # 2/4
    assert r["avg_ms"] == 50                        # 200ms / 4 条
    assert r["layer_distribution"] == {"rule": 2, "vector": 1, "llm": 1}
    assert r["layer_accuracy"] == {"rule": 2, "vector": 0, "llm": 0}
    assert r["misses"] == [
        {"text": "c", "expect": "writing", "got": "chitchat", "layer": "vector"},
        {"text": "d", "expect": "topic_analysis", "got": "chitchat", "layer": "llm"},
    ]


def test_score_intent_rounds_to_three_decimals():
    predictions = [{"text": "x", "expected": "writing", "got": "writing", "layer": "rule"},
                   {"text": "y", "expected": "writing", "got": "chitchat", "layer": "rule"},
                   {"text": "z", "expected": "writing", "got": "writing", "layer": "rule"}]
    assert score_intent(predictions, elapsed_s=0.0)["accuracy"] == 0.667  # 2/3


# ---------------- score_rag：文件级 Recall@k ----------------

def test_score_rag_file_level_recall():
    cases = [
        {"query": "q1", "expected": "a.txt"},
        {"query": "q2", "expected": "b.txt"},
    ]
    results = [
        # q1：期望文件出现在 Top5 的 meta.file 集合（不在第一位也算召回）
        [{"meta": {"file": "x.txt"}}, {"meta": {"file": "a.txt"}}],
        # q2：Top5 里没有期望文件 → MISS
        [{"meta": {"file": "y.txt"}}, {"meta": None}],
    ]
    r = score_rag(cases, results, k=5, use_rewrite=True, elapsed_s=0.4)
    assert r["suite"] == "rag@5" and r["cases"] == 2
    assert r["recall"] == 0.5
    assert r["avg_ms"] == 200
    assert r["use_rewrite"] is True
    assert r["misses"] == [{"query": "q2", "expect": "b.txt", "got": ["?", "y.txt"]}]


def test_score_rag_treats_missing_meta_as_unknown_file():
    # meta 缺失或非 dict 时按"?"归一，不抛异常；去重发生在归一化前（同值折叠）
    cases = [{"query": "q", "expected": "a.txt"}]
    results = [[{"meta": None}, {}, {"meta": {"other": 1}}]]
    r = score_rag(cases, results, k=3, use_rewrite=False, elapsed_s=0.1)
    assert r["misses"][0]["got"] == ["?"]
    assert r["suite"] == "rag@3" and r["use_rewrite"] is False


# ---------------- build_compression_fixture：超过压缩触发阈值的合成对话 ----------------

def test_build_compression_fixture_exceeds_trigger_threshold():
    from infrastructure.config import get_value
    threshold = int(get_value("memory", "compress_trigger_tokens", default=3000))
    msgs = build_compression_fixture()
    assert len(msgs) == 20                                   # 10 轮 × user/assistant
    assert [m["role"] for m in msgs[:2]] == ["user", "assistant"]
    assert sum(len(m["content"]) for m in msgs) > threshold  # 确保触发的是压缩而非静默返回


# ---------------- _load：JSONL 解析 ----------------

def test_load_parses_jsonl_skipping_blank_lines(tmp_path, monkeypatch):
    ds = tmp_path / "mini.jsonl"
    ds.write_text('{"a": 1}\n\n{"a": 2}\n', encoding="utf-8")
    monkeypatch.setattr("evals.harness.DATASET_DIR", tmp_path)
    assert _load("mini.jsonl") == [{"a": 1}, {"a": 2}]


# ---------------- 数据集完整性：口径锁定，防评测集腐烂 ----------------

def _read_jsonl(name):
    return _load(name)


def test_intent_dataset_matches_documented_scope():
    from services.classifier.intent import INTENTS
    cases = _read_jsonl("intent.jsonl")
    # 学习指南 0.3 / 14.1 与 README 均按"22 条"口径宣传，改动需三处同步
    assert len(cases) == 22
    for c in cases:
        assert c["text"].strip() and c["intent"] in INTENTS


def test_retrieval_datasets_expect_existing_corpus_files():
    import infrastructure.paths as paths
    corpus = paths.PROJECT_ROOT / "data" / "corpus"
    # (数据集, 文档承诺的条数)：常规集 8 条见第 14 课；两个困难集为 ab.py 实验组
    # （paper_hard 26 条，25/26 命中 = 96.2%，即文档记录的 Recall@5）
    for name, documented in [("retrieval.jsonl", 8), ("retrieval_hard.jsonl", 8),
                             ("retrieval_paper_hard.jsonl", 26)]:
        cases = _read_jsonl(name)
        assert len(cases) == documented, f"{name} 条数与文档口径不一致"
        for c in cases:
            assert c["query"].strip()
            assert (corpus / c["expected"]).is_file(), \
                f"{name} 期望文件不在语料库: {c['expected']}（评测会静默虚降）"
