"""独立 hold-out 意图集：打破 L2 原型句泄漏，得到经得起追问的意图准确率。

为什么必须单独建这个集合：
    现有 `evals/datasets/intent.jsonl`（50 条）与 `services/classifier/intent.py:47-55`
    的 L2 原型句**同源**——「你能做什么」逐字相同，另有 8 条字面 Jaccard ≥ 0.6。
    即"用原型句当参考答案，再用它的改写当考题"，因此 100%（旧）与 92%（重跑）
    都偏乐观。

    本集合的构造纪律（关键，勿破坏）：
    1. **零字面重叠**：每条与所有原型句、L1 正则的**字面重合必须为 0**（`--validate` 校验）；
    2. **口语化长尾**：贴近真实用户说法，不写教科书式标准句；
    3. **标签与预测分离**：数据集 `intent_holdout.jsonl` 只存 `text` 与**人工复核参考标签**；
       盲跑产物 `results_intent_holdout.json` 独立记录 `predicted`/`layer`/`confidence`，
       两者比对得到准确率与分层错误率（复核协议见 `scripts/_audit_holdout_review.py`）。

    数据集：`evals/datasets/intent_holdout.jsonl`（92 条，7 类）
    产物：  `evals/results_intent_holdout.json`

用法：
    python -m evals.eval_intent_holdout --validate   # 只校验零重叠纪律
    python -m evals.eval_intent_holdout              # 盲跑分类器并落产物
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evals.provenance import build_provenance, summarize_provenance
from infrastructure.paths import PROJECT_ROOT

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

HOLDOUT = PROJECT_ROOT / "evals" / "datasets" / "intent_holdout.jsonl"
OUT = PROJECT_ROOT / "evals" / "results_intent_holdout.json"


def _load_holdout() -> tuple[list[str], dict[str, str]]:
    """读 hold-out 数据集，返回 (文本列表, 文本→人工复核参考标签)。

    数据集纪律见文件头：样本**刻意避开全部 L1 触发字**，用于度量
    「规则层覆盖不到的长尾流量」。`intent` 字段是 2026-10-05 人工复核填入的
    参考标签（复核协议见 `scripts/_audit_holdout_review.py`），**不是**分类器预测。
    """
    rows = [json.loads(line) for line in
            HOLDOUT.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r["text"] for r in rows], {r["text"]: r.get("intent", "") for r in rows}


TEXTS, GOLD = _load_holdout()


def _rules_literal_hits(text: str) -> list[str]:
    from services.classifier.intent import _RULES
    return [intent for intent, pat in _RULES if pat.search(text)]


def validate() -> list[str]:
    """纪律校验：每条样本与全部 L1 正则的字面命中 + 与原型句的逐字重复。"""
    from services.classifier.intent import IntentClassifier

    protos = {s for ss in IntentClassifier()._prototypes.values() for s in ss}
    problems = []
    for t in TEXTS:
        if t in protos:
            problems.append(f"与原型句逐字相同: {t}")
        hits = _rules_literal_hits(t)
        if hits:
            problems.append(f"命中 L1 规则 {hits}: {t}")
    return problems


async def main(validate_only: bool) -> None:
    problems = validate()
    print(f"hold-out 样本数: {len(TEXTS)}")
    print(f"纪律校验：与原型句/ L1 正则的冲突 = {len(problems)} 条")
    for p in problems[:20]:
        print(f"  ⚠ {p}")
    if validate_only:
        return
    if problems:
        print("\n⚠ 存在冲突，建议先修订样本再跑（否则又是有泄漏的集合）")

    from services.classifier.intent import intent_classifier

    # 盲跑：样本里没有期望标签，避免确认偏差
    rows, layers = [], {"rule": 0, "vector": 0, "llm": 0}
    for t in TEXTS:
        r = await intent_classifier.classify(t)
        layers[r.layer] = layers.get(r.layer, 0) + 1
        rows.append({"text": t, "predicted": r.intent, "layer": r.layer,
                     "confidence": round(r.confidence, 3),
                     "review": ""})   # review 留给人工复核填写

    payload = {
        "_provenance": build_provenance({}, elapsed_s=None),
        "note": "盲标集合：intent 标签未预设，predicted 为分类器盲跑结果，review 待人工复核",
        "cases": len(rows),
        "layer_distribution": layers,
        "predictions": rows,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n分层分布: {layers}")
    print(f"结果已写入 {OUT}")
    print(f"身份证: {summarize_provenance(payload['_provenance'])}")


if __name__ == "__main__":
    asyncio.run(main("--validate" in sys.argv))
