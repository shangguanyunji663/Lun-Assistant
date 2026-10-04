"""论匠 FastAPI 入口：网关基座 + AI 运行时路由装配。"""
import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from api.middleware.audit import AuditMiddleware
from infrastructure.config import get_value
from infrastructure.db import dispose_engine, get_engine
from infrastructure.models import Base


class SystemInfoOut(BaseModel):
    """根路径返回的服务自描述信息。"""
    app: str
    version: str
    docs: str
    health: str


class HealthOut(BaseModel):
    status: str
    app: str

if sys.platform == "win32":
    # psycopg 异步连接池需要 Selector 事件循环（Windows 默认 Proactor 不支持）
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

logger = logging.getLogger("lunjiang.app")


async def _warmup_bm25() -> None:
    """后台预热：重建 BM25 稀疏索引，避免首次 sparse_search 触发慢查询。"""
    try:
        from services.rag.retriever import hybrid_retriever
        n = await hybrid_retriever.rebuild_bm25()
        logger.info("预热完成：BM25 索引 %d 篇文档", n)
    except Exception:
        logger.warning("BM25 预热失败，将在首次检索时懒重建", exc_info=True)


async def _warmup_reranker() -> None:
    """后台预热：加载交叉编码器并完成首次推理（CPU 首载+首跑 10~60s，线程池内执行，不阻塞启动）。

    预热若失败，每一次首次检索都要付同样的冷启动成本（实测可达 90s），
    因此加载耗时与失败都必须在启动日志里可见。
    """
    from services.rag.reranker import reranker
    elapsed = await reranker.preload()
    if elapsed is not None:
        logger.info("预热完成：交叉编码器已加载（%.1fs）", elapsed)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 开发期直接建表；生产应使用 Alembic 迁移
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 注册全部治理工具（RBAC/限流/熔断/容错/审计流水线入口）
    from services.governance.tools_impl import register_all
    register_all()

    # Redis 可达性显式告警：缺失时限流/熔断/短期记忆/分布式锁静默降级，
    # 服务「看似正常但无记忆」，必须在启动期把这一状态喊出来
    try:
        from infrastructure.redis_client import get_redis
        await get_redis().ping()
        logger.info("Redis 已连接（短期记忆/限流/熔断/分布式锁 正常）")
    except Exception:
        logger.warning(
            "⚠️ Redis 不可用：短期记忆/限流窗口/熔断状态/分布式锁已静默降级，"
            "对话将失去上下文记忆。请确认 redis-server 已启动（端口见 .env 的 REDIS_PORT），"
            "或直接 scripts/dev_up.ps1 -infra-only"
        )

    # 后台预热（不阻塞 HTTP 就绪；首用户请求到来时大概率已完成）
    asyncio.create_task(_warmup_bm25())
    asyncio.create_task(_warmup_reranker())

    yield
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title="LunJiang 论匠 API",
        description="基于 LangGraph 的多智能体论文全流程辅助平台",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(AuditMiddleware)

    # ---- 健康检查 + 根路径 ----
    @app.get("/", response_model=SystemInfoOut, tags=["system"])
    async def root():
        return SystemInfoOut(
            app=get_value("app", "name"),
            version=app.version,
            docs="/docs",
            health="/health",
        )

    @app.get("/health", response_model=HealthOut, tags=["system"])
    async def health():
        return HealthOut(status="ok", app=get_value("app", "name"))

    # ---- 平台基座路由（原 Java 职责）----
    from api.auth.router import router as auth_router
    from api.knowledge.router import router as knowledge_router
    from api.projects.router import router as projects_router
    app.include_router(auth_router)
    app.include_router(projects_router)
    app.include_router(knowledge_router)

    # ---- AI 运行时路由（阶段2装配）----
    from api.agent.router import router as agent_router
    app.include_router(agent_router)

    # ---- 可观测路由（阶段5装配）----
    from api.observability.router import router as obs_router
    app.include_router(obs_router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=get_value("app", "host"),
        port=int(get_value("app", "port")),
        reload=bool(get_value("app", "debug", default=False)),
    )
