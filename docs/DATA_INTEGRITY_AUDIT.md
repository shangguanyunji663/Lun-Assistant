# 数据可信度审计与修复记录（简历版）

> 日期：2026-10-05
> 范围：前端展示数字 → 评测产物 → 评测代码 → 后端实现，逐层追到 `file:line`
> 结论一句话：**引擎是真的，证据链是断的；修的不是数字，是「数字的生成方式」。**

本文档合并了两轮审计（初轮人工审计 + 全仓夸大陈述扫描），并对每条结论标注**是否已复验、是否已修复**。
凡标 ✅ 修复的，均可在本仓库中直接复跑命令验证。

---

## 〇、一句话诊断

面试官看到一排 **100%**，不会想「这人真强」，会想「**他的测试集怎么来的？**」
而这个问题的诚实答案是：50 条意图集里有多条是 L2 原型句的近义改写，100% 是**测试集泄漏 + 数据集扩容后未重跑**的合成结果。

真正的问题不是「数字写错了」，而是：

> **从代码到页面之间没有自动化通道。** 所有数字靠手抄、抄进 6 个 HTML 页面，所以必然腐烂。

对应的修法不是「把数字改小」，而是**给每个数字挂上身份证，让它能被第三方验证**。

---

## 一、已修复（P0 · 本轮完成）

| # | 问题 | 修复前 | 修复后 | 证据 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | 意图分类「50 条集 100%」 | 产物 `cases:22, accuracy:1.0, rule:16, vector:6` | **92%（46/50）**，rule 23 / vector 26 / llm 1，4 条 miss 逐条列出 | `evals/results_latest.json`（重跑） |
| 2 | Recall@5「100%」无产物 | 产物是 `cases:8, recall:0.875`（扩容前） | **100%（20/20）**，平均 62009ms/条，带 provenance | 同上 |
| 3 | 压缩率 0.214 | 未重跑；后续发现生产路径实测 **1.000（从未压缩）** | **合成 0.213 / 真实语料生产路径 0.035**；两个根因已修（标记子串误判保住 66.2% 正文、`keep_recent` 真值判断），新增 6 用例锁定 | `evals/results_compression_real.json` |
| 4 | 回归「16/16」含 4 处恒真 | `regression.py:164,174,192,200` 无条件 True / import 即 PASS / 常量自比 | **16 项全部为可失败的真断言**，逐项做了变异验证（改坏→变红→还原） | `evals/regression.py` |
| 5 | `smoke_trace.py:52` 恒真 | `'PASS' if spans[0] else 'PASS'`（两分支都是 PASS） | 断言 token 原值读回：写入 210/128 → 从库读回必须等于 210/128 | `scripts/smoke_trace.py:52-57` |
| 6 | 页面宣称「全部数字来自一次完整实测」 | 95% / 80% / 75% 在 `evals/` 下**零产物** | 改为如实区分「已带产物」与「快照待补测」，并在补测 | `frontend/*.html` |
| 7 | 产物无任何可追溯信息 | 无时间 / 无版本 / 无指纹 / 无模型名 | 新增 `_provenance`：本地时间、git revision + dirty 标记、数据集条数 + sha256、模型底座、复现命令 | `evals/provenance.py` |
| 8 | 「130 条全量基线」（同句明细相加为 138） | 文档自相矛盾 | 订正为 **138 条**（50+20+20+40+8） | `docs/EVALUATION_REPORT.md:20,46` |
| 9 | `how-it-works.html:729` 事实错误 | 「6 个专项环节：…查重、**答辩**」 | 实为 **AI检测**（`services/agent/specialists/specs.py:54`） | `frontend/how-it-works.html` |
| 10 | 离线用例数 93 | 我实测确为 93；本轮先加 4 项 provenance 单测 → 97，后又加 6 项压缩语义单测 | **103 passed**（`pytest tests/ -q` 实测），全仓同步 | `README.md` 等 |

### 修复后的验证状态（最终值）

```
envs\lunjiang\python.exe -m pytest tests/ -q   → 103 passed
envs\lunjiang\python.exe -m ruff check .       → All checks passed!
envs\lunjiang\python.exe evals\regression.py   → 16 项 | PASS=16 FAIL=0 SKIP=0
cd frontend; npm run lint                      → 通过
cd frontend; npm run build                     → ✓ built（9 入口 / 8 张 HTML）
```

产物身份证实例（`evals/results_latest.json`）：

```json
"_provenance": {
  "generated_at": "2026-10-05T18:41:19+08:00",
  "git": {"revision": "c622764", "dirty": true, "dirty_files": ["M evals/harness.py", "..."]},
  "models": {"chat": "qwen3:4b-ctx4096", "embedding": "bge-m3",
             "embedding_dim": 1024, "rerank": "BAAI/bge-reranker-base"},
  "suites": {"intent": {"cases": 50, "sha256": "6c589b04f7ebe4e2"},
             "rag":    {"cases": 20, "sha256": "f53037e7b9f6862d"}},
  "reproduce": "envs\\lunjiang\\python.exe -m evals.harness intent rag"
}
```

> `dirty: true` 是**诚实标记**而非缺陷：它说明这轮数字跑在未提交的工作区上。
> 提交后重跑即变干净 —— 这正是「结构上不可能手改」的机制。

---

## 二、仍然存在、尚未修复（按面试官杀伤力排序）

### 🔴 P0 · 强语义证据已被硬编码，且与产物冲突

`evals/AB_REPORT.md` 的三组对比表里，**A₀ 整列是写死的模板字符串**：

```python
# evals/ab.py:151-153 —— 这是生成 markdown 的 f-string，不是计算
| Recall@5 | 100% | 87.5% ↓ | **100%** |
| TOP1 命中 | 5/8 | 7/8 | **7/8** |
| MRR | 0.744 | 0.812 | **0.917 (+0.17 vs B)** |
```

而唯一产物 `evals/ab_report.json` 里 **off / on 两组都是 `recall: 1.0`**，**根本没有 87.5% 这个负结果**。

**但结论的一半是真的**：`ab_report.json:30-95,104-169` 保存了逐条 `rank`，
`0.744` 与 `0.917` 都能从各自 8 条 rank **独立复算出来**。所以：

- ✅ 可放心讲：**改写不提升召回，但提升排序（TOP1 5/8 → 7/8，MRR 0.744 → 0.917）**
- ❌ 不要讲：`87.5% ↓` 这个数字——它没有产物。要讲就先重跑 A₀ 并把产物落盘。

**修复**：`evals/ab.py:151-153` 改为从实跑结果渲染；或补跑 A₀ 组并把 `ab_report.json` 扩成三组。

### 🔴 P0 · 评测代码与测试集同源（方法论问题，比数字问题更重）

`services/rag/query_rewrite.py:64-70` 的注释**自己承认**：

```python
# 口语化/长尾信号词表：命中即视为"值得 LLM 改写"的高难度查询
# （取自 retrieval_hard.jsonl 特征：口语词 + 场景描述，语料无直接关键词）
_COLLOQUIAL_MARKERS = ("怎么破", "站不住脚", "没底", "太像", ...)
```

而 `_TOPIC_POOL`（`:76-93`）的触发词同样是评测集查询的连续子串：
「流水账」（hard #1）、「管住智能体」「外部接口」（hard #8）、「对照实验」「混淆变量」（paper_hard #18）、
「样本量」（hard #11）。**且注入点同时作用于规则层与 LLM 层，评测结果天然受益。**

同一文件 `:74` 却写「面向主题域而非评测集具体句子（避免为打靶而造词 / 过拟合验证集）」——
两处注释互相矛盾。

**这意味着**：长尾集 62.5% → 80% 的提升，不是泛化能力提升，而是**针对测试集的打靶**。
`hold-out 6/8 = 75%` 才是唯一诚实的泛化水位。

**修复建议（不是删词表，而是改叙事 + 补证据）**：
1. 把「我提升了召回」改成「**我发现测试集过拟合，于是补了 hold-out 集**」——后者是成熟工程师的标志；
2. `_COLLOQUIAL_MARKERS` / `_TOPIC_POOL` 的来源改为「从**训练语料**统计高频口语表达」而非从评测集摘取；
3. 用 hold-out 集重新报告增益。

### 🟠 P1 · 压缩率测在合成重复文本上

`evals/harness.py:86-94` 的 fixture 是 `"背景填充" * 120`、`"内容填充" * 120`，
且 `harness.py:135` 显式传 `keep_recent=4`（生产默认为 `compress_trigger_tokens // 8 = 375`）。
**任何压缩算法在高度重复文本上都能拿到漂亮数字**，且 `keep_recent` 一改结果就变。

压缩器实现本身是真的（分级留存 + 冗余去重 + 窗口截断 + **真 LLM 摘要**，`services/memory/compressor.py:102`）——
坏的是输入，不是算法。**修复**：换成真实多轮对话（可用 `frontend/src/demo.js` 的会话文本或语料片段），重测。

### 🟠 P1 · 意图测试集与 L2 原型句同源

`services/classifier/intent.py:47-55` 的原型句与 `evals/datasets/intent.jsonl` 存在同源：

| 测试集 | 原型句 | 关系 |
| :--- | :--- | :--- |
| 你能做什么 | 你能做什么 | **逐字相同** |
| 谢谢你的帮助 | 谢谢帮助 | 改写 |
| 帮我找几篇关于大语言模型的文献 | 找几篇核心期刊论文 | 改写 |

即「用原型句当参考答案，再用它的改写当考题」。**因此 92% 仍偏乐观**——
更严格的结论需要独立 hold-out 意图集（尚未做）。

### 🟠 P1 · `is_complex_task` 单目标词即判复杂

`services/agent/planner.py:43`：`if any(g in text for g in _GOAL_WORDS): return True`，
而 `_GOAL_WORDS` 含「报告」「综述」等极常见词。实测 `is_complex_task("报告")` → `True`。
`regression.py` 的三个用例恰好都是目标词覆盖句，**测试用例与规则同源，测不出这个缺陷**。

### 🟡 P2 · 若干口径夸大（代码诚实，文案夸大）

| 位置 | 问题 |
| :--- | :--- |
| `services/governance/tools_impl.py:86-115` | `check_plagiarism` 是与 81 篇本地语料的字符 bigram Jaccard，**不能查库外文本**；附带 bug：`likely_source` 取 `dense[0]` 而非 `best` 的候选 |
| `services/governance/tools_impl.py:135-145` | `detect_ai_text` = 0.4×启发式（8 个硬编码词 + 句长方差）+ 0.6×本地 4B 模型**自报** |
| `docs/EVALUATION_REPORT.md:128` | 「基线 62.5% (5/8)」实为 `AB_REPORT.md:13` 的 **TOP1 命中数**，Recall 与 TOP1 口径混用 |
| `frontend/landing-b.html:456` | 「RRF 融合 412ms · 命中 **50** 篇」，而 `configs/settings.yaml:102-103` 是 `recall_top_k:20` / `final_top_k:5`，50 不可能 |
| `evals/load_report.json:4-6` | `total:40` 但实际发 320 请求（`qps 1.9 × 168.37s ≈ 320`）；文档写 320 是诚实的，产物字段错 |
| `frontend/design-samples/*`、`frontend/public/easter/hunt.html` | 设计稿与彩蛋页也带 100% / 16/16 / 95% 等未核验数字（已修 `hunt.html`） |

### 🟡 P2 · 服务可运行性（本轮已解决，需固化）

审计开始时 **PG 5433 与 Ollama 11434 都没起**，意味着既复现不了数字也无法现场演示。
排查中发现两个环境陷阱（值得写进 README FAQ）：

1. PG 有两个实例：`PostgreSQL-17.9` 服务占 **5432**，项目用的是 `D:\Develop\DB\PostgreSQL16`（数据目录 `port=5433`），需 `pg_ctl -D ... start`；
2. **Ollama 模型仓库分裂**：CLI 能看到 4 个模型，但默认仓库 `~\.ollama\models` 只有 2 个，
   `qwen3*` 只在 `D:\Develop\Ollama\models` —— 需 `OLLAMA_MODELS` 指向该目录再启动，
   否则 harness 会拿不到 `qwen3:4b-ctx4096`。

---

## 三、真实且值得写进简历的部分（经复验）

| 能力 | 复验证据 |
| :--- | :--- |
| **三阶段 RAG** | 81 篇真实语料（库内 1376 块）；三个评测集期望的 20/14/28 个文件**缺失 0**；本次实测简单集 Recall@5 20/20 |
| **七步治理栈** | 14 工具统一纳管（`tools_impl.py` 8+6）；`tests/test_tool_registry_call.py` 13 个契约用例，含「Redis 故障时 fail-closed + 审计必落库 + 原始异常不被替换」 |
| **LangGraph 编排** | `build_graph()` **离线可编译**，实测 10 节点（supervisor + planner + 6 专项 Agent），回环边齐备（回归新断言） |
| **A/B 的 MRR 结论** | 可从 `ab_report.json` 逐条 rank 独立复算（0.744 / 0.917） |
| **103 项离线用例** | `pytest tests/ -q` → 103 passed（本轮新增 4 项 provenance 口径 + 6 项压缩语义测试） |
| **真实容错路径** | 补测日志出现 `Query改写异常(Request timed out.)，回退规则改写` —— 回退逻辑在真实数据上生效，非纸面设计 |
| **主动暴露负结果** | `AB_REPORT.md` 写明「改写不提升召回、纯开销 2.2s → 61s」——多数作品集不敢写失败 |

**这份清单才是 Agent 岗真正看的东西**：工具治理、编排、可观测、容错 —— 不是准确率数字。

---

## 四、简历话术对照（把「相信我」换成「你自己验」）

| ❌ 不要这样写 | ✅ 改成这样写 |
| :--- | :--- |
| 意图分类准确率 100% | 三层意图预分类（规则→向量→LLM）：50 条集实测 **92%**，规则层零 token 覆盖 **46%**；4 条 miss 均已定位到向量层误判（开放式提问被闲聊原型抢走） |
| RAG Recall@5 100% | 三阶段 RAG（改写→多路 RRF 融合→交叉精排），简单集 Recall@5 **100%（20/20，平均 62s/条，CPU）**；同时如实给出难度分层：口语长尾集 85%（17/20）/ 学术刁钻集 97.5%（39/40）/ hold-out 泛化 75%（6/8）——四档均带产物（results_latest / results_extra） |
| 回归 16/16 全通 | 7 场景 16 项断言，**每项均可失败**（相邻窗口召回 `[1,3]`、拒答回退、图 10 节点装配、产物骨架渲染）；最初 4 项为恒真空转，审计后已改写 |
| 压缩率 0.214 | 四层记忆分级留存 + 真 LLM 摘要压缩。合成 fixture 0.213，真实语料复测发现**生产路径实为 1.000（从未压缩）**，定位两个根因并修复（现 0.035），补 6 个离线用例锁定语义 |
| 查重降重 / AI 检测 | 本地语料相似度自查（81 篇，字符 bigram Jaccard）/ AI 痕迹提示（0.4 启发式 + 0.6 模型自报，**不作判定依据**） |
| 工具调用治理完善 | 14 个工具统一纳管于七步治理栈；**Redis 故障时 fail-closed 且审计必落库，该行为由 13 个单测锁定** |

**最后一条是工程含量最高、也最难被质疑的一条——比任何准确率都该往前放。**

核心原则：**写机制、写边界、写失败教训，不要写满分。**
`AB_REPORT` 里那句「改写不提升召回，纯开销 2.2s→61s」比任何 100% 都更像一个真正做过工程的人说的话。

---

## 五、验收标准（这套修复怎么算做完）

1. 页面每个数字都能在没有人工解释的情况下，被第三方在 2 分钟内验证：
   **数字 → 产物 → 数据集指纹 → 代码版本 → 复现命令**，链条不断；
2. 评测代码里不存在「无论如何都会 PASS」的断言（可 grep 验证）；
3. `pytest` + `ruff` + 前端 `lint/build` 全绿；
4. 服务可一键起（`scripts/dev_up.ps1`），能现场演示而非只放数字；
5. 主动列出的「已知边界」不少于 4 条，且每条都真实存在。

---

## 附：本轮复验命令清单

```powershell
# 1) 离线用例与 lint
envs\lunjiang\python.exe -m pytest tests/ -q          # → 103 passed
envs\lunjiang\python.exe -m ruff check .              # → All checks passed!

# 2) 规则层独立覆盖（不依赖 PG/Ollama）
envs\lunjiang\python.exe scripts\_audit_l1_coverage.py   # → 23/50 = 46.0%，误判 0

# 3) 语料就绪度
envs\lunjiang\python.exe scripts\_audit_corpus_count.py  # → 81 篇，缺失 0

# 4) 产物身份证
envs\lunjiang\python.exe scripts\_audit_provenance.py

# 5) 全量评测（需 PG/Ollama，约 22 分钟）
envs\lunjiang\python.exe -m evals.harness intent rag compression

# 6) 难度分层补测（需 PG/Ollama，约 1.8 小时）
envs\lunjiang\python.exe -m evals.eval_suites

# 7) 回归（需 PG/Ollama）
envs\lunjiang\python.exe evals\regression.py          # → 16 项 | PASS=16 FAIL=0 SKIP=0

# 8) 前端
cd frontend; npm run lint; npm run build
```
