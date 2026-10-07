"""临时审计脚本：量化"简单集为什么简单"——查询与期望语料的字面重合度。

用途：回应"20 条拿到 100% 会不会显得假"。
    假的感觉来自"没有难度参照系"。本脚本用**纯字面重合**（无需 PG/LLM）
    对比四个检索集的难度画像，给出可写进文档/简历的客观依据。

口径：取查询的分词集合（中文按 2-gram + 英文数字整词）与期望语料正文的分词集合求交，
    重合率 = |交集| / |查询词集|。重合率高 = 关键词直给 = 简单。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CORPUS = ROOT / "data" / "corpus"
DATASETS = ROOT / "evals" / "datasets"


def tokens(text: str) -> set[str]:
    """中文 2-gram + 英文/数字整词，去停用样式噪声。"""
    text = text.lower()
    grams: set[str] = set(re.findall(r"[a-z0-9]{2,}", text))
    han = re.sub(r"[^\u4e00-\u9fff]", "", text)
    grams.update(han[i:i + 2] for i in range(len(han) - 1))
    return grams


def overlap(query: str, doc: str) -> float:
    q, d = tokens(query), tokens(doc)
    return len(q & d) / len(q) if q else 0.0


def report(name: str) -> None:
    rows = [json.loads(line) for line in
            (DATASETS / name).read_text(encoding="utf-8").splitlines() if line.strip()]
    scores, missing = [], 0
    for r in rows:
        path = CORPUS / r["expected"]
        if not path.is_file():
            missing += 1
            continue
        scores.append(overlap(r["query"], path.read_text(encoding="utf-8", errors="ignore")))
    scores.sort()
    avg = sum(scores) / len(scores)
    ge70 = sum(1 for s in scores if s >= 0.70)
    ge85 = sum(1 for s in scores if s >= 0.85)
    print(f"{name:<28} n={len(scores):<3} 平均字面重合={avg:5.1%}  "
          f"≥70% 的条目={ge70:>2}/{len(scores)}  ≥85% 的条目={ge85:>2}/{len(scores)}"
          + (f"  (缺语料 {missing})" if missing else ""))


for ds in ("retrieval.jsonl", "retrieval_hard.jsonl",
           "retrieval_paper_hard.jsonl", "holdout.jsonl"):
    report(ds)

# 逐条给出简单集的最高重合条目，作为"为什么简单"的例证
print("\n简单集 retrieval.jsonl 逐条字面重合率（升序）：")
rows = [json.loads(line) for line in
        (DATASETS / "retrieval.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
pairs = sorted(((overlap(r["query"], (CORPUS / r["expected"]).read_text(
    encoding="utf-8", errors="ignore")), r["query"]) for r in rows if (CORPUS / r["expected"]).is_file()))
for score, q in pairs:
    print(f"  {score:6.1%}  {q}")
