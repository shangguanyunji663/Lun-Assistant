"""知识库路由离线集成测试：真实路由 + SQLite 元数据表 + 向量层打桩。

knowledge_documents 表无向量列，SQLite 可真建真查——因此 upload→list→delete 的
元数据链路、mode=project 空库短路、检索结果映射全部走真实路由逻辑；
仅三类触向量层的服务打桩（不依赖 PG/嵌入模型）：
- ingest_document（解析+分块+向量化，位于 api.knowledge.router 命名空间）
- delete_document（删 MemoryItem 向量分块，Vector 列 SQLite 无法建表）
- rag_pipeline.search（多路召回+精排）

列表/计数用真实 list_documents / count_documents，覆盖真实 SQL 路径。
"""
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import BigInteger
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from api.auth.router import router as auth_router
from api.knowledge.router import router as knowledge_router
from api.projects.router import router as projects_router
from infrastructure.models.audit import AuditLog
from infrastructure.models.base import Base
from infrastructure.models.knowledge import KnowledgeDocument
from infrastructure.models.project import Project
from infrastructure.models.trace import TraceSpan
from infrastructure.models.user import User


@compiles(BigInteger, "sqlite")
def _bigint_as_integer(type_, compiler, **kw):
    """SQLite 行 ID 自增要求主键类型名为 INTEGER（见 test_api_offline.py 同名说明）。"""
    return "INTEGER"


@pytest.fixture()
async def engine():
    eng = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[
            User.__table__, Project.__table__, AuditLog.__table__,
            TraceSpan.__table__, KnowledgeDocument.__table__,
        ])
    yield eng
    await eng.dispose()


@pytest.fixture()
def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
def _sqlite_backend(session_factory, monkeypatch):
    monkeypatch.setattr("infrastructure.db._session_factory", session_factory)


@pytest.fixture(autouse=True)
def _offline_rate_limit(monkeypatch):
    async def _allow(*args, **kwargs):
        return None
    monkeypatch.setattr("api.auth.router.check_rate", _allow)


@pytest.fixture(autouse=True)
def _fake_vector_services(monkeypatch):
    """打桩三类触向量层的服务；记录调用以便断言路由传参。"""
    calls = {"ingest": [], "delete": [], "search": []}

    async def _ingest(*, db, project_id, user_id, filename, data):
        calls["ingest"].append({"filename": filename, "bytes": len(data)})
        if "boom" in filename:
            raise RuntimeError("解析失败" + "，详细原因" * 60)   # >200 字符，验证截断
        ftype = filename.rsplit(".", 1)[-1] if "." in filename else "txt"
        doc = KnowledgeDocument(project_id=project_id, user_id=user_id,
                                filename=filename, file_type=ftype,
                                size_bytes=len(data), content_hash=f"md5-{filename}",
                                chunk_count=3, word_count=120, status="ready")
        db.add(doc)
        await db.commit()
        return {"status": "ready", "id": doc.id, "chunks": 3, "word_count": 120,
                "title": filename.rsplit(".", 1)[0]}

    async def _delete(db, doc):
        calls["delete"].append(doc.id)
        await db.delete(doc)
        await db.commit()

    async def _search(query, *, top_k, project_id=None, no_project_only=False):
        calls["search"].append({"query": query, "top_k": top_k,
                                "project_id": project_id,
                                "no_project_only": no_project_only})
        return {"rewritten": f"改写({query})", "keywords": ["检索", "知识库"],
                "results": [
                    {"content": "项目库命中片段", "noise_flag": "mild",
                     "rerank_score": 0.81234,
                     "meta": {"doc_id": 7, "filename": "笔记.md", "source": "project"}},
                    {"content": "公共语料命中片段",
                     "rrf_score": 0.05, "meta": {}},
                ]}

    monkeypatch.setattr("api.knowledge.router.ingest_document", _ingest)
    monkeypatch.setattr("api.knowledge.router.delete_document", _delete)
    monkeypatch.setattr("api.knowledge.router.rag_pipeline",
                        SimpleNamespace(search=_search))
    return calls


@pytest.fixture()
def app():
    test_app = FastAPI()
    test_app.include_router(auth_router)
    test_app.include_router(projects_router)
    test_app.include_router(knowledge_router)
    return test_app


@pytest.fixture()
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _register_login_create_project(client, username: str) -> tuple[str, int]:
    r = await client.post("/api/auth/register",
                          json={"username": username, "password": "secret1"})
    assert r.status_code == 200, r.text
    r = await client.post("/api/auth/login",
                          json={"username": username, "password": "secret1"})
    token = r.json()["access_token"]
    r = await client.post("/api/projects", json={"title": f"{username}的项目"},
                          headers={"Authorization": f"Bearer {token}"})
    return token, r.json()["id"]


async def _seed_doc(session_factory, project_id: int, user_id: int,
                    filename: str = "已有文档.txt") -> int:
    async with session_factory() as s:
        doc = KnowledgeDocument(project_id=project_id, user_id=user_id,
                                filename=filename, file_type="txt", size_bytes=10,
                                content_hash=f"md5-{filename}", chunk_count=2,
                                word_count=30, status="ready")
        s.add(doc)
        await s.commit()
        return doc.id


# ---------------- 鉴权与归属 ----------------

async def test_knowledge_requires_authentication(client):
    r = await client.post("/api/projects/1/knowledge", files=[("files", ("a.txt", b"x"))])
    assert r.status_code == 401
    r = await client.get("/api/projects/1/knowledge")
    assert r.status_code == 401


async def test_knowledge_ownership_enforced(client):
    _, alice_pid = await _register_login_create_project(client, "kb_alice")
    mallory_token, _ = await _register_login_create_project(client, "kb_mallory")
    h = {"Authorization": f"Bearer {mallory_token}"}
    r = await client.post(f"/api/projects/{alice_pid}/knowledge",
                          files=[("files", ("a.txt", b"x"))], headers=h)
    assert r.status_code == 404
    r = await client.get(f"/api/projects/{alice_pid}/knowledge", headers=h)
    assert r.status_code == 404


# ---------------- 上传：逐文件结果 + 失败截断 + 列表联动 ----------------

async def test_upload_mixed_results_then_list(client):
    token, pid = await _register_login_create_project(client, "kb_up")
    h = {"Authorization": f"Bearer {token}"}
    r = await client.post(f"/api/projects/{pid}/knowledge", headers=h, files=[
        ("files", ("笔记.md", "# 标题\n正文".encode(), "text/markdown")),
        ("files", ("boom.pdf", b"%PDF-1.4", "application/pdf")),
    ])
    assert r.status_code == 200
    body = r.json()
    assert body["project_id"] == pid and body["uploaded"] == 2 and body["ready"] == 1
    ok, failed = body["results"]
    assert ok["status"] == "ready" and ok["filename"] == "笔记.md"
    assert ok["chunks"] == 3 and ok["word_count"] == 120 and ok["id"] > 0
    assert failed["status"] == "failed" and failed["error"].startswith("解析失败")

    r = await client.get(f"/api/projects/{pid}/knowledge", headers=h)
    docs = r.json()["documents"]
    assert r.json()["count"] == 1
    assert docs[0]["filename"] == "笔记.md" and docs[0]["file_type"] == "md"
    assert docs[0]["status"] == "ready" and docs[0]["chunk_count"] == 3
    assert docs[0]["created_at"] is not None


async def test_upload_failure_error_truncated_to_200(client):
    token, pid = await _register_login_create_project(client, "kb_trunc")
    h = {"Authorization": f"Bearer {token}"}
    r = await client.post(f"/api/projects/{pid}/knowledge", headers=h, files=[
        ("files", ("boom.txt", b"x", "text/plain")),
    ])
    err = r.json()["results"][0]["error"]
    assert len(err) <= 200


# ---------------- 删除：跨项目 404 + 元数据清理 ----------------

async def test_delete_wrong_project_404_and_owner_deletes(client, session_factory):
    token, pid = await _register_login_create_project(client, "kb_del")
    user_id = 1  # kb_del 是本库首个用户
    doc_id = await _seed_doc(session_factory, pid, user_id)
    mallory_token, _ = await _register_login_create_project(client, "kb_del2")
    h_m = {"Authorization": f"Bearer {mallory_token}"}
    # mallory 用自己的项目 id 也删不到别人的文档（doc.project_id != project_id → 404）
    _, mallory_pid = 0, 0
    r = await client.get("/api/projects", headers=h_m)
    mallory_pid = r.json()[0]["id"]
    r = await client.delete(f"/api/projects/{mallory_pid}/knowledge/{doc_id}", headers=h_m)
    assert r.status_code == 404

    h = {"Authorization": f"Bearer {token}"}
    r = await client.delete(f"/api/projects/{pid}/knowledge/{doc_id}", headers=h)
    assert r.status_code == 200 and r.json() == {"deleted": doc_id}
    async with session_factory() as s:
        assert (await s.get(KnowledgeDocument, doc_id)) is None
    r = await client.delete(f"/api/projects/{pid}/knowledge/{doc_id}", headers=h)
    assert r.status_code == 404


# ---------------- 库内检索：空库短路 / 结果映射 / builtin 过滤 ----------------

async def test_search_empty_project_kb_short_circuits(client, _fake_vector_services):
    token, pid = await _register_login_create_project(client, "kb_empty")
    h = {"Authorization": f"Bearer {token}"}
    r = await client.post(f"/api/projects/{pid}/knowledge/search",
                          json={"query": "怎么写综述", "mode": "project"}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["results"] == [] and body["rewritten"] == "怎么写综述"
    assert _fake_vector_services["search"] == []       # 未触检索管线


async def test_search_maps_hits_and_passes_mode(client, session_factory, _fake_vector_services):
    token, pid = await _register_login_create_project(client, "kb_search")
    await _seed_doc(session_factory, pid, 1)           # 库非空，mode=project 不会短路
    h = {"Authorization": f"Bearer {token}"}
    r = await client.post(f"/api/projects/{pid}/knowledge/search",
                          json={"query": "三线表怎么调", "top_k": 3, "mode": "project"},
                          headers=h)
    assert r.status_code == 200
    assert _fake_vector_services["search"] == [{
        "query": "三线表怎么调", "top_k": 3, "project_id": pid,
        "no_project_only": True,                       # mode=project 透传为仅库内
    }]
    hit = r.json()["results"][0]
    assert hit["doc_id"] == 7 and hit["filename"] == "笔记.md"
    assert hit["score"] == 0.8123                      # rerank_score 优先且保留 4 位
    assert hit["noise_flag"] == "mild"


async def test_search_builtin_mode_filters_project_hits(client):
    token, pid = await _register_login_create_project(client, "kb_builtin")
    h = {"Authorization": f"Bearer {token}"}
    r = await client.post(f"/api/projects/{pid}/knowledge/search",
                          json={"query": "选题", "mode": "builtin"}, headers=h)
    results = r.json()["results"]
    assert [x["content"] for x in results] == ["公共语料命中片段"]
    assert results[0]["doc_id"] is None and results[0]["score"] == 0.05  # rrf 兜底
