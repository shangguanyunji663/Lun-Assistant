# 术语与数字单一真源（CANON）

> 日期：2026-10-05
> 用途：全仓文档同步的**唯一数字/术语基准**。任何文档引用的数字与此不符即为缺陷。
> 纪律：数字只能来自**已落盘产物**，产物路径必须同时给出。

---

## 一、术语规范（同一概念只用一个说法）

| 概念 | ✅ 规范说法 | ❌ 不要用 | 出处 |
| :--- | :--- | :--- | :--- |
| 主题 | 皮肤 | 主题 / theme（正文描述用「皮肤」；CSS 类名与令牌 `--*` 保持 `skin`/`theme-color` 原样） | `frontend/src/skins/registry.js` |
| 展示页 | 落地页 | landing page / 首页 | `frontend/*.html` |
| 主应用 | 工作台 | 应用页 / 主界面 | `frontend/app.html` |
| 意图分层 | L1 规则层 / L2 向量层 / L3 LLM 层 | 规则层/向量层（可简称，但首次出现须写全） | `services/classifier/intent.py` |
| 工具治理 | 七步治理栈 | 治理流水线 6 步（早期口径，已废） | `services/governance/tool_registry.py` |
| 检索管线 | 三阶段 RAG（改写 → 多路 RRF 融合 → 交叉编码器精排） | 三路召回（易与「三引擎」混淆） | `services/rag/pipeline.py` |
| 召回三引擎 | 稠密（bge-m3）/ 稀疏（BM25+jieba）/ 相邻句窗 | 三路检索 | `services/rag/retriever.py` |
| 召回路数 | **六路**（稠密、稀疏、关键词、原查询保底、项目私有库、相邻窗口） | — | `services/rag/pipeline.py:64` |

> **「三引擎」与「六路召回」不矛盾**：三引擎指**召回机制**（稠密 / 稀疏 / 句窗扩展），
> 六路指**装配到 RRF 融合的具体召回路**。文档中同时出现时须各用其名，勿混称。
| 产物可信信息 | 产物身份证（provenance） | 元数据 / metadata | `evals/provenance.py` |
| 评测产物 | 产物（不放「报告」二字，`*.md` 报告另称「报告」） | — | `evals/results_*.json` |
| 专项角色 | 专项 Agent（6 个） | 子 agent / 专家 agent | `services/agent/specialists/specs.py` |
| 测试 | 离线用例（`tests/`，不依赖外部服务） | 单测/离线测试（可简称，首次须写全） | `pytest.ini` |

**皮肤命名**（八套，顺序固定）：
A 铅字印刷 / B 夜航仪表 / C 学术海报 / D 木牍竖排 / E 孔版双色 / F 索引档案 / G 编队总谱 / H 论文底片。
出处：`frontend/src/skins/registry.js`。

---

## 二、数字真源（每个数字必须附产物路径）

### 工程规模

| 指标 | 值 | 产物 / 出处 |
| :--- | :--- | :--- |
| 离线用例 | **103 passed** | `pytest tests/ -q`（15 个测试文件） |
| 工具数 | **14**（8 通用 + 6 学术） | `services/governance/tools_impl.py` |
| 治理栈 | **七步** | `services/governance/tool_registry.py` |
| 专项 Agent | **6** | `services/agent/specialists/specs.py` |
| 编排图节点 | **10**（supervisor + planner + 6 专项 + 2） | `build_graph()` 实测，见 `evals/regression.py` |
| 语料 | **81 篇**（库内 1376 块） | `data/corpus/`；`scripts/_audit_corpus_count.py` |
| 评测样本总量 | **138 条** | 50+20+20+40+8；`evals/datasets/` |
| 皮肤 / 落地页 | **8 套 / 8 张** | `frontend/src/skins/registry.js` |
| vite 入口 | **9 个**（站根 + 工作台 + 8 落地页） | `frontend/vite.config.js` |

### 评测指标

| 指标 | 值 | 口径 | 产物 |
| :--- | :--- | :--- | :--- |
| 意图分类 L1 覆盖 | **23/50 = 46%** | 规则层独立命中（零 token） | `scripts/_audit_l1_coverage.py` |
| 意图分类（50 条集） | **92.0%（46/50）** | rule 23 / vector 26 / llm 1 | `evals/results_latest.json` |
| 意图分类（hold-out 92 条） | **76.1%（70/92）** | 零原型句重叠；分层错误率 rule 0% / vector 38.1% / llm 12.2% | `evals/results_intent_holdout.json`（样本内嵌于 `evals/eval_intent_holdout.py` 的 `TEXTS`，未单独落 jsonl） |
| RAG Recall@5（简单集 20） | **100%（20/20）**，平均 **108.2s/条** | 期望文件出现在 Top-5 的 `meta.file`。**该耗时随 CPU 负载波动大（历次 62.0s / 108.2s），引用时须与产物时间戳同时给出** | `evals/results_latest.json`（21:40:44 那轮） |
| RAG Recall@5（口语长尾 20） | **80%** | 09-04 快照，**产物待补** | — |
| RAG Recall@5（学术刁钻 40） | **95%** | 09-04 快照，**产物待补** | — |
| 泛化（hold-out 8） | **75%（6/8）** | 09-04 快照，**产物待补** | — |
| 难度画像（字面重合） | 简单 **67.5%** / 长尾 **29.2%** / 学术 **43.1%** / 泛化 **31.5%** | 查询与期望语料 2-gram 重合率 | `scripts/_audit_dataset_difficulty.py` |
| 压缩率（合成 fixture） | **0.214** | `"背景填充"*120`，keep_recent=4 | `evals/results_latest.json` |
| 压缩率（真实语料·生产路径） | **0.035** | keep_recent=0，12 轮 / 11943 字 | `evals/results_compression_real.json` |
| 压缩率（真实语料·keep_recent=4） | **0.191** | 历史发布口径 | 同上 |
| 回归 | **16/16 真断言 PASS**，无 SKIP | 每项均可失败 | `evals/regression.py` |
| A/B MRR（长尾困难集） | **0.744 → 0.917** | 改写关闭 → 改写开+防漂移修复 | `evals/ab_report.json`（逐条 rank 可复算） |
| A/B 耗时 | 简单集改写纯开销 **2.2s → 61s** | — | `evals/ab_report.json` |

### ⚠️ 不可再引用的数字（已证伪或有争议）

| 废弃数字 | 原因 |
| :--- | :--- |
| 意图分类 100%（50/50） | 实为 22 条那次产物凑数；真实 92% |
| 意图 rule 16 / vector 34 | 同上，凑数产物 |
| Recall@5 100%（8 条） | 扩容前旧产物，现为 20 条 |
| 回归「七大场景全通」 | 16 是子项计数，不是场景数 |
| 压缩率 0.212 / 0.214（单列） | 必须注明是**合成 fixture**；生产路径为 0.035 |
| A/B 的 `87.5% ↓`（A₀ 列） | 硬编码模板字符串，无产物支撑 |
| `is_complex_task` 单目标词判定 | 已知缺陷（`planner.py:43`），勿作能力宣称 |
| 130 条 | 算术错误，应为 138 |

---

## 三、今日（2026-10-05）代码行为变更 → 文档需同步

| # | 变更 | 文件 | 影响的文档 |
| :--- | :--- | :--- | :--- |
| 1 | 新增产物身份证（provenance） | `evals/provenance.py`（新） | README、EVALUATION_REPORT、PROJECT_STRUCTURE、学习指南 |
| 2 | harness 产物加 `_provenance`；**子集运行改为合并**不再截断 | `evals/harness.py` | 同上 |
| 3 | 新增 hold-out 意图集与盲跑脚本 | `evals/eval_intent_holdout.py`（新，92 条样本内嵌于 `TEXTS`） | README、PROJECT_STRUCTURE、EVALUATION_REPORT |
| 4 | 新增难度分层补测入口 | `evals/eval_suites.py`（新） | 同上 |
| 5 | 新增真实语料压缩重测 | `evals/eval_compression_real.py`（新） | 同上 |
| 6 | 回归 4 处恒真断言改为真断言（16 项不变） | `evals/regression.py` | EVALUATION_REPORT、学习指南（回归口径） |
| 7 | `smoke_trace.py` token 统计改为真断言 | `scripts/smoke_trace.py` | 学习指南（冒烟锚点） |
| 8 | **压缩器三处行为修复**：高价值判定三档化、`keep_recent` 改 `is None` + `==0` 分支、摘要加 300 字硬上限 | `services/memory/compressor.py` | README、METRICS_FINAL、学习指南（压缩章节）、ARCHITECTURE_REVIEW |
| 9 | 新增 6 项压缩语义用例 + 4 项 provenance 用例 | `tests/test_memory_pure.py`、`tests/test_evals_scoring.py` | 各处用例数 93 → **103** |
| 10 | 前端 6 张落地页读数区数字与水位声明更新 | `frontend/*.html`、`dossier.html` | PROJECT_STRUCTURE（若提及读数）、frontend-versions 索引 |

> 新增诊断脚本（`scripts/_audit_*.py`）为**一次性审计工具，不是正式工具链**。
> 经 2026-10-05 清理，仅保留被文档引用的 5 个作为可复现证据：
>
> | 脚本 | 用途 | 被引用于 |
> | :--- | :--- | :--- |
> | `_audit_corpus_count.py` | 核对评测集期望语料是否都在库 | CANON §二、DATA_INTEGRITY_AUDIT |
> | `_audit_l1_coverage.py` | L1 规则层独立覆盖率 | CANON §二、DATA_INTEGRITY_AUDIT |
> | `_audit_dataset_difficulty.py` | 各检索集字面重合度（难度画像） | CANON §二、METRICS_FINAL §二 |
> | `_audit_holdout_review.py` | hold-out 人工复核 + 分层错误率 | METRICS_FINAL §一 |
> | `_audit_doc_links.py` | 全仓 Markdown 内部链接校验 | CANON §四 |
>
> 其余一次性脚本（`_audit_pg_state` / `_audit_provenance` / `_audit_holdout_dump` / `_audit_doc_anchors`）已清理；
> 如需重跑，从本文档的复现命令重建即可。

---

## 四、文档分层（改哪里、不改哪里）

| 层 | 文档 | 处理方式 |
| :--- | :--- | :--- |
| **活文档**（描述当前状态） | README、PROJECT_STRUCTURE、DEPLOY、EVALUATION_REPORT、METRICS_FINAL、ARCHITECTURE_REVIEW、FORMAT_STANDARD、frontend-versions/README、skins/CONTRACT、AB_REPORT、RESUME_READINESS_AUDIT 顶部标注 | **同步到最新** |
| **教学文档** | 论匠学习指南.md | **仅同步受影响段落**（用例数、压缩章节、评测口径、冒烟锚点） |
| **历史记录**（某时点的轮次档案） | docs/OPTIMIZATION_ROUND*.md、docs/frontend-versions/CHANGELOG-*、OPTIMIZATION_ROUND*、ROUND20-ADDENDUM、VISUAL_DIRECTIONS、TEMPLATE | **不改正文**（改了会让文档说谎）；如被活文档引用需保证链接有效 |
| **非文档** | `.workbuddy*/memory/`、`data/uploads/*.md`、`frontend/src/skins/patterns/README.md`（组件说明，非项目文档，如无变化不动） | **不动** |

> 历史记录的纪律：`OPTIMIZATION_ROUND*.md` 里写「tests 89 用例」是**当时的事实**。
> 强行改成 103 等于伪造历史。正确做法是让活文档指向最新，历史文档保持原样。
