"""RAG 三阶段检索冒烟：Query改写 → 双路混合召回(RRF) → 交叉编码器精排。

前置: 语料已入库（scripts/ingest_corpus.py）。
用法：python scripts/smoke_rag.py
"""
import asyncio
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main() -> None:
    from rag.pipeline import rag_pipeline

    queries = [
        "如何写好文献综述",
        "开题报告的常见问题有哪些",
        "RAG混合检索为什么要用RRF融合",
        "查重降重的合规做法",
    ]

    for q in queries:
        t0 = time.perf_counter()
        out = await rag_pipeline.search(q)
        dt = (time.perf_counter() - t0) * 1000
        print(f"\n=== 查询: {q}")
        print(f"    改写: {out['rewritten']}")
        print(f"    关键词: {out['keywords']}")
        print(f"    耗时: {dt:.0f}ms, 精排后: {len(out['results'])}")
        for i, r in enumerate(out["results"][:3], 1):
            meta = r.get("meta") or {}
            print(f"    TOP{i} [{meta.get('title', '?')}|chunk{meta.get('chunk')}] "
                  f"rerank={r.get('rerank_score', 0):.3f} :: {r['content'][:60]}...")


if __name__ == "__main__":
    asyncio.run(main())
