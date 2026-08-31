"""语料入库：读取 data/corpus/*.txt → 分块 → 向量化 → pgvector 入库 → 重建 BM25。

用法：python scripts/ingest_corpus.py [--force]
"""
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main() -> None:
    force = "--force" in sys.argv

    # 建表（幂等）
    from app.db import get_engine
    from app.models import Base
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from rag.ingest.corpus_loader import ingest_corpus
    result = await ingest_corpus(force=force)
    print("入库结果:", result)


if __name__ == "__main__":
    asyncio.run(main())
