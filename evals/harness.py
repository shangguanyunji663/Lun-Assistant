"""评测 Harness：意图分类 / RAG 检索 / 上下文压缩 三项核心指标。

指标口径:
- 意图分类: Top-1 准确率 + 分层命中占比（rule/vector/llm）
- RAG 检索: Recall@5（命中期望语料文件即算召回，对照 settings 目标 0.9）
- 上下文压缩: 压缩率（对照 settings 目标 ≤ 0.3）

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


# ---------------- 意图分类 ----------------
async def eval_intent() -> dict:
    from services.classifier.intent import intent_classifier

    cases = _load("intent.jsonl")
    correct, layers, per_layer_hit = 0, {"rule": 0, "vector": 0, "llm": 0}, {"rule": 0, "vector": 0, "llm": 0}
    misses: list[dict] = []
    t0 = time.perf_counter()
    for c in cases:
        r = await intent_classifier.classify(c["text"])
        layers[r.layer] = layers.get(r.layer, 0) + 1
        if r.intent == c["intent"]:
            correct += 1
            per_layer_hit[r.layer] = per_layer_hit.get(r.layer, 0) + 1
        else:
            misses.append({"text": c["text"], "expect": c["intent"], "got": r.intent,
                           "layer": r.layer})
    dt = time.perf_counter() - t0
    return {
        "suite": "intent", "cases": len(cases), "accuracy": round(correct / len(cases), 3),
        "avg_ms": round(dt * 1000 / len(cases)),
        "layer_distribution": layers, "layer_accuracy": per_layer_hit,
        "misses": misses,
    }


# ---------------- RAG 检索 ----------------
async def eval_rag(*, use_rewrite: bool = True, k: int = 5, verbose: bool = True) -> dict:
    from services.rag.pipeline import rag_pipeline

    cases = _load("retrieval.jsonl")
    hits, misses = 0, []
    t0 = time.perf_counter()
    for c in cases:
        out = await rag_pipeline.search(c["query"], use_rewrite=use_rewrite, top_k=k)
        files = {(r.get("meta") or {}).get("file") for r in out["results"]}
        if c["expected"] in files:
            hits += 1
        else:
            misses.append({"query": c["query"], "expect": c["expected"],
                           "got": sorted(f or "?" for f in files)})
        if verbose:
            mark = "HIT " if c["expected"] in files else "MISS"
            print(f"    [{mark}] {c['query']} → {c['expected']}")
    dt = time.perf_counter() - t0
    return {
        "suite": f"rag@{k}", "cases": len(cases),
        "recall": round(hits / len(cases), 3),
        "avg_ms": round(dt * 1000 / len(cases)),
        "use_rewrite": use_rewrite, "misses": misses,
    }


# ---------------- 上下文压缩 ----------------
async def eval_compression() -> dict:
    from services.memory.compressor import context_compressor

    # 构造超阈值长对话（重复填充确保 > 3000 字）
    msgs = []
    for i in range(10):
        msgs.append({"role": "user", "content": f"第{i}轮提问：请围绕论文选题给我建议。" + "背景填充" * 120})
        msgs.append({"role": "assistant", "content": f"第{i}轮回答：好的，建议如下。" + "内容填充" * 120})
    result = await context_compressor.compress(msgs, keep_recent=4, force=True)
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
