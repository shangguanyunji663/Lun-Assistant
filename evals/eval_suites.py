"""评测扩展入口：对 retrieval_hard / retrieval_paper_hard / holdout 三个数据集直测 Recall@5。

为什么单独有这个入口：
    `evals/harness.py` 主基线只跑 `retrieval.jsonl`（简单集 20 条），
    而落地页与文档还引用「口语长尾集 / 学术刁钻集 / 泛化 hold-out」三组数字——
    2026-10-07 之前它们仅有 09-04 快照、无产物支撑（"口头水位"）。

    本脚本用与主基线**完全相同**的口径（same pipeline / rewrite_mode=on / top_k=5 /
    同一评分函数 score_rag）把三组补测出来，并写入带 provenance 的产物，
    使每个页面数字都能对应到 `evals/results_extra.json` 里的一条记录。
    首轮补测结果（2026-10-07）：长尾 85%（17/20）/ 学术 97.5%（39/40）/ 泛化 83.3%（25/30，8→30 扩充后）。

口径（与 harness 一致，勿单独修改）：
    - 召回判定：期望语料文件名出现在 Top-5 结果的 meta.file 集合里即算召回；
    - 改写策略：rewrite_mode="on"（强制 LLM 改写）；
    - 评分算术复用 evals/harness.py::score_rag，避免两套口径。

用法：
    python -m evals.eval_suites                       # 全部三组
    python -m evals.eval_suites retrieval_hard         # 指定数据集
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evals.harness import _load, score_rag
from evals.provenance import build_provenance, summarize_provenance
from infrastructure.paths import PROJECT_ROOT

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

OUT_PATH = PROJECT_ROOT / "evals" / "results_extra.json"
DEFAULT_SUITES = ("retrieval_hard", "retrieval_paper_hard", "holdout")


async def eval_dataset(stem: str, *, k: int = 5) -> dict:
    """对 evals/datasets/<stem>.jsonl 直测 Recall@k（口径与 harness 主基线一致）。"""
    from services.rag.pipeline import rag_pipeline

    cases = _load(f"{stem}.jsonl")
    results_per_case: list[list[dict]] = []
    t0 = time.perf_counter()
    for c in cases:
        out = await rag_pipeline.search(c["query"], use_rewrite=True, top_k=k,
                                        rewrite_mode="on")
        results_per_case.append(out["results"])
    report = score_rag(cases, results_per_case, k=k, use_rewrite=True,
                       elapsed_s=time.perf_counter() - t0)
    for c in cases:
        miss = next((m for m in report["misses"] if m["query"] == c["query"]), None)
        print(f"    [{'MISS' if miss else 'HIT '}] {c['query']} → {c['expected']}")
    return report


async def main(suites: list[str]) -> None:
    out: dict = {}
    if OUT_PATH.exists():
        try:
            out = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            out = {}
    out.pop("_provenance", None)

    t_start = time.perf_counter()
    for stem in suites:
        print(f"== {stem} ==")
        report = await eval_dataset(stem)
        out[stem] = report
        print(f"    Recall@5: {report['recall']:.1%} ({report['cases']} 条, "
              f"平均{report['avg_ms']}ms/条, miss={len(report['misses'])})")

    # provenance 覆盖产物内全部 suite（指纹按数据集现文件计算）；未重跑的沿用既有记录
    stale = sorted(set(out) - set(suites))
    provenance = build_provenance({s: f"{s}.jsonl" for s in out},
                                 elapsed_s=time.perf_counter() - t_start,
                                 command="envs\\lunjiang\\python.exe -m evals.eval_suites " + " ".join(suites))
    payload = {"_provenance": provenance, **out}
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n== 产物身份证（provenance）==")
    print(f"    {summarize_provenance(provenance)}")
    if stale:
        print(f"    ℹ 本轮未重跑、沿用既有产物的指标：{', '.join(stale)}"
              "（其数字来自上一次运行，provenance 时间戳非其观测时间）")
    print(f"\n结果已写入 {OUT_PATH}")


if __name__ == "__main__":
    picked = [a for a in sys.argv[1:] if a in DEFAULT_SUITES] or list(DEFAULT_SUITES)
    asyncio.run(main(picked))
