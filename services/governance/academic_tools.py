"""P2 学术工具生态：6 类企业级论文辅助工具（统一经 ToolRegistry 治理）。

1.  translate_academic  学术翻译（中↔英，术语保持）
2.  polish_academic     学术润色（正式/简洁风格）
3.  recommend_method    研究方法推荐（RAG 证据 + LLM 决策）
4.  format_reference    参考文献格式化（GB/T 7714 / APA 规则引擎，同步工具）
5.  generate_abstract   摘要生成（结构化：目的/方法/结果/结论）
6.  term_explain        术语解析（RAG 检索 + LLM 人话解释）

设计约束：
- 纯 LLM 工具限长输入（截断至 4000 字），避免 OOM/超时；
- 规则工具（format_reference）零外部依赖，离线可用；
- 所有工具有默认参数，满足 tools.yaml 降级路径。
"""
from services.llm.provider import LLMProvider
from services.rag.pipeline import rag_pipeline

# ---------------- 参考文献格式模板（规则引擎，离线可用） ----------------
_GB7714 = "{authors}.{title}[J].{journal},{year},{volume}({issue}):{pages}."
_APA = "{authors} ({year}). {title}. {journal}, {volume}({issue}), {pages}."
_STYLE_TMPL = {"gb7714": _GB7714, "apa": _APA}

# 各风格缺失字段的占位值
_PLACEHOLDER = {
    "gb7714": {"authors": "佚名", "title": "(未命名文献)", "journal": "佚刊",
               "year": "无年份", "volume": "—", "issue": "—", "pages": "—"},
    "apa": {"authors": "Anonymous", "title": "Untitled", "journal": "Unknown Journal",
            "year": "n.d.", "volume": "—", "issue": "—", "pages": "—"},
}


def format_reference(authors: str = "", title: str = "", journal: str = "",
                     year: str = "", volume: str = "", issue: str = "",
                     pages: str = "", style: str = "gb7714"):
    """规则化参考文献格式化（GB/T 7714 / APA），缺失字段用占位值。"""
    style = (style or "").lower().strip()
    if style not in _STYLE_TMPL:
        return f"不支持的格式: {style}，可选 {list(_STYLE_TMPL)}"
    values = {"authors": authors, "title": title, "journal": journal,
              "year": year, "volume": volume, "issue": issue, "pages": pages}
    if style == "gb7714":
        values["authors"] = values["authors"].replace("；", ",")
    else:
        values["authors"] = values["authors"].replace("，", " & ")
    ph = _PLACEHOLDER[style]
    out = _STYLE_TMPL[style]
    for key, raw in values.items():
        out = out.replace("{" + key + "}", raw.strip() or ph[key])
    return out


# ---------------- 1. 学术翻译 ----------------
async def translate_academic(text: str = "", target: str = "en"):
    if not text:
        return "缺少待翻译文本"
    direction = "中译英" if target.lower() == "en" else "英译中"
    prompt = (f"请对以下学术文本进行{direction}，要求：\n"
              "1. 术语使用学界规范译法，人名/机构保留原文；\n"
              "2. 保持学术严谨，句式通顺；\n"
              "3. 直接输出译文。\n\n" + text[:4000])
    return await LLMProvider().chat([{"role": "user", "content": prompt}], max_tokens=1500)


# ---------------- 2. 学术润色 ----------------
async def polish_academic(text: str = "", style: str = "formal"):
    if not text:
        return "缺少待润色文本"
    style_hint = {"formal": "正式学术风格", "concise": "简洁凝练风格",
                  "plain": "平实易懂风格"}.get(style, "正式学术风格")
    prompt = (f"请对以下段落进行学术润色（{style_hint}），要求：\n"
              "1. 修正语法、标点与冗余表达；\n"
              "2. 术语规范统一；\n"
              "3. 保留原意与结构，直接输出润色后文本；\n"
              "4. 若文本过短或无需修改，说明原因。\n\n" + text[:4000])
    return await LLMProvider().chat([{"role": "user", "content": prompt}], max_tokens=1500)


# ---------------- 3. 研究方法推荐 ----------------
async def recommend_method(question: str = ""):
    if not question:
        return "请描述你的研究问题（如变量/数据形态/验证目标）"
    out = await rag_pipeline.search(question, top_k=4)
    evidence = "\n".join(
        f"[{i}] {(r.get('meta') or {}).get('title', '')}"
        for i, r in enumerate(out["results"], 1)) or "(无直接证据)"
    prompt = (
        "你是研究方法论顾问。针对研究问题推荐 2-3 种可行方法，"
        "每种包含：方法名称 / 适用条件 / 数据要求 / 局限。"
        "结合检索到的相关知识领域作为依据。\n\n"
        f"研究问题：{question[:800]}\n相关领域线索：{evidence}\n"
        "用 Markdown 列表输出。")
    return await LLMProvider().chat([{"role": "user", "content": prompt}], max_tokens=1200)


# ---------------- 5. 摘要生成 ----------------
async def generate_abstract(topic: str = "", keywords: str = "",
                            length: int = 200, focus: str = ""):
    if not topic:
        return "请提供论文主题"
    out = await rag_pipeline.search(topic, top_k=4)
    evidence = "\n".join(
        f"[{i}] {(r.get('meta') or {}).get('title', '')}：{r['content'][:150]}"
        for i, r in enumerate(out["results"], 1)) or "(无检索证据)"
    prompt = (
        "撰写学术论文中文摘要，按 目的/方法/结果/结论 四要素组织，"
        f"全文约{int(length)}字，不含图表引用。\n\n"
        f"主题：{topic[:500]}\n"
        f"{'关键词提示：' + keywords if keywords else ''}\n"
        f"{'侧重方向：' + focus if focus else ''}\n"
        f"相关背景（供参考）：\n{evidence}\n"
        "直接输出摘要正文。")
    return await LLMProvider().chat([{"role": "user", "content": prompt}], max_tokens=900)


# ---------------- 6. 术语解析 ----------------
async def term_explain(term: str = ""):
    if not term:
        return "请提供要解释的术语"
    out = await rag_pipeline.search(f"{term} 概念 原理 应用", top_k=3)
    evidence = "\n".join(
        f"[{i}] {(r.get('meta') or {}).get('title', '')}：{r['content'][:200]}"
        for i, r in enumerate(out["results"], 1)) or "(知识库无直接资料)"
    prompt = (
        f"用通俗+学术两层解释术语「{term[:100]}」：\n"
        "1. 一句话通俗解释；\n"
        "2. 学术定义与核心原理；\n"
        "3. 典型应用场景 2-3 个；\n"
        f"知识库线索：\n{evidence}\nMarkdown 输出，总长不超过400字。")
    return await LLMProvider().chat([{"role": "user", "content": prompt}], max_tokens=700)
