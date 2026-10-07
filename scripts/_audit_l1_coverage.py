"""临时审计脚本：独立评估 L1 规则层在 intent.jsonl(50) 上的覆盖率与准确率。

不依赖 PG/Ollama/Redis；只导入 _RULES 正则。
用法: python scripts/_audit_l1_coverage.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.classifier.intent import _RULES  # noqa: E402

rows = [json.loads(line) for line in
        open(ROOT / "evals" / "datasets" / "intent.jsonl", encoding="utf-8") if line.strip()]

hit = miss = wrong = 0
wrongs = []
per_intent = {}
for r in rows:
    per_intent.setdefault(r["intent"], [0, 0])
    per_intent[r["intent"]][1] += 1
    got = None
    for intent, pat in _RULES:
        if pat.search(r["text"]):
            got = intent
            break
    if got is None:
        miss += 1
    elif got == r["intent"]:
        hit += 1
        per_intent[r["intent"]][0] += 1
    else:
        wrong += 1
        wrongs.append((r["text"], r["intent"], got))

print(f"L1 规则层独立评估：{hit}/{len(rows)} = {100 * hit / len(rows):.1f}% 命中"
      f" | 未覆盖 {miss} | 误判 {wrong}")
print("分层覆盖（规则命中/该类总数）：")
for k, (h, n) in per_intent.items():
    print(f"  {k:<20} {h}/{n}")
for w in wrongs:
    print("  MISCLASSIFY:", w)
