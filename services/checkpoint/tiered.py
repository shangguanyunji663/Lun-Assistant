"""Checkpointer 三级降级存储：Redis → PostgreSQL → 进程内存。

- 一级 Redis: 低延迟热存储，支撑高频断点恢复
- 二级 PostgreSQL: Redis 不可用时持久化降级
- 三级 Memory: 都不可用时进程内兜底（单机开发模式）
- 对图编译透明: 返回的 saver 实现同一 BaseCheckpointSaver 接口
"""
import logging

from infrastructure.config import get_value

logger = logging.getLogger("lunjiang.checkpoint")


def with_suppress_close(pool) -> None:
    """失败时尽力关闭连接池，避免残留 pending worker 任务。"""
    import asyncio
    import contextlib

    task = asyncio.ensure_future(pool.close())
    async def _wait():
        with contextlib.suppress(Exception):
            await asyncio.wait_for(task, timeout=5)
    asyncio.ensure_future(_wait())


class TieredCheckpointer:
    """按优先级探测可用的 Checkpointer，返回 (saver, tier)。"""

    @staticmethod
    async def create() -> tuple[object, str]:
        # ---- 一级: Redis ----
        try:
            from langgraph.checkpoint.redis.aio import AsyncRedisSaver

            saver = AsyncRedisSaver(get_value("storage", "redis", "url"))
            await saver.setup()
            logger.info("Checkpointer 一级降级生效: Redis")
            return saver, "redis"
        except Exception as e:
            logger.warning("Redis Checkpointer 不可用: %s", e)

        # ---- 二级: PostgreSQL ----
        pool = None
        try:
            from psycopg_pool import AsyncConnectionPool
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

            # autocommit=True: setup() 的 CREATE INDEX CONCURRENTLY 不允许在事务块内
            pool = AsyncConnectionPool(
                conninfo=get_value("storage", "postgres", "sync_dsn"),
                min_size=1, max_size=5, open=False,
                kwargs={"autocommit": True},
            )
            await pool.open(wait=True, timeout=10)
            saver = AsyncPostgresSaver(pool)
            await saver.setup()
            logger.info("Checkpointer 二级降级生效: PostgreSQL")
            return saver, "postgres"
        except Exception as e:
            logger.warning("PostgreSQL Checkpointer 不可用: %s", e)
            if pool is not None:
                with_suppress_close(pool)

        # ---- 三级: Memory ----
        from langgraph.checkpoint.memory import InMemorySaver

        logger.warning("Checkpointer 三级降级生效: 进程内存（仅开发模式）")
        return InMemorySaver(), "memory"
