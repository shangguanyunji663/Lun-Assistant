"""记忆体系冒烟：四层装配 + 窗口压缩归档 + 长期向量召回。

前置: Redis / 独立 PostgreSQL 实例（D:\Develop\DB\PostgreSQL16）已运行。
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from infrastructure.db import get_engine
from services.memory.short_term import short_term_memory


async def main() -> None:
    # 建表（幂等）
    from infrastructure.models import Base
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    pid, sid = 0, "mem-smoke-0002"

    # ---- L1 短期记忆写入（超过 3000 字触发阈值）----
    for i in range(6):
        marker = "重要约束：全文必须使用中文写作，" if i % 2 == 0 else "普通讨论："
        await short_term_memory.append(pid, sid, "user", f"第{i}轮：{marker + '内容填充' * 150}")
        await short_term_memory.append(pid, sid, "assistant", f"第{i}轮回复：{'好的，已了解。' + '回复填充' * 150}")
    total = await short_term_memory.total_chars(pid, sid)
    print(f"[L1] 短期记忆累计 {total} 字（阈值 3000）")

    # ---- 四级压缩：截断 → 摘要 → 归档长期记忆 ----
    from services.memory.compressor import compress_window_if_needed
    result = await compress_window_if_needed(pid, sid)
    assert result is not None, "应触发压缩"
    print(f"[压缩] 原始 {result.original_chars} 字 → {result.compressed_chars} 字 "
          f"(ratio={result.ratio:.2f}, 摘要={result.summary[:60]}...)")

    # ---- L4 偏好沉淀 + 召回（取真实用户 id 满足外键）----
    from sqlalchemy import select

    from infrastructure.db import get_session_factory
    from infrastructure.models.user import User
    from services.memory.preference import preference_memory
    async with get_session_factory()() as db:
        uid = (await db.execute(select(User.id).limit(1))).scalar()
        assert uid is not None, "请先注册至少一个用户"
        await preference_memory.learn(db, user_id=uid, content="用户偏好：参考文献使用 GB/T 7714 格式")
        prefs = await preference_memory.recall(db, uid)
    print(f"[L4] 偏好召回 {len(prefs)} 条: {prefs[:1]}")

    # ---- L3 长期向量召回 ----
    from services.memory.long_term import long_term_memory
    async with get_session_factory()() as db:
        text = await long_term_memory.recall_text(db, query="论文写作有什么约束要求吗",
                                                  project_id=0, top_k=2)
    print(f"[L3] 长期召回:\n{text[:200]}")

    # ---- 引擎四层装配 ----
    from services.agent.engine import AgentEngine
    history, brief = await AgentEngine._assemble_memory(
        project_id=0, session_id=sid, user_id=uid, user_input="写作格式要求")
    print(f"[装配] history_text {len(history)} 字; memory_brief {len(brief)} 字")
    print("memory_brief 预览:", brief[:300].replace("\n", " | "))

    print("\nmemory smoke OK")


if __name__ == "__main__":
    asyncio.run(main())
