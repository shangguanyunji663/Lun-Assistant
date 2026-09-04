"""语料入库：读取 data/corpus/*.txt → 分块 → 向量化 → pgvector 入库 → 重建 BM25。

用法：python scripts/ingest_corpus.py [--force]
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main() -> None:
    force = "--force" in sys.argv

    # 建表（幂等）
    from infrastructure.db import dispose_engine, get_engine
    from infrastructure.models import Base
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from services.rag.ingest.corpus_loader import ingest_corpus
    result = await ingest_corpus(force=force)
    print("入库结果:", result)

    await dispose_engine()   # 关连接池，避免 asyncio.run 收尾时挂起


if __name__ == "__main__":
    asyncio.run(main())
