"""结构化产物生成：文献综述初稿 / 开题报告 / 答辩大纲。

设计：
- 每种产物一套模板（骨架固定，保证结构完整、评委友好）；
- 生成前自动检索证据（公共语料 + 可选项目知识库），把 Evidence 注入提示词，
  避免 LLM 空泛编造；
- 产物以 Markdown 输出，可直接落盘/复制；
- 注册为治理工具 "generate_artifact"，供 Planner 步骤与专项 Agent 调用。
"""
from services.llm.provider import LLMProvider
from services.rag.pipeline import rag_pipeline

# 产物模板：标题 + 章节骨架（中文占位符由 LLM 填充）
_ARTIFACT_TEMPLATES: dict[str, dict] = {
    "review_draft": {
        "name": "文献综述初稿",
        "outline": [
            "一、引言（综述范围与检索策略）",
            "二、国内外研究现状（按主题聚类，条目式引用[证据编号]）",
            "三、研究方法与技术路线概述",
            "四、研究空白与本文切入点",
            "五、参考文献（按出现顺序编号）",
        ],
        "instruction": (
            "基于检索证据撰写中文文献综述初稿，要求：\n"
            "1. 每个主体节至少3个主题段落，每段引用对应证据编号；\n"
            "2. 突出研究脉络与争议点；\n"
            "3. 全文600字/节左右，学术语言。"
        ),
    },
    "proposal_report": {
        "name": "开题报告",
        "outline": [
            "一、选题背景与研究意义",
            "二、国内外研究现状",
            "三、研究内容与技术路线",
            "四、可行性分析",
            "五、预期成果与创新点",
            "六、研究进度安排（甘特式分阶段）",
        ],
        "instruction": (
            "基于检索证据撰写开题报告，要求：\n"
            "1. 研究内容可分解为3-4个子任务并给出技术路线；\n"
            "2. 可行性从数据/方法/环境三方面论证；\n"
            "3. 进度安排精确到月；\n"
            "4. 每节200-400字，学术语言。"
        ),
    },
    "defense_outline": {
        "name": "答辩大纲",
        "outline": [
            "一、开场白（自我介绍+题目）",
            "二、研究背景与问题提出",
            "三、研究方法与主要工作",
            "四、核心结果与创新点",
            "五、存在不足与展望",
            "六、评委高频提问准备（QA清单≥8条，含参考回答要点）",
        ],
        "instruction": (
            "基于检索证据生成答辩提纲，要求：\n"
            "1. 每节给出要点条目与时长建议（总时长10-12分钟）；\n"
            "2. QA清单针对该主题预测评委会问什么；\n"
            "3. 输出可直接排练的提纲，学术语言。"
        ),
    },
}

KINDS = tuple(_ARTIFACT_TEMPLATES)


async def generate_artifact(kind: str, topic: str, *, requirement: str = "",
                            references: str = "", project_id: int | None = None) -> dict:
    """生成结构化产物。kind ∈ review_draft / proposal_report / defense_outline。

    流程：证据检索(RAG) → 模板+证据组装 → LLM 生成 Markdown。
    """
    if kind not in _ARTIFACT_TEMPLATES:
        raise ValueError(f"不支持的产物类型: {kind}，可选: {KINDS}")
    tmpl = _ARTIFACT_TEMPLATES[kind]

    # 1. 证据检索：公共语料 + 可选项目知识库
    out = await rag_pipeline.search(topic, top_k=6, project_id=project_id)
    evidence = "\n".join(
        f"[{i}] (来源: {(r.get('meta') or {}).get('title') or '未知'}) "
        f"{r['content'][:260]}"
        for i, r in enumerate(out["results"], 1)
    ) or "(未检索到直接证据，请基于常识与用户提供资料撰写并提示核实)"

    # 2. LLM 生成
    prompt = (
        f"请生成《{tmpl['name']}》\n"
        f"研究主题: {topic}\n"
        f"{'论文要求: ' + requirement if requirement else ''}\n"
        f"{'用户提供参考文献: ' + references if references else ''}\n\n"
        f"【章节骨架（必须完整覆盖）】\n" + "\n".join(tmpl["outline"]) + "\n\n"
        f"【检索证据（引用请标注[编号]）】\n{evidence}\n\n"
        f"【生成要求】\n{tmpl['instruction']}"
    )
    provider = LLMProvider()
    content = await provider.chat([{"role": "user", "content": prompt}], max_tokens=2500)

    return {
        "kind": kind, "artifact_name": tmpl["name"], "topic": topic,
        "content": content,
        "evidence_count": len(out["results"]),
        "sources": [
            {"title": (r.get("meta") or {}).get("title", ""),
             "source": (r.get("meta") or {}).get("source", "")}
            for r in out["results"][:6]
        ],
    }