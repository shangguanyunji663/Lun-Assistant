"""论匠 FastAPI 入口：网关基座 + AI 运行时路由装配。"""
import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_value
from app.db import dispose_engine, get_engine
from app.middleware.audit import AuditMiddleware
from app.models import Base  # noqa: F401 —— 聚合导入确保全部表注册

if sys.platform == "win32":
    # psycopg 异步连接池需要 Selector 事件循环（Windows 默认 Proactor 不支持）
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 开发期直接建表；生产应使用 Alembic 迁移
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 注册全部治理工具（RBAC/限流/熔断/容错/审计流水线入口）
    from governance.tools_impl import register_all
    register_all()
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

    # ---- 健康检查 ----
    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "ok", "app": get_value("app", "name")}

    # ---- 平台基座路由（原 Java 职责）----
    from app.auth.router import router as auth_router
    from app.gateway.router import router as projects_router
    app.include_router(auth_router)
    app.include_router(projects_router)

    # ---- AI 运行时路由（阶段2装配）----
    from app.agent.router import router as agent_router
    app.include_router(agent_router)

    # ---- 可观测路由（阶段5装配）----
    from app.observability.router import router as obs_router
    app.include_router(obs_router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=get_value("app", "host"),
        port=int(get_value("app", "port")),
        reload=bool(get_value("app", "debug", default=False)),
    )
