"""API 层离线集成测试：真实路由 + 真实 JWT/bcrypt + SQLite 内存库。

覆盖此前零测试的 api/ 门面（auth / projects / observability / agent 鉴权）。
不依赖 PostgreSQL / Redis / LLM，CI 可直接跑：

- 把 infrastructure.db._session_factory 补丁为 aiosqlite 内存引擎（StaticPool 单连接），
  get_db 依赖与 get_session_factory 直调两条取会话路径全部落到内存库；
- sqlite 方言下 BigInteger 主键编译为 INTEGER——SQLite 仅对 INTEGER PRIMARY KEY
  做行 ID 自增，不改则 audit_logs / trace_spans 插入必报 NOT NULL；
- 认证端点的 Redis 限流 check_rate 默认打桩放行，另设用例验证 429 路径；
- 认证本身（bcrypt 散列 / JWT 签发与解析 / require_role）走真实实现；
- 知识库路由需 pgvector 列与嵌入服务，不在离线范围（由 smoke_api 覆盖）。
"""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import BigInteger
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from api.auth.router import router as auth_router
from api.auth.security import create_access_token, hash_password
from api.observability.router import router as observability_router
from api.projects.router import router as projects_router
from infrastructure.models.audit import AuditLog
from infrastructure.models.base import Base
from infrastructure.models.project import Project
from infrastructure.models.trace import TraceSpan
from infrastructure.models.user import User


@compiles(BigInteger, "sqlite")
def _bigint_as_integer(type_, compiler, **kw):
    """SQLite 行 ID 自增要求主键类型名为 INTEGER，BigInteger 主键需降级渲染。"""
    return "INTEGER"


@pytest.fixture()
async def engine():
    eng = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,  # 内存库单连接：所有会话共享同一份数据
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[
            User.__table__, Project.__table__, AuditLog.__table__, TraceSpan.__table__,
        ])
    yield eng
    await eng.dispose()


@pytest.fixture()
def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
def _sqlite_backend(session_factory, monkeypatch):
    """get_db 与 get_session_factory 直调（observability/trace 服务）统一走内存库。"""
    monkeypatch.setattr("infrastructure.db._session_factory", session_factory)


@pytest.fixture(autouse=True)
def _offline_rate_limit(monkeypatch):
    """认证限流默认放行（Redis 不在离线范围）；429 用例在测试内覆盖此桩。"""
    async def _allow(*args, **kwargs):
        return None
    monkeypatch.setattr("api.auth.router.check_rate", _allow)


@pytest.fixture()
def app():
    test_app = FastAPI()
    test_app.include_router(auth_router)
    test_app.include_router(projects_router)
    test_app.include_router(observability_router)
    return test_app


@pytest.fixture()
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _register_and_login(client: AsyncClient, username: str,
                              password: str = "secret1") -> str:
    r = await client.post("/api/auth/register",
                          json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    r = await client.post("/api/auth/login",
                          json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


async def _seed_admin(session_factory, username: str = "root") -> int:
    """绕过注册端点直接落一个 admin 用户（注册入口固定 student 角色）。"""
    async with session_factory() as s:
        admin = User(username=username, password_hash=hash_password("adminpw"),
                     role="admin")
        s.add(admin)
        await s.commit()
        return admin.id


# ---------------- 认证：注册 / 登录 / JWT ----------------

async def test_register_login_me_roundtrip(client):
    r = await client.post("/api/auth/register",
                          json={"username": "alice", "password": "secret1"})
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "alice" and body["id"] > 0

    r = await client.post("/api/auth/login",
                          json={"username": "alice", "password": "secret1"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    assert r.json()["user"]["role"] == "student"

    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == {"id": body["id"], "username": "alice", "role": "student"}


async def test_register_duplicate_username_conflict(client):
    payload = {"username": "bob", "password": "secret1"}
    assert (await client.post("/api/auth/register", json=payload)).status_code == 200
    r = await client.post("/api/auth/register", json=payload)
    assert r.status_code == 409


async def test_login_rejects_wrong_password_and_unknown_user(client):
    await _register_and_login(client, "carol")
    r = await client.post("/api/auth/login",
                          json={"username": "carol", "password": "wrong!"})
    assert r.status_code == 401
    r = await client.post("/api/auth/login",
                          json={"username": "nobody", "password": "secret1"})
    assert r.status_code == 401


async def test_me_rejects_missing_and_tampered_token(client):
    r = await client.get("/api/auth/me")
    assert r.status_code == 401
    token = await _register_and_login(client, "dave")
    r = await client.get("/api/auth/me",
                         headers={"Authorization": f"Bearer {token[:-4]}aaaa"})
    assert r.status_code == 401


async def test_register_throttled_to_429(client, monkeypatch):
    from services.governance.rate_limiter import RateLimitExceeded

    async def _deny(*args, **kwargs):
        raise RateLimitExceeded("限流")

    monkeypatch.setattr("api.auth.router.check_rate", _deny)
    r = await client.post("/api/auth/register",
                          json={"username": "erin", "password": "secret1"})
    assert r.status_code == 429
    assert "每分钟最多" in r.json()["detail"]


# ---------------- 论文项目：CRUD / 归属校验 ----------------

async def test_project_requires_authentication(client):
    r = await client.get("/api/projects")
    assert r.status_code == 401


async def test_project_crud_lifecycle(client):
    headers = {"Authorization": f"Bearer {await _register_and_login(client, 'frank')}"}
    r = await client.post("/api/projects",
                          json={"title": "RAG可解释性研究", "major": "计算机"},
                          headers=headers)
    assert r.status_code == 200
    pid = r.json()["id"]
    assert r.json()["status"] == "created"

    r = await client.get("/api/projects", headers=headers)
    assert [item["id"] for item in r.json()] == [pid]

    r = await client.get(f"/api/projects/{pid}", headers=headers)
    assert r.status_code == 200
    assert r.json()["title"] == "RAG可解释性研究"
    assert r.json()["structured_memory"] is None

    r = await client.patch(f"/api/projects/{pid}", json={"status": "topic"},
                           headers=headers)
    assert r.status_code == 200 and r.json()["status"] == "topic"

    r = await client.delete(f"/api/projects/{pid}", headers=headers)
    assert r.status_code == 200 and r.json()["deleted"] == pid
    r = await client.get(f"/api/projects/{pid}", headers=headers)
    assert r.status_code == 404


async def test_project_rejects_unknown_status(client):
    headers = {"Authorization": f"Bearer {await _register_and_login(client, 'grace')}"}
    r = await client.post("/api/projects", json={}, headers=headers)
    pid = r.json()["id"]
    r = await client.patch(f"/api/projects/{pid}", json={"status": "bogus"},
                           headers=headers)
    assert r.status_code == 422


async def test_project_ownership_isolated_between_users(client):
    alice_h = {"Authorization": f"Bearer {await _register_and_login(client, 'alice2')}"}
    pid = (await client.post("/api/projects", json={}, headers=alice_h)).json()["id"]

    mallory_h = {"Authorization": f"Bearer {await _register_and_login(client, 'mallory')}"}
    assert (await client.get(f"/api/projects/{pid}", headers=mallory_h)).status_code == 404
    assert (await client.patch(f"/api/projects/{pid}", json={"status": "topic"},
                               headers=mallory_h)).status_code == 404
    assert (await client.delete(f"/api/projects/{pid}", headers=mallory_h)).status_code == 404
    # 他人项目也不出现在自己的列表里
    assert (await client.get("/api/projects", headers=mallory_h)).json() == []


async def test_admin_can_access_any_project(client, session_factory):
    admin_id = await _seed_admin(session_factory)
    user_h = {"Authorization": f"Bearer {await _register_and_login(client, 'henry')}"}
    pid = (await client.post("/api/projects", json={"title": "别人的项目"},
                             headers=user_h)).json()["id"]

    admin_h = {"Authorization": f"Bearer {create_access_token(admin_id, 'admin')}"}
    r = await client.get(f"/api/projects/{pid}", headers=admin_h)
    assert r.status_code == 200 and r.json()["title"] == "别人的项目"


# ---------------- 可观测：require_role + Trace 列表/回放 ----------------

async def _seed_trace(session_factory, trace_id: str = "tr-001") -> None:
    async with session_factory() as s:
        s.add(TraceSpan(trace_id=trace_id, span_id="s-root", kind="engine",
                        name="agent_run", status="ok", latency_ms=100, cost_usd=0.01,
                        user_id=1))
        s.add(TraceSpan(trace_id=trace_id, span_id="s-kid", parent_span_id="s-root",
                        kind="tool", name="search_literature", status="ok",
                        latency_ms=40, cost_usd=0.0, user_id=1))
        await s.commit()


async def test_observability_requires_admin(client):
    r = await client.get("/api/observability/traces")
    assert r.status_code == 401  # 未认证
    user_h = {"Authorization": f"Bearer {await _register_and_login(client, 'iris')}"}
    r = await client.get("/api/observability/traces", headers=user_h)
    assert r.status_code == 403  # student 无权（require_role）


async def test_trace_list_and_replay(client, session_factory):
    admin_id = await _seed_admin(session_factory)
    await _seed_trace(session_factory)
    admin_h = {"Authorization": f"Bearer {create_access_token(admin_id, 'admin')}"}

    r = await client.get("/api/observability/traces", headers=admin_h)
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["trace_id"] == "tr-001" and items[0]["spans"] == 2
    assert items[0]["total_latency_ms"] == 140

    r = await client.get("/api/observability/traces/tr-001", headers=admin_h)
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["span_count"] == 2
    assert body["summary"]["total_latency_ms"] == 140
    assert len(body["tree"]) == 1 and len(body["tree"][0]["children"]) == 1
    assert body["tree"][0]["children"][0]["name"] == "search_literature"

    r = await client.get("/api/observability/traces/no-such", headers=admin_h)
    assert r.status_code == 404


async def test_metrics_counts_reflect_seeded_rows(client, session_factory):
    admin_id = await _seed_admin(session_factory)
    await _seed_trace(session_factory, "tr-metrics")
    admin_h = {"Authorization": f"Bearer {create_access_token(admin_id, 'admin')}"}

    r = await client.get("/api/observability/metrics", headers=admin_h)
    assert r.status_code == 200
    counts = r.json()["counts"]
    assert counts["users"] == 1
    assert counts["trace_spans"] == 2
    # knowledge_documents 表未在内存库建（需 pgvector），容错路径应返回 None
    assert counts["knowledge_documents"] is None


# ---------------- Agent 运行时：仅验证鉴权门槛（SSE 编排由 smoke_graph 覆盖） ----------------

async def test_agent_endpoints_require_authentication(app, session_factory):
    from api.agent.router import router as agent_router

    app.include_router(agent_router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.post("/api/agent/chat",
                         json={"session_id": "12345678", "message": "你好"})
        assert r.status_code == 401
        r = await c.post("/api/agent/resume",
                         json={"session_id": "12345678", "feedback": "确认"})
        assert r.status_code == 401
