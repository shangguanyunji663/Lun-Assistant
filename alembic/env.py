"""Alembic 迁移环境：异步引擎 + 聚合项目全部 ORM 模型。

- DSN 不从 alembic.ini 读取，而是复用基础设施配置层
  infrastructure.config.get_value("storage", "postgres", "async_dsn")，
  保证与运行时（asyncpg）使用同一连接串、同一维度配置。
- target_metadata = Base.metadata：infrastructure.models 聚合了全部表，
  因此 autogenerate 可一次性生成完整初始迁移。
- pgvector 的 Vector 类型已内置 Alembic 支持（compare_type 生效）。
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from infrastructure.config import get_value
from infrastructure.models import Base  # 聚合全部 ORM 模型

config = context.config

# 日志配置（alembic.ini [loggers] 段）
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 用配置层覆盖连接串：运行时 async DSN（asyncpg 驱动）
config.set_main_option("sqlalchemy.url", get_value("storage", "postgres", "async_dsn"))

# 供 autogenerate 比对的全表元数据
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式：只渲染 SQL，不需要数据库连接。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """在线模式：异步引擎执行迁移（与 app 运行时的 asyncpg 一致）。"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
