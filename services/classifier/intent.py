"""三层轻量意图预分类器：规则层 → 向量相似层 → LLM 兜底。

设计目标（对应简历"三层轻量意图预分类器降低成本提高速率"）:
- L1 规则层: 关键词/正则命中直接返回，0 token、毫秒级，覆盖大部分高频指令
- L2 向量层: 与意图原型句做 embedding 余弦相似，成本低、中文效果好
- L3 LLM 层: 前两层置信度不足时才调用大模型 JSON 输出兜底
"""
import logging
import re
from dataclasses import dataclass

from services.llm.provider import LLMProvider

logger = logging.getLogger("lunjiang.classifier")

INTENTS = ["topic_analysis", "literature_search", "writing",
           "format_check", "plagiarism_reduce", "ai_detect", "chitchat"]

INTENT_LABEL = {
    "topic_analysis": "选题分析", "literature_search": "文献检索", "writing": "论文写作",
    "format_check": "格式校验", "plagiarism_reduce": "查重降重", "ai_detect": "AI检测",
    "chitchat": "闲聊/其他",
}

# ---------- L1 规则层（顺序敏感：更具体的模式在前）----------
_RULES: list[tuple[str, re.Pattern]] = [
    ("format_check", re.compile(r"(格式|排版|目录|参考文献格式|页码|字体).*(检查|校验|规范|对|错)|格式(对|错|有问题)|按.{0,6}格式")),
    ("literature_search", re.compile(r"(找|查|检索|搜)(一些|几篇|相关)?(文献|论文|资料)|文献综述|参考文献")),
    ("plagiarism_reduce", re.compile(r"(查重|重复率|降重|改写.*(降|避免)重复|抄袭)")),
    ("ai_detect", re.compile(r"(AI(检测|率|痕迹|味)|像AI写的|人味|降AI)")),
    ("topic_analysis", re.compile(r"(选题|题目|方向).*(分析|推荐|确定|纠结)|帮我想(个|个合适的)?(题|题目|选题)|开题")),
    ("writing", re.compile(r"(写|扩写|续写|润色|修改)(一)?(下|段|章|节|部分)?(摘要|引言|文献综述|方法|结论|正文|大纲)?|大纲|提纲")),
    ("chitchat", re.compile(r"^(你好|您好|hi|hello|在吗|谢谢|感谢)[!！。~\s]*$", re.I)),
]


@dataclass
class IntentResult:
    intent: str
    confidence: float
    layer: str  # rule / vector / llm


class IntentClassifier:
    def __init__(self):
        self._provider: LLMProvider | None = None
        self._prototypes: dict[str, list[str]] = {
            "topic_analysis": ["帮我确定毕业论文选题方向", "这个研究题目可行吗", "开题报告题目怎么定"],
            "literature_search": ["帮我检索相关领域文献", "找几篇核心期刊论文", "这个主题有哪些参考文献"],
            "writing": ["帮我写论文摘要", "扩写这一段正文", "润色这段话的表达", "生成论文大纲"],
            "format_check": ["检查我的论文格式是否规范", "参考文献格式对不对", "目录页码符合要求吗"],
            "plagiarism_reduce": ["这段话重复率太高帮我降重", "改写句子避免查重", "同义替换这段内容"],
            "ai_detect": ["检测这段文字的AI痕迹", "AI率会不会很高", "帮我降低AI味"],
            "chitchat": ["你好呀", "你能做什么", "谢谢帮助"],
        }
        self._proto_vecs: dict[str, list[list[float]]] | None = None

    @property
    def provider(self) -> LLMProvider:
        if self._provider is None:
            self._provider = LLMProvider()
        return self._provider

    async def classify(self, text: str) -> IntentResult:
        text = text.strip()
        # L1 规则
        for intent, pattern in _RULES:
            if pattern.search(text):
                return IntentResult(intent, 0.95, "rule")
        # L2 向量原型相似
        result = await self._vector_layer(text)
        if result and result.confidence >= 0.62:
            return result
        # L3 LLM 兜底
        return await self._llm_layer(text)

    # ---------- L2 ----------
    async def _ensure_prototypes(self) -> None:
        if self._proto_vecs is None:
            texts = [(i, s) for i, ss in self._prototypes.items() for s in ss]
            vecs = await self.provider.embed([t[1] for t in texts])
            self._proto_vecs = {}
            for (intent, _), v in zip(texts, vecs):
                self._proto_vecs.setdefault(intent, []).append(v)

    @staticmethod
    def _cos(a: list[float], b: list[float]) -> float:
        na = sum(x * x for x in a) ** 0.5
        nb = sum(x * x for x in b) ** 0.5
        return sum(x * y for x, y in zip(a, b)) / (na * nb or 1)

    async def _vector_layer(self, text: str) -> IntentResult | None:
        try:
            await self._ensure_prototypes()
            qvec = (await self.provider.embed([text]))[0]
            best_intent, best_score = "chitchat", -1.0
            proto_vecs = self._proto_vecs or {}
            for intent, vecs in proto_vecs.items():
                score = max(self._cos(qvec, v) for v in vecs)
                if score > best_score:
                    best_intent, best_score = intent, score
            # 余弦归一到 0~1 置信度
            return IntentResult(best_intent, max(0.0, min(1.0, best_score)), "vector")
        except Exception:
            logger.exception("向量分类层失败，转 LLM 兜底")
            return None

    # ---------- L3 ----------
    async def _llm_layer(self, text: str) -> IntentResult:
        prompt = (
            "你是论文助手的意图分类器。将用户输入分类到以下意图之一: "
            f"{', '.join(INTENTS)}。\n"
            f"意图含义: {INTENT_LABEL}\n"
            '只输出JSON: {"intent": "...", "confidence": 0.xx}\n'
            f"用户输入: {text}"
        )
        try:
            data = await self.provider.chat(
                [{"role": "user", "content": prompt}], json_mode=True,
                temperature=0.0, max_tokens=64,
            )
            payload: dict = data if isinstance(data, dict) else {}
            intent = payload.get("intent", "chitchat")
            if intent not in INTENTS:
                intent = "chitchat"
            return IntentResult(intent, float(payload.get("confidence", 0.5)), "llm")
        except Exception:
            logger.exception("LLM 分类兜底失败，默认 chitchat")
            return IntentResult("chitchat", 0.3, "llm")


intent_classifier = IntentClassifier()
