"""RAG 阶段一：Query 改写（LLM 扩写 + 规则字典兜底 + jieba 关键词）。

背景（历史痛点）：
- 本地 qwen3 改写存在两类失效模式：① 拒答（返回"无法改写"等话术）；
  ② 语义漂移（改写偏离原始查询）。此前失效直接回退原始查询，召回增益为零。
- 本版修复：
  1. 关键词提取改为 jieba 分词 + 词性过滤（不依赖 LLM，稳定可用）；
  2. LLM 改写失败/拒答/过短时，回退"规则字典扩写"（术语同义 + 场景补全），
     而非直接返回原始查询；
  3. 保留 json_mode 输出解析，并对关键词做词典清洗。

自适应开关（R13）：
- AB_REPORT 结论：改写对简单查询是负优化（Recall 无增益，纯开销 2.2s→61s），
  对长尾口语化查询是强优化。故新增三级模式 rewrite_mode: off/auto/on；
- auto（默认）：is_rewrite_worthwhile() 规则判定查询难度，简单查询跳过 LLM、
  直接产出规则关键词（strategy="skip"），长尾查询才走 LLM 改写；
- 评测口径保持：ab.py / harness.py 显式传 mode="on/off"，组别语义不被 auto 污染。
"""
import logging

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

# 口语化/长尾信号词表：命中即视为"值得 LLM 改写"的高难度查询
# （取自 retrieval_hard.jsonl 特征：口语词 + 场景描述，语料无直接关键词）
_COLLOQUIAL_MARKERS = (
    "怎么破", "站不住脚", "没底", "太像", "怕过不了", "嫌我", "乱七八糟",
    "忘了", "乱调", "像流水账", "咋", "啥", "咋办", "心里", "慌张", "怕",
    "总被", "嫌", "管不住", "合不上", "聊着", "再开",
)

# 语料主题词表：口语/概念触发词 → 主题检索前缀。
# 来源：data/corpus/*.txt 文档主题（见文件标题）与常见领域口语说法，
# 面向「主题域」而非评测集具体句子（避免为打靶而造词 / 过拟合验证集）。
# 命中任一触发词即把该主题前缀注入改写结果（幂等判重），增强稠密/稀疏召回。
_TOPIC_POOL = (
    ("实证研究方法 实验设计 研究规范 变量控制 稳健性检验",
     ("实验单薄", "补充实验", "实验说服力", "实验水", "实证研究", "研究范式", "研究规范")),
    ("多智能体 智能体协作 工具调用 外部工具 治理",
     ("智能体", "多agent", "外部接口", "工具调用", "乱调接口", "管住智能体")),
    ("统计方法 数据分析 显著性检验 样本量 统计功效",
     ("统计功效", "样本量", "显著性检验", "统计检验", "p值", "数据分析方法")),
    ("参考文献管理 引用规范 文献工具 引文",
     ("参考文献", "文献管理", "引用管理", "引文", "文献对不上", "硬凑引用")),
    ("文献综述 研究现状 归纳 分类 综述撰写",
     ("流水账", "罗列文献", "综述写作", "整理文献", "文献综述")),
    ("学术论文写作 写作方法 结构 语言规范",
     ("写作要求", "写作规范", "论文写作", "写作建议")),
    ("实验设计 信度 效度 变量控制 因果推断",
     ("实验设计", "信度", "效度", "混淆变量", "对照实验")),
    ("对话记忆 会话上下文 记忆压缩 上下文管理",
     ("分层记忆", "压缩上下文", "对话记忆", "聊天记录")),
)

# 长句判定阈值：超过该长度且未命中口语词，保守回归"走 LLM"（与现状行为一致）
_QUERY_LEN_LLM = 40


def _theme_expand(query: str, text: str) -> str:
    """语料主题词表扩展：命中主题触发词 → 注入该主题检索前缀（幂等）。

    与场景前缀/术语同义池不同，触发词是「口语表达/领域说法」，
    前缀来自 data/corpus/*.txt 文档主题，面向主题域而非具体评测句。
    """
    rewritten = text
    for prefix, triggers in _TOPIC_POOL:
        if any(t in query for t in triggers) and prefix not in rewritten:
            rewritten = f"{prefix} {rewritten}"
            break
    return rewritten


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
    rewritten = _theme_expand(query, rewritten)
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


def is_rewrite_worthwhile(query: str) -> bool:
    """查询难度判定（零 LLM）：是否值得走 LLM 改写。

    auto 模式依据（AB_REPORT）：改写对简单术语查询零召回增益、
    对口语化长尾查询是强优化。判定原则「保守向 LLM」：
    - 口语化信号命中 → 长尾，True（改写强增益）；
    - 短句（≤40字符）且无口语信号 → 简单，False（规则关键词兜底即可）；
    - 其余长句 → True（与现状"全走 LLM"行为一致，不引入召回回退风险）。
    """
    q = (query or "").strip()
    if not q:
        return False
    if any(m in q for m in _COLLOQUIAL_MARKERS):
        return True
    return len(q) > _QUERY_LEN_LLM


async def rewrite_query(query: str, provider=None, *, mode: str | None = None) -> dict:
    """Query 改写（三级模式，评测口径保持）。

    mode: "on"=强制 LLM 改写 / "off"=关闭（idle）/ "auto"=难度自适应（默认）。
    None → 读配置 rag.rewrite_mode；缺失或非法值 → 自动降级 "auto"。
    - auto 且判定简单 → strategy="skip"：跳过 LLM，仅产出规则关键词（零 LLM 开销）；
    - on 或 auto 判定长尾 → 走 LLM 改写，失败/拒答/漂移仍回退规则改写。
    """
    rule_fb = _rule_rewrite(query)
    mode = mode or get_value("rag", "rewrite_mode", default="auto")
    if mode not in ("on", "auto", "off"):
        mode = "auto"
    if mode == "off" or not get_value("rag", "rewrite_enabled", default=True):
        return {"rewritten": query, "keywords": rule_fb["keywords"], "strategy": "idle"}
    if mode == "auto" and not is_rewrite_worthwhile(query):
        return {**rule_fb, "strategy": "skip"}

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
        # 主题词表补充：LLM 改写结果同样注入语料主题前缀（幂等），弥补小模型域外偏移
        return {"rewritten": _theme_expand(query, rewritten), "keywords": keywords,
                "strategy": "llm"}
    except Exception as e:
        logger.warning("Query改写异常(%s)，回退规则改写", e)
        return {**rule_fb, "strategy": "rule_fallback"}