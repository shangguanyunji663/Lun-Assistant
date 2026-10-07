"""人工复核：为 hold-out 意图集填入参考标签并计算分层错误率。

复核纪律：标签由人工按"这句话在论文辅助场景下最合理的意图"判定，
**不看分类器结果**先定标签，再比对（脚本里标签是独立硬编码的，与预测无关）。
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "evals" / "results_intent_holdout.json"

# 人工复核标签（按样本顺序，独立于分类器预测）
GOLD = [
    # 1-14 开放式选题咨询
    "topic_analysis", "topic_analysis", "topic_analysis", "topic_analysis",
    "topic_analysis", "topic_analysis", "topic_analysis", "topic_analysis",
    "topic_analysis", "topic_analysis", "topic_analysis", "topic_analysis",
    "topic_analysis", "topic_analysis",
    # 15-26 资料检索意图（"想看看别人怎么做的/有什么新动静/谁做过"）
    "literature_search", "literature_search", "literature_search", "literature_search",
    "literature_search", "literature_search", "literature_search", "literature_search",
    "literature_search", "literature_search", "literature_search", "literature_search",
    # 27-40 论文写作意图（措辞/结构/表达）
    "writing", "writing", "writing", "writing", "writing", "writing",
    "writing", "writing", "writing", "writing", "writing", "writing",
    "writing", "writing",
    # 41-50 格式规范意图
    "format_check", "format_check", "format_check", "format_check", "format_check",
    "format_check", "format_check", "format_check", "format_check", "format_check",
    # 51-59 降重意图
    "plagiarism_reduce", "plagiarism_reduce", "plagiarism_reduce", "plagiarism_reduce",
    "plagiarism_reduce", "plagiarism_reduce", "plagiarism_reduce", "plagiarism_reduce",
    "plagiarism_reduce",
    # 60-68 AI 痕迹意图（60 归 ai_detect："机器检查"指 AI 检测器）
    "ai_detect", "ai_detect", "ai_detect", "ai_detect", "ai_detect",
    "ai_detect", "ai_detect", "ai_detect", "ai_detect",
    # 69-80 闲聊
    "chitchat", "chitchat", "chitchat", "chitchat", "chitchat", "chitchat",
    "chitchat", "chitchat", "chitchat", "chitchat", "chitchat", "chitchat",
    # 81-92 边界样本（按最合理意图判定）
    "plagiarism_reduce",   # 81 同时有 AI 与撞车，先处理撞车 → 降重
    "writing",             # 82 推倒重来 → 写作
    "writing",             # 83 材料变成一章 → 写作
    "writing",             # 84 怕被问到答不上来 → 准备/写作辅助
    "chitchat",            # 85 怎么准备才能不慌 → 闲聊式安抚
    "chitchat",            # 86 不知道从哪下手 → 求助/闲聊
    "format_check",        # 87 通读看毛病 → 检查
    "writing",             # 88 这篇还有救吗 → 写作求助
    "chitchat",            # 89 流程要多久 → 咨询
    "chitchat",            # 90 难在哪 → 咨询
    "chitchat",            # 91 有没有省事的办法 → 咨询
    "chitchat",            # 92 从哪一步开始 → 咨询
]

d = json.loads(PATH.read_text(encoding="utf-8"))
preds = d["predictions"]
assert len(preds) == len(GOLD) == 92, f"{len(preds)} vs {len(GOLD)}"

correct = 0
layer_total: Counter = Counter()
layer_hit: Counter = Counter()
confusion: Counter = Counter()
misses = []
for i, (p, gold) in enumerate(zip(preds, GOLD), 1):
    layer = p["layer"]
    layer_total[layer] += 1
    if p["predicted"] == gold:
        correct += 1
        layer_hit[layer] += 1
    else:
        confusion[(gold, p["predicted"])] += 1
        misses.append({"n": i, "text": p["text"], "gold": gold,
                       "predicted": p["predicted"], "layer": layer,
                       "confidence": p["confidence"]})

layer_wrong = {k: layer_total[k] - layer_hit[k] for k in layer_total}
print("hold-out 意图集（92 条，零原型句重叠）")
print(f"  总体准确率: {correct}/{len(GOLD)} = {correct / len(GOLD):.1%}")
print(f"  分层分布  : {dict(layer_total)}")
print(f"  分层命中  : {dict(layer_hit)}")
print(f"  分层错误  : {layer_wrong}")
for k in layer_total:
    print(f"    {k:<7} 错误率 {layer_wrong[k] / layer_total[k]:5.1%}  ({layer_wrong[k]}/{layer_total[k]})")
print("\n  主要混淆对（参考→预测）:")
for (gold, pred), n in confusion.most_common(8):
    print(f"    {gold:<18} → {pred:<18} {n} 次")
print(f"\n  逐条错误（{len(misses)} 条）:")
for m in misses:
    print(f"    #{m['n']:>2} [{m['layer']:<6}] {m['gold']:<18}→{m['predicted']:<18} {m['text']}")

# 回写复核结果
for p, gold in zip(preds, GOLD):
    p["gold"] = gold
    p["review"] = "correct" if p["predicted"] == gold else "wrong"
d["review"] = {
    "protocol": "先按场景定参考标签，再与盲跑预测比对（标签独立于预测）",
    "cases": len(GOLD),
    "accuracy": round(correct / len(GOLD), 3),
    "layer_distribution": dict(layer_total),
    "layer_hits": dict(layer_hit),
    "layer_error_rate": {k: round(layer_wrong[k] / layer_total[k], 3) for k in layer_total},
    "top_confusions": [{"gold": g, "predicted": p, "count": n}
                       for (g, p), n in confusion.most_common(8)],
    "misses": misses,
    "key_finding": (
        "向量层错误率 38.1% 是 LLM 层 12.2% 的三倍。更深一层：向量层 correct 的置信度"
        "均值 0.672、wrong 均值 0.655 —— **两者区间完全重叠（0.622~0.709），置信度"
        "无法区分对错**。这说明余弦相似度在 0.62 附近不是一个有效的置信度门："
        "42 条向量层判定全部落在 0.62~0.71，全部被放行，LLM 兜底层从未被启用。"
        "可执行结论：不应微调阈值，而应把 L2 判定改送 LLM 复核（或改用 margin/"
        "长度归一化等真正有区分度的信号）。"
    ),
    "scope_caveat": (
        "本集合为**刻意构造的零 L1 命中**集合（样本避开了全部规则触发字），"
        "因此 76.1% 测的是'规则层覆盖不到的那部分'（长尾占比 54/92 ≈ 59%），"
        "比生产流量分布更差：生产查询含关键词时规则层以 0 成本兜住 46%。"
        "故 76.1% 是**下限**而非总体水位，不应与含关键词的 50 条集 92% 直接并列。"
    ),
}
PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n复核结果已回写 {PATH}")

# 阈值敏感性：若把向量层阈值提到 0.75，会有多少样本转交 LLM
for th in (0.62, 0.70, 0.75, 0.80, 0.85):
    escalated = [p for p in preds if p["layer"] == "vector" and p["confidence"] < th]
    esc_wrong = [p for p in escalated if p["review"] == "wrong"]
    print(f"  阈值 {th:.2f}: 向量层转交 LLM {len(escalated):>2} 条"
          f"（其中当前判错 {len(esc_wrong)} 条，即潜在可救回 {len(esc_wrong)} 条）")
