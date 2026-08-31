"""检查长期记忆归档情况（summary/decision 条目）。"""
import asyncio
import sys

sys.path.insert(0, ".")

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import text

from app.db import get_session_factory  # noqa: E402


async def main() -> None:
    async with get_session_factory()() as db:
        rows = (await db.execute(text(
            "SELECT id, kind, importance, left(content, 120) AS content "
            "FROM memory_items WHERE kind IN ('summary', 'decision') "
            "ORDER BY id DESC LIMIT 8"))).all()
        for r in rows:
            print(r)


if __name__ == "__main__":
    asyncio.run(main())
