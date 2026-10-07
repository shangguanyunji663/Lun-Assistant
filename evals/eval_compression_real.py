"""真实语料压缩率重测：用 data/corpus 的真实论文段落替代合成填充文本。

为什么必须重测：
    `evals/harness.py:86-94` 的 fixture 是 `"背景填充" * 120` —— 高度重复的合成文本，
    任何压缩算法都能拿到漂亮数字（0.212）。而且 `harness.py:135` 显式传
    `keep_recent=4`，而生产默认是 `compress_trigger_tokens // 8 = 375`：
    **参数一改结果就变**，所以那个数字不测压缩能力，只测参数。

本脚本口径（与 harness 对齐，便于直接对比）：
    - 10 轮 × (user + assistant)，总量与合成 fixture 同量级（≈1 万字）；
    - assistant 内容取 data/corpus 真实论文段落（每段约 500 字），**不是重复填充**；
    - 混入 3 轮带高价值标记（"记住/改成/要求"）的用户纠正如真实对话，
      触发 `_HIGH_VALUE_MARKERS` 分级留存路径；
    - 同时跑 `keep_recent=4`（published 口径）与 `keep_recent=375`（生产默认），
      暴露该参数对结果的影响。

产物：`evals/results_compression_real.json`（含 provenance）

用法：
    python -m evals.eval_compression_real              # 两种 keep_recent 都跑
    python -m evals.eval_compression_real --dry-run    # 只造 fixture 并打印规模
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evals.provenance import build_provenance, summarize_provenance
from infrastructure.config import get_value
from infrastructure.paths import PROJECT_ROOT

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

CORPUS = PROJECT_ROOT / "data" / "corpus"
DATASETS = PROJECT_ROOT / "evals" / "datasets"
OUT_PATH = PROJECT_ROOT / "evals" / "results_compression_real.json"

ROUNDS = 12
EXCERPT_CHARS = 1000         # 每轮 assistant 正文长度，与合成 fixture 的 9920 字同量级
# 三个口径：
#   0   = **生产真实路径**（compress_window_if_needed 传 keep_recent=0，被逐出消息整体压缩）
#   4   = 原 harness 口径（历史发布数字 0.212 用的就是这个）
#   None = ctx.compress() 的签名默认值（375），生产不传该值，仅供对照
KEEP_RECENT_VARIANTS: tuple = (0, 4, None)


def _paragraphs(text: str, size: int) -> list[str]:
    """把语料切成语义段（按句号/换行聚合到约 size 字），保证是真实连贯文本。"""
    chunks = [c.strip() for c in re.split(r"(?<=[。！？\n])", text) if c.strip()]
    out, buf = [], ""
    for c in chunks:
        if len(buf) + len(c) <= size:
            buf += c
        else:
            if buf:
                out.append(buf)
            buf = c
    if buf:
        out.append(buf)
    return out


def build_real_fixture() -> list[dict]:
    """构造 12 轮真实对话：问题取自检索集，回答取自语料正文。"""
    cases = [json.loads(line) for line in
             (DATASETS / "retrieval.jsonl").read_text(encoding="utf-8").splitlines()
             if line.strip()]
    pool: list[tuple[str, str]] = []          # (query, excerpt)
    for c in cases:
        path = CORPUS / c["expected"]
        if not path.is_file():
            continue
        paras = _paragraphs(path.read_text(encoding="utf-8", errors="ignore"), EXCERPT_CHARS)
        if paras:
            pool.append((c["query"], paras[0]))

    # 高价值纠正：真实对话里用户会中途改要求，触发 _HIGH_VALUE_MARKERS 分级留存
    corrections = {
        2: "要求：后续章节都按 GB/T 7714 格式引用，记住这一点。",
        5: "这段不对，我改成实证研究路线，不要纯理论综述。",
        8: "重要：导师要求实验部分必须有对照实验，务必保留。",
    }

    msgs: list[dict] = []
    for i in range(ROUNDS):
        query, excerpt = pool[i % len(pool)]
        msgs.append({"role": "user", "content": f"第{i + 1}轮提问：{query}"
                     + (corrections.get(i, ""))})
        msgs.append({"role": "assistant", "content": f"第{i + 1}轮回答：{excerpt}"})
    return msgs


def marker_attribution(messages: list[dict]) -> dict:
    """归因：哪些消息被判为「高价值」、各自命中哪个标记词、误判来自正文还是用户纠正。

    这是本脚本存在的核心理由：0.766 的压缩率**不是算法不行**，而是
    `_HIGH_VALUE_MARKERS` 用子串匹配，把中文论文正文里的高频词（要求/重要/必须）
    全部判成"用户纠正"，导致大段正文被强制保留、永不压缩。
    """
    from services.memory.compressor import _HIGH_VALUE_MARKERS, _is_high_value

    rows, by_marker = [], {m: 0 for m in _HIGH_VALUE_MARKERS}
    for i, msg in enumerate(messages):
        if not _is_high_value(msg):
            continue
        hits = [m for m in _HIGH_VALUE_MARKERS if m in msg.get("content", "")]
        for h in hits:
            by_marker[h] += 1
        rows.append({
            "index": i,
            "role": msg.get("role"),
            # 用户消息即"真实纠正"，assistant 正文命中标记即**误判**
            "verdict": "真实纠正" if msg.get("role") == "user" else "误判（正文含高频词）",
            "markers_hit": hits,
            "chars": len(msg.get("content", "")),
            "preview": msg.get("content", "")[:60],
        })
    total_chars = sum(len(m.get("content", "")) for m in messages)
    hv_chars = sum(r["chars"] for r in rows)
    false_positives = [r for r in rows if r["verdict"].startswith("误判")]
    return {
        "high_value_messages": len(rows),
        "high_value_chars": hv_chars,
        "high_value_char_share": round(hv_chars / total_chars, 3) if total_chars else 0.0,
        "false_positive_messages": len(false_positives),
        "false_positive_chars": sum(r["chars"] for r in false_positives),
        "marker_hit_counts": by_marker,
        "detail": rows,
    }


async def run_variant(messages: list[dict], keep_recent: int | None) -> dict:
    from services.memory.compressor import context_compressor

    result = await context_compressor.compress(messages, keep_recent=keep_recent, force=True)
    producers = getattr(context_compressor, "_provider", None)
    return {
        "keep_recent": keep_recent if keep_recent is not None else "default(375)",
        "original_chars": result.original_chars,
        "compressed_chars": result.compressed_chars,
        "ratio": round(result.ratio, 3),
        "target_ratio": 0.3,
        "pass": result.ratio <= 0.3,
        "kept_messages": len(result.messages),
        "evicted_messages": len(result.removed),
        "summary_chars": len(result.summary),
        "llm_called": producers is not None,
    }


async def main(dry_run: bool) -> None:
    trigger = int(get_value("memory", "compress_trigger_tokens", default=3000))
    messages = build_real_fixture()
    total = sum(len(m["content"]) for m in messages)
    attribution = marker_attribution(messages)
    print(f"真实语料 fixture：{len(messages)} 条消息 / {total} 字"
          f"（压缩触发阈值 {trigger} 字）")
    print(f"  高价值消息 {attribution['high_value_messages']} 条"
          f" / {attribution['high_value_chars']} 字"
          f"（占全文 {attribution['high_value_char_share']:.1%}）")
    print(f"  其中**误判**（assistant 正文含高频词）{attribution['false_positive_messages']} 条"
          f" / {attribution['false_positive_chars']} 字")
    print(f"  标记命中次数：{attribution['marker_hit_counts']}")
    if dry_run:
        return

    results: dict = {}
    for variant in KEEP_RECENT_VARIANTS:
        r = await run_variant(messages, variant)
        results[f"keep_recent_{r['keep_recent']}"] = r
        print(f"  keep_recent={r['keep_recent']:<14} "
              f"{r['original_chars']} → {r['compressed_chars']} 字 "
              f"ratio={r['ratio']} {'PASS' if r['pass'] else 'FAIL'}"
              f"（保留 {r['kept_messages']} 条 / 逐出 {r['evicted_messages']} 条，"
              f"摘要 {r['summary_chars']} 字）")

    payload = {
        "_provenance": build_provenance(
            {"compression_real": "retrieval.jsonl"},
            elapsed_s=None),
        "fixture": {
            "source": "data/corpus（真实论文段落）",
            "rounds": ROUNDS,
            "messages": len(messages),
            "original_chars": total,
            "note": "替代 evals/harness.py 的合成重复文本 fixture，用于暴露真实压缩水位",
        },
        "high_value_attribution": attribution,
        "variants": results,
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n== 产物身份证 ==")
    print(f"    {summarize_provenance(payload['_provenance'])}")
    print(f"\n结果已写入 {OUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main("--dry-run" in sys.argv))
