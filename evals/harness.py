"""评测 Harness：意图分类 / RAG 检索 / 上下文压缩 三项核心指标。

指标口径:
- 意图分类: Top-1 准确率 + 分层命中占比（rule/vector/llm）
- RAG 检索: Recall@5（命中期望语料文件即算召回，对照 settings 目标 0.9）
- 上下文压缩: 压缩率（对照 settings 目标 ≤ 0.3）

评分算术抽为纯函数（score_intent / score_rag / build_compression_fixture），
离线单测见 tests/test_evals_scoring.py——不需要 PG/LLM 即可验证口径本身。

用法:
    python evals/harness.py            # 全部评测
    python evals/harness.py intent rag # 指定评测项
"""
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from infrastructure.paths import PROJECT_ROOT

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

DATASET_DIR = PROJECT_ROOT / "evals" / "datasets"


def _load(name: str) -> list[dict]:
    with open(DATASET_DIR / name, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# ---------------- 纯评分函数（离线可测） ----------------
def score_intent(predictions: list[dict], *, elapsed_s: float) -> dict:
    """意图评测口径：Top-1 命中即正确，按命中层（rule/vector/llm）分层统计。

    predictions 元素: {text, expected, got, layer}
    """
    layers: dict[str, int] = {"rule": 0, "vector": 0, "llm": 0}
    per_layer_hit: dict[str, int] = {"rule": 0, "vector": 0, "llm": 0}
    misses: list[dict] = []
    correct = 0
    for p in predictions:
        layers[p["layer"]] = layers.get(p["layer"], 0) + 1
        if p["got"] == p["expected"]:
            correct += 1
            per_layer_hit[p["layer"]] = per_layer_hit.get(p["layer"], 0) + 1
        else:
            misses.append({"text": p["text"], "expect": p["expected"],
                           "got": p["got"], "layer": p["layer"]})
    n = len(predictions)
    return {
        "suite": "intent", "cases": n, "accuracy": round(correct / n, 3),
        "avg_ms": round(elapsed_s * 1000 / n),
        "layer_distribution": layers, "layer_accuracy": per_layer_hit,
        "misses": misses,
    }


def score_rag(cases: list[dict], results_per_case: list[list[dict]], *,
              k: int, use_rewrite: bool, elapsed_s: float) -> dict:
    """检索评测口径：文件级 Recall@k——期望语料文件出现在 Top-k 结果的
    meta.file 集合里即算一次召回（不要求排第一，chunk 级排序交给 MRR，见 ab.py）。
    """
    hits = 0
    misses: list[dict] = []
    for c, results in zip(cases, results_per_case):
        files = {(r.get("meta") or {}).get("file") for r in results}
        if c["expected"] in files:
            hits += 1
        else:
            misses.append({"query": c["query"], "expect": c["expected"],
                           "got": sorted(f or "?" for f in files)})
    n = len(cases)
    return {
        "suite": f"rag@{k}", "cases": n,
        "recall": round(hits / n, 3),
        "avg_ms": round(elapsed_s * 1000 / n),
        "use_rewrite": use_rewrite, "misses": misses,
    }


def build_compression_fixture(rounds: int = 10, filler: int = 120) -> list[dict]:
    """构造合成长对话：默认 10 轮 × 约 500 字 ≈ 1 万字，确保超过压缩触发阈值
    （memory.compress_trigger_tokens，默认 3000 字），测的是压缩率而非触发逻辑。
    """
    msgs = []
    for i in range(rounds):
        msgs.append({"role": "user", "content": f"第{i}轮提问：请围绕论文选题给我建议。" + "背景填充" * filler})
        msgs.append({"role": "assistant", "content": f"第{i}轮回答：好的，建议如下。" + "内容填充" * filler})
    return msgs


# ---------------- 评测项（I/O 循环 + 委托纯函数评分） ----------------
async def eval_intent() -> dict:
    from services.classifier.intent import intent_classifier

    cases = _load("intent.jsonl")
    predictions: list[dict] = []
    t0 = time.perf_counter()
    for c in cases:
        r = await intent_classifier.classify(c["text"])
        predictions.append({"text": c["text"], "expected": c["intent"],
                            "got": r.intent, "layer": r.layer})
    return score_intent(predictions, elapsed_s=time.perf_counter() - t0)


async def eval_rag(*, use_rewrite: bool = True, k: int = 5, verbose: bool = True) -> dict:
    from services.rag.pipeline import rag_pipeline

    cases = _load("retrieval.jsonl")
    results_per_case: list[list[dict]] = []
    t0 = time.perf_counter()
    for c in cases:
        # R13: 显式传 rewrite_mode 保持评测口径（on/off），不受线上 auto 配置影响
        out = await rag_pipeline.search(c["query"], use_rewrite=True, top_k=k,
                                        rewrite_mode=("on" if use_rewrite else "off"))
        results_per_case.append(out["results"])
    report = score_rag(cases, results_per_case, k=k, use_rewrite=use_rewrite,
                       elapsed_s=time.perf_counter() - t0)
    if verbose:
        miss_by_query = {m["query"]: m["got"] for m in report["misses"]}
        for c in cases:
            mark = "MISS" if c["query"] in miss_by_query else "HIT "
            print(f"    [{mark}] {c['query']} → {c['expected']}")
    return report


async def eval_compression() -> dict:
    from services.memory.compressor import context_compressor

    result = await context_compressor.compress(build_compression_fixture(),
                                               keep_recent=4, force=True)
    return {
        "suite": "compression", "original_chars": result.original_chars,
        "compressed_chars": result.compressed_chars,
        "ratio": round(result.ratio, 3),
        "target_ratio": 0.3, "pass": result.ratio <= 0.3,
    }


# ---------------- 汇总 ----------------
async def main(suites: list[str]) -> None:
    from infrastructure.config import get_value
    target_recall = float(get_value("rag", "recall_target_at5", default=0.9))

    results = {}
    if "intent" in suites:
        print("== 意图分类评测 ==")
        results["intent"] = r = await eval_intent()
        print(f"    准确率: {r['accuracy']:.1%} ({r['cases']}条, 平均{r['avg_ms']}ms/条)")
        print(f"    分层分布: {r['layer_distribution']}  分层命中: {r['layer_accuracy']}")
        for m in r["misses"]:
            print(f"    MISS: {m['text'][:20]}... expect={m['expect']} got={m['got']}")

    if "rag" in suites:
        print("== RAG 检索评测 (Recall@5, rewrite=on) ==")
        results["rag"] = r = await eval_rag(use_rewrite=True)
        print(f"    Recall@5: {r['recall']:.1%} (目标 {target_recall:.0%}, "
              f"平均{r['avg_ms']}ms/条)")
        for m in r["misses"]:
            print(f"    MISS: {m['query']} → {m['expect']} got={m['got']}")

    if "compression" in suites:
        print("== 上下文压缩评测 ==")
        results["compression"] = r = await eval_compression()
        print(f"    {r['original_chars']} 字 → {r['compressed_chars']} 字 "
              f"(ratio={r['ratio']}, 目标≤{r['target_ratio']}, {'PASS' if r['pass'] else 'FAIL'})")

    out_path = DATASET_DIR.parent / "results_latest.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已写入 {out_path}")


if __name__ == "__main__":
    suites = [a for a in sys.argv[1:] if a in {"intent", "rag", "compression"}] \
        or ["intent", "rag", "compression"]
    asyncio.run(main(suites))
