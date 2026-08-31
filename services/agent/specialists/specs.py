"""6 类专项 Agent 规格定义（纯数据，不含节点执行逻辑）。"""
from dataclasses import dataclass, field


@dataclass
class SpecialistSpec:
    name: str                 # 节点名, 如 "topic_agent"
    intent: str               # 负责的意图
    title: str                # 中文名
    system: str
    tools: list[str] = field(default_factory=list)     # 允许的工具名
    needs_confirmation: bool = False                   # 产出后是否人机确认


TOPIC_AGENT = SpecialistSpec(
    name="topic_agent", intent="topic_analysis", title="选题分析Agent",
    system="你是毕业论文选题分析专家。结合用户专业、兴趣与要求，产出可执行的选题建议。"
           "先调用 topic_analysis 工具生成候选，可用 search_literature 检验方向热度。",
    tools=["topic_analysis", "search_literature"],
    needs_confirmation=True,
)

LITERATURE_AGENT = SpecialistSpec(
    name="literature_agent", intent="literature_search", title="文献检索Agent",
    system="你是学术文献检索专家。对用户的研究主题执行递进式检索并归纳综述。"
           "先调用 rewrite_query 优化查询，再调用 search_literature 获取文献，"
           "输出按主题聚类的文献综述（含出处）。",
    tools=["rewrite_query", "search_literature"],
)

WRITING_AGENT = SpecialistSpec(
    name="writing_agent", intent="writing", title="论文写作Agent",
    system="你是学术论文写作专家。根据用户要求撰写/润色指定章节，"
           "可先用 search_literature 检索支撑材料，再调用 generate_section 产出正文。"
           "遵循学术语言规范，引用检索到的文献。",
    tools=["search_literature", "generate_section"],
)

FORMAT_AGENT = SpecialistSpec(
    name="format_agent", intent="format_check", title="格式校验Agent",
    system="你是论文格式审查专家。调用 check_format 对文本做规则+语义双通道校验，"
           "汇总问题清单并给出修复建议。",
    tools=["check_format"],
)

PLAGIARISM_AGENT = SpecialistSpec(
    name="plagiarism_agent", intent="plagiarism_reduce", title="查重降重Agent",
    system="你是查重与降重专家。先调用 check_plagiarism 定位高重复片段，"
           "对高重复部分给出同义改写版本，保持学术含义不变。",
    tools=["check_plagiarism"],
)

AI_DETECT_AGENT = SpecialistSpec(
    name="ai_detect_agent", intent="ai_detect", title="AI检测Agent",
    system="你是AI文本痕迹检测专家。调用 detect_ai_text 检测AI痕迹，"
           "输出AI概率、判定信号与降低AI味的具体改写建议。",
    tools=["detect_ai_text"],
)

SPECIALISTS: dict[str, SpecialistSpec] = {
    s.name: s for s in (TOPIC_AGENT, LITERATURE_AGENT, WRITING_AGENT,
                        FORMAT_AGENT, PLAGIARISM_AGENT, AI_DETECT_AGENT)
}

INTENT_TO_AGENT = {s.intent: s.name for s in SPECIALISTS.values()}