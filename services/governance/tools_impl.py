"""业务工具实现：6 类论文工具（经 ToolRegistry 治理后供 Agent 调用）。"""
import re

from services.llm.provider import LLMProvider
from services.governance.tool_registry import ToolSpec, tool_registry


# ---------------- 文献检索 ----------------
async def search_literature(query: str, top_k: int = 5):
    from services.rag.pipeline import rag_pipeline
    try:
        top_k = int(top_k or 5)
    except (TypeError, ValueError):
        top_k = 5
    top_k = max(1, min(top_k, 20))  # 收敛到合法窗口，防字符串/越界
    out = await rag_pipeline.search(query, top_k=top_k)
    return {
        "query": out["rewritten"],
        "results": [
            {"title": (r.get("meta") or {}).get("title", "未知"),
             "source": (r.get("meta") or {}).get("source", ""),
             "content": r["content"][:300], "score": round(r.get("rerank_score", r.get("rrf_score", 0)), 4)}
            for r in out["results"]
        ],
    }


# ---------------- 选题分析 ----------------
async def topic_analysis(major: str, interest: str, requirement: str = ""):
    provider = LLMProvider()
    prompt = (
        f"专业: {major}\n兴趣方向: {interest}\n论文要求: {requirement or '本科毕业论文'}\n\n"
        "请给出3个可行的毕业论文选题，每个含: 题目/研究问题/可行性分析/创新点/风险。"
        "用markdown列表输出。"
    )
    return await provider.chat([{"role": "user", "content": prompt}], max_tokens=1200)


# ---------------- 论文写作 ----------------
async def generate_section(section: str, outline: str = "", references: str = "",
                           preferences: str = ""):
    provider = LLMProvider()
    prompt = (
        f"你是学术论文写作助手。撰写章节: {section}\n"
        f"{'大纲: ' + outline + chr(10) if outline else ''}"
        f"{'可用参考文献: ' + references + chr(10) if references else ''}"
        f"{'写作偏好: ' + preferences + chr(10) if preferences else ''}\n"
        "要求: 学术语言、逻辑连贯、直接输出正文内容。"
    )
    return await provider.chat([{"role": "user", "content": prompt}], max_tokens=2000)


# ---------------- 格式校验 ----------------
async def check_format(text: str, strict: bool = True):
    """规则 + LLM 双通道格式校验。"""
    issues = []
    paragraphs = [p for p in text.split("\n") if p.strip()]
    # 规则通道
    if len(text) < 200:
        issues.append("正文过短（<200字），不符合论文章节基本要求")
    if not re.search(r"摘\s*要", text):
        issues.append("缺少摘要部分")
    if not re.search(r"参考文献|References", text, re.I):
        issues.append("缺少参考文献部分")
    long_paras = [p for p in paragraphs if len(p) > 800]
    if long_paras:
        issues.append(f"{len(long_paras)}个段落超过800字，建议拆分")
    if re.search(r"[，。]{3,}|,{4,}", text):
        issues.append("存在连续标点，疑似占位符未清理")
    # LLM 通道
    provider = LLMProvider()
    llm_review = await provider.chat(
        [{"role": "system", "content": "你是论文格式审查专家。检查结构完整性/标题层级/语言规范，"
                                       "输出markdown列表，若无问题输出'格式检查通过'。"},
         {"role": "user", "content": text[:3000]}],
        temperature=0.2, max_tokens=600)
    return {"rule_issues": issues, "llm_review": llm_review,
            "strict": strict, "pass": not issues and "通过" in llm_review}


# ---------------- 查重降重 ----------------
async def check_plagiarism(text: str, granularity: str = "paragraph"):
    """与本地语料库比对估算重复率（dense+bm25 双路相似度）。"""
    from services.rag.retriever import hybrid_retriever
    paragraphs = [p.strip() for p in re.split(r"[\n。]", text) if len(p.strip()) > 30]
    if not paragraphs:
        return {"estimated_rate": 0.0, "matched": []}
    total_sim, matched = 0.0, []
    for para in paragraphs:
        dense = await hybrid_retriever.dense_search(para, top_k=3)
        sparse = await hybrid_retriever.sparse_search(para, top_k=3)
        best = 0.0
        for cand in dense + sparse:
            sim = _char_sim(para, cand["content"])
            best = max(best, sim)
        total_sim += best
        if best > 0.45:
            src = (dense[0].get("meta") or {}).get("title", "") if dense else ""
            matched.append({"fragment": para[:80], "similarity": round(best, 3),
                            "likely_source": src})
    return {"estimated_rate": round(total_sim / len(paragraphs), 3),
            "matched": matched, "paragraphs": len(paragraphs)}


def _char_sim(a: str, b: str) -> float:
    """字符 bigram Jaccard 相似度（轻量，避免额外模型）。"""
    def grams(s):
        return {s[i:i + 2] for i in range(len(s) - 1)}
    ga, gb = grams(a), grams(b[:1000])
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / len(ga | gb)


# ---------------- AI 检测 ----------------
_AI_SYSTEM = (
    "你是AI生成文本检测器。判断文本的AI写作痕迹，输出JSON: "
    "{\"ai_probability\": 0.xx, \"signals\": [\"信号1\", ...], "
    "\"humanize_suggestions\": [\"具体改写建议\"]}"
)


async def detect_ai_text(text: str, mode: str = "standard"):
    provider = LLMProvider()
    # 启发式信号: 句长方差小 + 高频AI词
    sentences = [s for s in re.split(r"[。！？]", text) if len(s.strip()) > 5]
    lens = [len(s) for s in sentences] or [0]
    mean_len = sum(lens) / len(lens)
    var = sum((x - mean_len) ** 2 for x in lens) / len(lens)
    ai_words = ["首先", "其次", "总之", "综上所述", "值得注意的是", "在很大程度上", "赋能", "闭环"]
    hits = sum(text.count(w) for w in ai_words)
    heuristic = min(1.0, (hits / max(1, len(sentences))) * 0.6 + (0.3 if var < 80 else 0))
    llm_out = await provider.chat(
        [{"role": "system", "content": _AI_SYSTEM},
         {"role": "user", "content": text[:2500]}],
        json_mode=True, temperature=0.1, max_tokens=400)
    llm_prob = float(llm_out.get("ai_probability", 0.5))
    return {"ai_probability": round(0.4 * heuristic + 0.6 * llm_prob, 3),
            "heuristic_signals": {"sentence_len_variance": round(var, 1),
                                  "ai_word_hits": hits},
            "llm": llm_out}


# ---------------- Query 改写 ----------------
async def rewrite_query(query: str):
    from services.rag.query_rewrite import rewrite_query as _rw
    return await _rw(query)


# ---------------- 结构化产物生成 ----------------
async def generate_artifact(kind: str, topic: str, requirement: str = "",
                            references: str = "", project_id: int | None = None):
    """综述初稿 / 开题报告 / 答辩大纲（证据检索 + 模板生成，见 services/agent/artifacts.py）。"""
    from services.agent.artifacts import generate_artifact as _gen
    return await _gen(kind=kind, topic=topic, requirement=requirement,
                      references=references, project_id=project_id)


# ---------------- P2 学术工具生态（6类）----------------
def _register_academic() -> None:
    """学术翻译/润色/方法推荐/参考文献格式化/摘要生成/术语解析。"""
    from services.governance import academic_tools as at

    tool_registry.register(ToolSpec(
        name="translate_academic", description="学术翻译(中英互译)", handler=at.translate_academic))
    tool_registry.register(ToolSpec(
        name="polish_academic", description="学术润色", handler=at.polish_academic))
    tool_registry.register(ToolSpec(
        name="recommend_method", description="研究方法推荐", handler=at.recommend_method))
    tool_registry.register(ToolSpec(
        name="format_reference", description="参考文献格式化(GB/T 7714/APA)",
        handler=at.format_reference))
    tool_registry.register(ToolSpec(
        name="generate_abstract", description="论文摘要生成", handler=at.generate_abstract))
    tool_registry.register(ToolSpec(
        name="term_explain", description="学术术语解析", handler=at.term_explain))


# ---------------- 注册 ----------------
def register_all() -> None:
    tool_registry.register(ToolSpec(
        name="search_literature", description="三阶段RAG文献检索",
        handler=search_literature))
    tool_registry.register(ToolSpec(
        name="rewrite_query", description="检索Query改写", handler=rewrite_query))
    tool_registry.register(ToolSpec(
        name="topic_analysis", description="选题分析生成", handler=topic_analysis))
    tool_registry.register(ToolSpec(
        name="generate_section", description="论文章节写作", handler=generate_section))
    tool_registry.register(ToolSpec(
        name="check_format", description="论文格式校验", handler=check_format))
    tool_registry.register(ToolSpec(
        name="check_plagiarism", description="查重估算", handler=check_plagiarism))
    tool_registry.register(ToolSpec(
        name="detect_ai_text", description="AI痕迹检测", handler=detect_ai_text))
    tool_registry.register(ToolSpec(
        name="generate_artifact", description="结构化产物生成(综述初稿/开题报告/答辩大纲)",
        handler=generate_artifact))
    _register_academic()
