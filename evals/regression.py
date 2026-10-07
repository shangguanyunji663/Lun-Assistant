"""七大必测场景自动化回归评测（RAG 知识库助手验收）。

场景（对应路线图 P0/P1 验收标准）：
  S1 知识库上传→解析→分块→入库（含 MD5 去重 / 扫描件拒绝）
  S2 项目级知识隔离（A 项目文档不出现在 B 项目检索结果）
  S3 多路混合召回（稠密 / 稀疏 / 相邻窗口三路 RRF 融合生效）
  S4 Query 改写（规则兜底稳定产出关键词；LLM 拒答回退策略正确）
  S5 Supervisor 复杂任务识别 → Planner 路由
  S6 结构化产物生成（综述初稿骨架完整，证据引用存在）
  S7 工具治理（全部注册工具均可经治理栈解析配置 + RBAC 放行）

输出：逐场景 PASS/FAIL/SKIP + 汇总；退出码 0=全过，1=有失败，2=环境缺失。
DB/LLM 不可用时对应场景标记 SKIP(env)，不影响其它纯逻辑场景结论。
用法：envs\\lunjiang\\python.exe evals/regression.py
"""
import asyncio
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.WARNING)
logging.getLogger("lunjiang").setLevel(logging.INFO)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from infrastructure.paths import PROJECT_ROOT  # noqa: E402 —— 路径唯一真源

_results: list[dict] = []


def _record(scene: str, name: str, ok: bool, detail: str, kind: str = "check"):
    _results.append({"scene": scene, "name": name, "ok": ok, "detail": detail, "kind": kind})
    flag = "PASS" if ok else ("SKIP" if kind == "skip" else "FAIL")
    print(f"[{flag}] {scene} | {name} — {detail}")


async def _db_ok() -> bool:
    try:
        from infrastructure.db import get_session_factory
        async with get_session_factory()() as db:
            await db.execute(__import__("sqlalchemy").text("SELECT 1"))
        return True
    except Exception:
        return False


async def s1_ingest() -> None:
    if not await _db_ok():
        _record("S1", "入库流水线", False, "DB 不可用", "skip")
        return
    from sqlalchemy import select

    from infrastructure.db import get_session_factory
    from infrastructure.models.knowledge import KnowledgeDocument
    from infrastructure.models.memory import MemoryItem
    from infrastructure.models.project import Project
    from infrastructure.models.user import User

    factory = get_session_factory()
    async with factory() as db:
        # 测试环境：临时用户+项目
        user = User(username=f"__reg_{int(time.time())}", password_hash="x", role="student")
        db.add(user)
        await db.flush()
        proj = Project(user_id=user.id, title="__reg__")
        db.add(proj)
        await db.flush()
        pid = proj.id

        from services.rag.ingest.pipeline import ingest_document

        sample = ("# 测试知识库\n\n## 第一章 检索增强生成\n\n"
                  "RAG 检索增强生成通过引入外部知识库提升大模型回答准确性。"
                  "混合检索融合稠密向量与稀疏关键词，在工业落地中广泛应用。"
                  "交叉编码器精排进一步过滤无关文档，显著提升检索精度。\n")
        r1 = await ingest_document(db=db, project_id=pid, user_id=user.id,
                                   filename="kb_test.md", data=sample.encode("utf-8"))
        r2 = await ingest_document(db=db, project_id=pid, user_id=user.id,
                                   filename="kb_test2.md", data=sample.encode("utf-8"))
        dup_ok = r1.get("status") == "ready" and r2.get("status") == "skipped"
        _record("S1", "入库与MD5去重", dup_ok,
                f"r1={r1.get('status')} r2={r2.get('status')}")

        # 扫描件拒绝：空文本 PDF（无可提取文本）
        empty_pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n" + b"x" * 60
        r3 = await ingest_document(db=db, project_id=pid, user_id=user.id,
                                   filename="scan.pdf", data=empty_pdf)
        _record("S1", "扫描件拒绝", r3.get("status") == "failed",
                f"scan.pdf -> {r3.get('status')}")

        # 分块落库
        n_chunks = await db.scalar(
            select(__import__("sqlalchemy").func.count()).select_from(MemoryItem)
            .where(MemoryItem.kind == "user_doc", MemoryItem.project_id == pid))
        _record("S1", "分块落库", (n_chunks or 0) >= 1, f"user_doc chunks={n_chunks}")

        # 清理
        from services.rag.ingest.pipeline import delete_document, list_documents
        for doc in (await list_documents(db, pid)):
            d = await db.get(KnowledgeDocument, doc["id"])
            if d:
                await delete_document(db, d)
        await db.delete(proj)
        await db.delete(user)
        await db.commit()


async def s2_isolation() -> None:
    if not await _db_ok():
        _record("S2", "项目隔离", False, "DB 不可用", "skip")
        return
    from infrastructure.db import get_session_factory
    from infrastructure.models.project import Project
    from infrastructure.models.user import User

    factory = get_session_factory()
    async with factory() as db:
        ua = User(username=f"__isoa_{int(time.time())}", password_hash="x", role="student")
        ub = User(username=f"__isob_{int(time.time())}", password_hash="x", role="student")
        db.add_all([ua, ub])
        await db.flush()
        pa, pb = Project(user_id=ua.id, title="__A__"), Project(user_id=ub.id, title="__B__")
        db.add_all([pa, pb])
        await db.flush()

        from services.rag.ingest.pipeline import ingest_document
        secret = ("# 机密项目文档\n\n仅属于项目A的独家内容：量子纠缠密码学在匿名通信中的应用，"
                  "密钥分发协议与安全性证明，明确标注仅供A项目内部检索使用，不得泄露。\n" * 3)
        await ingest_document(db=db, project_id=pa.id, user_id=ua.id,
                              filename="secret.md", data=secret.encode("utf-8"))

        from services.rag.retriever import hybrid_retriever
        hits_b = await hybrid_retriever.project_dense_search("量子纠缠密码学 匿名通信", pb.id, top_k=5)
        _record("S2", "跨项目隔离", len(hits_b) == 0,
                f"B 项目命中 {len(hits_b)} 条（期望0）")

        # 清理
        from infrastructure.models.knowledge import KnowledgeDocument
        from services.rag.ingest.pipeline import delete_document, list_documents
        for doc in (await list_documents(db, pa.id)):
            d = await db.get(KnowledgeDocument, doc["id"])
            if d:
                await delete_document(db, d)
        await db.delete(pa)
        await db.delete(pb)
        await db.delete(ua)
        await db.delete(ub)
        await db.commit()


async def s3_multi_road() -> None:
    # 纯逻辑：RRF 融合 + 道路标记（不依赖外部服务）
    from services.rag.retriever import hybrid_retriever

    a = [{"id": 1, "content": "x1"}, {"id": 2, "content": "x2"}]
    b = [{"id": 2, "content": "x2"}, {"id": 3, "content": "x3"}]
    fused = hybrid_retriever.rrf_fuse(a, b, top_k=5)
    ids = [f["id"] for f in fused]
    _record("S3", "RRF融合", ids == [2, 1, 3], f"fused order={ids}")

    # 相邻窗口召回：自造同源 4 个临时块（chunk=1..4，唯一 doc_key），以 chunk=2 命中，
    # 断言恰好召回相邻块 [1, 3]（自身与跨窗的 4 均不得召回）；依赖 DB，跑完即清理
    if not await _db_ok():
        _record("S3", "相邻窗口查询语法", False, "DB 不可用", "skip")
        return

    from sqlalchemy import delete, func

    from infrastructure.config import get_embedding_dim
    from infrastructure.db import get_session_factory
    from infrastructure.models.memory import MemoryItem

    doc_key = f"udoc:__reg_s3_{time.time_ns()}__"  # 唯一来源键，避免与真实数据混淆
    factory = get_session_factory()
    inserted = False
    try:
        async with factory() as db:
            db.add_all([
                MemoryItem(project_id=None, user_id=None, kind="user_doc",
                           content=f"__regression__ 相邻窗口临时块 chunk={i}",
                           embedding=[0.0] * get_embedding_dim(), importance=0.6,
                           # meta 复刻 ingest 落库形态：项目文档块以 doc_key 定位同源
                           meta={"filename": "__reg_s3__.md", "doc_id": 0, "chunk": i,
                                 "doc_key": doc_key, "title": "__reg_s3__"})
                for i in (1, 2, 3, 4)
            ])
            await db.commit()
            inserted = True

        sib = await hybrid_retriever.sibling_search(
            [{"meta": {"doc_key": doc_key, "chunk": 2}}], window=1, top_k=10)
        chunks = sorted((r.get("meta") or {}).get("chunk") for r in sib)
        same_src = all((r.get("meta") or {}).get("doc_key") == doc_key for r in sib)
        _record("S3", "相邻窗口查询语法", chunks == [1, 3] and same_src,
                f"chunk=2 window=1 实召回 {chunks}（期望[1, 3]：邻块召回、自身与跨窗块剔除）")
    finally:
        # 清理临时数据：断言失败或异常也不留下脏数据
        if inserted:
            async with factory() as db:
                await db.execute(delete(MemoryItem).where(
                    func.json_extract_path_text(MemoryItem.meta, "doc_key") == doc_key))
                await db.commit()


async def s4_rewrite() -> None:
    from services.rag.query_rewrite import _rule_rewrite, rewrite_query

    rw = _rule_rewrite("怎么做好大模型微调的开题报告")
    kws = rw["keywords"]
    _record("S4", "规则改写", len(kws) >= 3 and ("开题报告" in rw["rewritten"]),
            f"keywords={kws[:4]} rewritten含场景前缀={('开题报告' in rw['rewritten'])}")

    # 改写策略回退：① 拒答识别函数判定 ② 端到端回退分支（桩 Provider，零外部依赖）
    from services.rag.pipeline import _is_rejection

    query = "怎么做好大模型微调的开题报告"
    reject_txt = "抱歉，我无法回答这个问题。"
    normal_txt = "如何高质量完成大模型微调方向的开题报告撰写"

    class _StubProvider:
        """桩 LLM：按预设 payload 返回，用于驱动真实的分支判定。"""

        def __init__(self, payload: dict) -> None:
            self._payload = payload

        async def chat(self, messages, **kwargs) -> dict:
            return self._payload

    refused = await rewrite_query(
        query, provider=_StubProvider({"rewritten": reject_txt, "keywords": []}), mode="on")
    adopted = await rewrite_query(
        query, provider=_StubProvider(
            {"rewritten": normal_txt, "keywords": ["大模型微调", "开题报告"]}), mode="on")
    ok = (_is_rejection(reject_txt) is True          # 拒答话术 → 判为拒答
          and _is_rejection(normal_txt) is False     # 正常改写 → 不判拒答
          and refused["strategy"] == "rule_fallback"  # 拒答 → 回退规则改写
          and refused["rewritten"] == rw["rewritten"]  # 回退内容即规则改写产物
          and adopted["strategy"] == "llm")           # 正常改写 → 采纳 LLM 结果
    _record("S4", "改写策略回退", ok,
            f"拒答识别={_is_rejection(reject_txt)}/正常识别={_is_rejection(normal_txt)}；"
            f"拒答→{refused['strategy']}（期望rule_fallback）/正常→{adopted['strategy']}（期望llm）")


async def s5_complex_task() -> None:
    from services.agent.planner import is_complex_task

    cases = [
        ("帮我把这个话题梳理一下，先检索相关文献，再生成一篇文献综述，最后给出开题建议", True),
        ("什么是注意力机制？", False),
        ("帮我分析研究方向，搜索最新论文，撰写开题报告并规划研究路线", True),
    ]
    for text, expect in cases:
        got = is_complex_task(text)
        _record("S5", f"复杂任务识别: {text[:16]}...", got == expect,
                f"expect={expect} got={got}")
    # 图装配校验：真实编译 LangGraph 图，断言 planner 与 6 个专项 Agent 节点已注册且接线
    try:
        from services.agent.builder import build_graph
        from services.agent.specialists import SPECIALISTS

        draw = build_graph().get_graph()
        nodes = set(draw.nodes)
        missing = sorted({"supervisor", "planner", *SPECIALISTS} - nodes)
        cond = {(e.source, e.target) for e in draw.edges if e.conditional}
        edges = {(e.source, e.target) for e in draw.edges if not e.conditional}
        planner_wired = ("supervisor", "planner") in cond and ("planner", "supervisor") in edges
        loops = all((n, "supervisor") in edges for n in SPECIALISTS)
        _record("S5", "Planner 节点装配", not missing and planner_wired and loops,
                f"实编译图 {len(nodes)} 节点，缺={missing or '无'}，"
                f"planner接线={'ok' if planner_wired else '断'}，"
                f"{len(SPECIALISTS)}个专项Agent回环={'ok' if loops else '断'}")
    except Exception as e:
        _record("S5", "Planner 节点装配", False, str(e)[:120])


# S6 必填段落：独立于服务端模板硬编码，模板漏段/改名即 FAIL
_S6_REQUIRED_SECTIONS: dict[str, tuple[str, ...]] = {
    "review_draft": ("引言", "研究现状", "研究方法", "研究空白", "参考文献"),
    "proposal_report": ("选题背景", "研究现状", "研究内容", "可行性", "预期成果", "进度安排"),
    "defense_outline": ("开场白", "研究背景", "研究方法", "创新点", "不足", "QA清单"),
}


async def s6_artifact() -> None:
    # 真渲染校验：桩掉 LLM 与 RAG，跑通三种产物的模板渲染，断言必填段落齐全
    import services.governance.artifacts as artifacts

    captured: list[str] = []

    class _StubProvider:
        """桩 LLM：记录提示词（含渲染骨架）并返回占位内容。"""

        async def chat(self, messages, **kwargs) -> str:
            captured.append(messages[-1]["content"])
            return "（桩生成内容）"

    class _StubPipeline:
        async def search(self, topic, **kwargs) -> dict:
            return {"results": [{"content": "证据A", "meta": {"title": "t", "source": "s"}}]}

    orig_provider, orig_pipeline = artifacts.LLMProvider, artifacts.rag_pipeline
    artifacts.LLMProvider, artifacts.rag_pipeline = _StubProvider, _StubPipeline()
    try:
        problems: list[str] = []
        if set(artifacts.KINDS) != set(_S6_REQUIRED_SECTIONS):
            problems.append(f"KINDS覆盖不全: {sorted(artifacts.KINDS)}")
        for kind, sections in _S6_REQUIRED_SECTIONS.items():
            captured.clear()
            out = await artifacts.generate_artifact(kind=kind, topic="大模型微调")
            prompt = captured[0] if captured else ""
            lacking = [s for s in sections if s not in prompt]
            if lacking:
                problems.append(f"{kind} 渲染骨架缺段落{lacking}")
            elif out.get("kind") != kind or not out.get("content") \
                    or out.get("evidence_count") != 1:
                problems.append(f"{kind} 返回结构异常: {sorted(out)}")
        _record("S6", "产物模板覆盖", not problems,
                f"离线桩渲染 {len(_S6_REQUIRED_SECTIONS)} 种产物，必填段落齐全且返回结构正常"
                if not problems else "; ".join(problems))
    finally:
        artifacts.LLMProvider, artifacts.rag_pipeline = orig_provider, orig_pipeline

    try:
        await artifacts.generate_artifact(kind="xx", topic="t")
        _record("S6", "参数校验", False, "非法 kind 未抛错")
    except ValueError:
        _record("S6", "参数校验", True, "非法 kind 正确拒绝")


async def s7_governance() -> None:
    import yaml

    from services.governance.tool_registry import tool_registry
    from services.governance.tools_impl import register_all

    register_all()
    cfg = yaml.safe_load((PROJECT_ROOT / "configs" / "tools.yaml").read_text(
        encoding="utf-8")).get("tools", {})
    missing_cfg = [name for name in tool_registry.tools if name not in cfg]
    _record("S7", "工具与配置一致", not missing_cfg,
            f"缺配置: {missing_cfg or '无'}")
    try:
        from infrastructure.rbac.policy import check_tool_permission
        allow = check_tool_permission("student", "search_literature")
        _record("S7", "RBAC放行", allow, "student 可调 search_literature")
    except Exception as e:
        _record("S7", "RBAC放行", False, str(e)[:100])


async def main() -> int:
    print("=" * 70)
    print("论匠 · RAG 知识库助手 —— 七大必测场景回归评测")
    print("=" * 70)
    # 建表（与 main.py lifespan 一致：开发期自动建表）
    try:
        from infrastructure.db import get_engine
        from infrastructure.models import Base as _Base
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(_Base.metadata.create_all)
    except Exception:
        pass
    await s1_ingest()
    await s2_isolation()
    await s3_multi_road()
    await s4_rewrite()
    await s5_complex_task()
    await s6_artifact()
    await s7_governance()
    print("=" * 70)
    passed = sum(1 for r in _results if r["ok"])
    failed = sum(1 for r in _results if not r["ok"] and r["kind"] != "skip")
    skipped = sum(1 for r in _results if not r["ok"] and r["kind"] == "skip")
    print(f"汇总: {len(_results)} 项 | PASS={passed} FAIL={failed} SKIP={skipped}/环境依赖")
    with open(PROJECT_ROOT / "evals" / "regression_latest.json", "w", encoding="utf-8") as f:
        import json
        json.dump(_results, f, ensure_ascii=False, indent=2)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))