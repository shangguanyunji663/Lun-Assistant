"""RAG 阶段一：Query 改写（LLM 扩写 + 规则字典兜底 + jieba 关键词）。

背景（历史痛点）：
- 本地 qwen3 改写存在两类失效模式：① 拒答（返回"无法改写"等话术）；
  ② 语义漂移（改写偏离原始查询）。此前失效直接回退原始查询，召回增益为零。
- 本版修复：
  1. 关键词提取改为 jieba 分词 + 词性过滤（不依赖 LLM，稳定可用）；
  2. LLM 改写失败/拒答/过短时，回退"规则字典扩写"（术语同义 + 场景补全），
     而非直接返回原始查询；
  3. 保留 json_mode 输出解析，并对关键词做词典清洗。
"""
import json
import logging

import jieba
import jieba.posseg as pseg

from infrastructure.config import get_value
from services.llm.provider import LLMProvider

logger = logging.getLogger("lunjiang.rag")

_SYSTEM = (
    "你是学术检索查询改写器。将用户的论文相关请求改写为适合学术文献检索的查询。"
    "输出JSON: {\"rewritten\": \"改写后的完整查询(中英混合均可, 补全学科术语)\", "
    "\"keywords\": [\"3-6个检索关键词\"]}"
)

# 学术场景补全：口语化问法 → 检索前缀（保持语义不变，仅增强召回合）
_SCENE_PREFIX = {
    "开题": "开题报告 选题 研究问题 可行性 研究计划",
    "综述": "文献综述 研究现状 研究进展 分类 归纳",
    "答辩": "毕业答辩 答辩准备 问答 演示 评审",
    "格式": "论文格式 排版 规范 章节结构 参考文献格式",
    "查重": "查重 降重 重复率 学术不端 引用规范",
    "写作": "学术写作 论文写作 章节 结构 语言规范",
    "如何写": "写作方法 撰写要点 结构 规范",
    "怎么": "方法 步骤 流程 要点",
}

# 术语同义池：命中即扩充等价表述（中英/近义），提升稠密召回
_SYNONYM_POOL = {
    "注意力机制": "注意力机制 attention transformer",
    "transformer": "transformer 自注意力 注意力机制",
    "大模型": "大模型 大语言模型 LLM 预训练语言模型",
    "llm": "大语言模型 LLM 大模型 预训练语言模型",
    "检索增强": "检索增强 RAG 检索增强生成 知识检索",
    "微调": "微调 fine-tuning 参数高效微调 迁移学习",
    "向量": "向量 embedding 嵌入 稠密检索",
    "语料": "语料库 数据集 语料 训练数据",
    "卷积": "卷积神经网络 CNN 卷积核",
    "循环": "循环神经网络 RNN 序列建模",
    "强化学习": "强化学习 RL 奖励函数 智能体训练",
    "推荐": "推荐系统 协同过滤 召回 排序",
    "隐私": "隐私保护 数据安全 差分隐私 脱敏",
    "云原生": "云原生 容器化 Kubernetes 微服务",
}


def _rule_rewrite(query: str) -> dict:
    """规则级改写：场景前缀扩写 + 术语同义扩充 + jieba 关键词。

    判重口径：以「整段扩展是否已出现」为准，而非「扩展串首词是否已出现」。
    旧实现用首词判重，而首词通常就是被匹配的触发词本身（如术语"大模型"的
    扩展首词即"大模型"），导致守卫恒真、同义词池整体失效（死逻辑）。
    """
    rewritten = query
    for trigger, prefix in _SCENE_PREFIX.items():
        if trigger in query and prefix not in rewritten:
            rewritten = f"{prefix} {rewritten}"
            break
    for term, expand in _SYNONYM_POOL.items():
        if term.lower() in query.lower() and expand.lower() not in rewritten.lower():
            rewritten = f"{rewritten} {expand}"
            break  # 一次扩写即可，避免无限拼接
    keywords = _rule_keywords(query)
    return {"rewritten": rewritten, "keywords": keywords,
            "strategy": "rule"}


def _rule_keywords(query: str) -> list[str]:
    """jieba 词性过滤提取检索关键词（不依赖 LLM）。"""
    stop = {"我们", "你们", "一些", "这个", "那个", "什么", "怎么", "如何", "可以",
            "需要", "请问", "想要", "关于", "以及", "自己", "现在", "一下"}
    seen, keywords = set(), []
    for w, flag in pseg.cut(query):
        if flag.startswith(("n", "v", "a", "eng", "x")) and w.lower() not in stop \
                and w not in seen:
            seen.add(w)
            keywords.append(w)
        if len(keywords) >= 6:
            break
    # jieba 词典未命中时按字符 bigram 兜底，保证非空
    if len(keywords) < 3:
        for i in range(0, len(query) - 1):
            bigram = query[i:i + 2]
            if not bigram.strip() or bigram in stop:
                continue
            if bigram not in seen:
                seen.add(bigram)
                keywords.append(bigram)
            if len(keywords) >= 3:
                break
    return keywords[:6]


def _clean_keywords(keywords: list, query: str) -> list[str]:
    """关键词洗白：过滤非法字符、去重、保序；不足时回落 jieba 规则提取。"""
    cleaned, seen = [], set()
    for k in keywords or []:
        k = str(k).strip(" '\"[]。；，,.")[:32]
        if not k or k in seen:
            continue
        seen.add(k)
        cleaned.append(k)
        if len(cleaned) >= 6:
            break
    return cleaned or _rule_keywords(query)


async def rewrite_query(query: str, provider=None) -> dict:
    """LLM 改写优先，失败/拒答/漂移时回退规则改写。"""
    rule_fb = _rule_rewrite(query)
    if not get_value("rag", "rewrite_enabled", default=True):
        return {"rewritten": query, "keywords": rule_fb["keywords"], "strategy": "idle"}

    provider = provider or LLMProvider()
    try:
        data = await provider.chat(
            [{"role": "system", "content": _SYSTEM},
             {"role": "user", "content": query}],
            json_mode=True, temperature=0.1, max_tokens=200,
        )
        rewritten = str(data.get("rewritten") or "").strip()
        keywords = _clean_keywords(data.get("keywords"), query)
        # 拒答 / 过短 / 语义漂移（与原文重合度过低视为漂移，回退规则）
        lowered = rewritten.lower()
        if not rewritten or len(rewritten) < 8 or \
                any(m in lowered[:60] for m in ("无法", "无关", "抱歉", "不能", "不适合")):
            logger.info("Query改写拒答/无效，回退规则改写")
            return {**rule_fb, "strategy": "rule_fallback"}
        overlap = len(set(query) & set(rewritten)) / max(1, len(set(query)))
        if overlap < 0.15:
            logger.info("Query改写语义漂移(重合%.2f)，回退规则改写", overlap)
            return {**rule_fb, "strategy": "rule_fallback"}
        return {"rewritten": rewritten, "keywords": keywords,
                "strategy": "llm"}
    except Exception as e:
        logger.warning("Query改写异常(%s)，回退规则改写", e)
        return {**rule_fb, "strategy": "rule_fallback"}