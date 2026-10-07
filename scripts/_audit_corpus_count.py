"""临时审计脚本：核对 retrieval 数据集期望语料是否都在库（只读）。"""
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main() -> None:
    from sqlalchemy import text

    from infrastructure.db import get_session_factory

    async with get_session_factory()() as db:
        rows = (await db.execute(text(
            "select distinct meta->>'file' from memory_items where kind='document'"))).all()
    in_db = {r[0] for r in rows if r[0]}
    print(f"库内语料文件数 = {len(in_db)}")

    for name in ("retrieval.jsonl", "retrieval_hard.jsonl", "retrieval_paper_hard.jsonl"):
        cases = [json.loads(line) for line in
                 open(ROOT / "evals" / "datasets" / name, encoding="utf-8") if line.strip()]
        exp = {c["expected"] for c in cases}
        missing = sorted(exp - in_db)
        print(f"{name:<28} 条数={len(cases):<4} 期望文件={len(exp):<4} "
              f"缺失={len(missing)} {missing if missing else ''}")


asyncio.run(main())
