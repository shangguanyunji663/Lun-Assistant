"""论匠 FastAPI 入口：网关基座 + AI 运行时路由装配。"""
import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from infrastructure.config import get_value
from infrastructure.db import dispose_engine, get_engine
from api.middleware.audit import AuditMiddleware
from infrastructure.models import Base  # noqa: F401 —— 聚合导入确保全部表注册


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
    """后台预热：加载交叉编码器模型（CPU 首载 10~60s，线程池内执行，不阻塞启动）。"""
    try:
        from services.rag.reranker import reranker
        await reranker.preload()
        logger.info("预热完成：交叉编码器已加载")
    except Exception:
        logger.warning("交叉编码器预热失败，将在首次精排时懒加载", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 开发期直接建表；生产应使用 Alembic 迁移
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 注册全部治理工具（RBAC/限流/熔断/容错/审计流水线入口）
    from services.governance.tools_impl import register_all
    register_all()

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
    from api.projects.router import router as projects_router
    from api.knowledge.router import router as knowledge_router
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
