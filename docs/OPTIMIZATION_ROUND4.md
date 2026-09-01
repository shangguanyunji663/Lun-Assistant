# 优化记录 · 第四轮（企业 RAG 知识库 + 多步规划 Agent）

> 本轮事由：结合企业级 RAG 知识库系统 / Agent 运维助手两个参考项目的设计思路，把论匠升级为**企业级智能论文知识库助手**。P0 与 P1 阶段落地完成。

## 一、改进总览

| 模块       | 升级内容                                                | 关键文件                                                                                                                                                                                                                                                                      |
| -------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 项目级私有知识库 | 多格式文档上传 → 解析 → 分块 → 向量化入库；MD5 去重；扫描件拒绝 | [parsers.py](file:///d:/PythonProject/Lun-Assistant/services/rag/ingest/parsers.py)、[pipeline.py](file:///d:/PythonProject/Lun-Assistant/services/rag/ingest/pipeline.py)、[knowledge.py](file:///d:/PythonProject/Lun-Assistant/infrastructure/models/knowledge.py) |
| 检索引擎     | 稠密 + 稀疏 + **相邻窗口**三引擎；项目知识库路 + 混合保底；精排降噪对比          | [retriever](file:///d:/PythonProject/Lun-Assistant/services/rag/retriever.py)、[pipeline](file:///d:/PythonProject/Lun-Assistant/services/rag/pipeline.py)                                                                                                                 |
| Query 改写 | 规则字典兜底 + jieba 关键词 + LLM 拒答/**语义漂移**检测回退            | [query\_rewrite](file:///d:/PythonProject/Lun-Assistant/services/rag/query_rewrite.py)                                                                                                                                                                                    |
| Agent 架构 | **Plan-Execute-Replan** 规划器接入主从图（supervisor 复杂任务路由） | [planner](file:///d:/PythonProject/Lun-Assistant/services/agent/planner.py)、[builder](file:///d:/PythonProject/Lun-Assistant/services/agent/builder.py)                                                                                                                   |
| 结构化产物    | 文献综述初稿 / 开题报告 / 答辩大纲（证据检索 + 模板生成 + 治理工具）            | [artifacts](file:///d:/PythonProject/Lun-Assistant/services/agent/artifacts.py)                                                                                                                                                                                           |
| 量化验收     | 七大必测场景自动化回归评测（16 项断言全 PASS）                         | [regression](file:///d:/PythonProject/Lun-Assistant/evals/regression.py)                                                                                                                                                                                                  |
| 知识库 API  | 上传 / 列表 / 删除 / 库内检索（project / hybrid 双模式）           | [projects 路由](file:///d:/PythonProject/Lun-Assistant/api/projects/router.py)                                                                                                                                                                                              |

## 二、设计决策（用户确认）

1. **解析库**：PyMuPDF + python-docx（提取质量优先）；
2. **数据模型**：`KnowledgeDocument` 只存文件元数据；向量分块**复用** **`MemoryItem(kind="user_doc")`**，直接并入既有 RAG 稠密/稀疏/精排链路，避免双轨检索代码；
3. **OCR**：本期不支持扫描版 PDF，检测到无可提取文本时记 `failed` 并返回明确错误。

## 三、知识库：上传 → 解析 → 分块 → 入库

```
POST /api/projects/{id}/knowledge  (multipart files)
  → ingest_document:
      infer_type(魔数/扩展名) → 大小上限 20MB → MD5 同项目去重
      → KnowledgeDocument(status=parsing)
      → parse_document（线程池内解析，PDF/DOCX/TXT/MD）
         · PDF 逐页 get_text，扫描件(< min_text_chars) 抛 DocumentParseError
         · DOCX 段落 + 表格
      → chunk_text 分块（复用语料分块口径 512/64）
      → 批量 embedding（32/批，bge-m3）→ MemoryItem(kind=user_doc, meta 含 doc_id/doc_key/chunk)
      → 原文件落盘 data/uploads/{project}/
      → status=ready + chunk_count/word_count
```

- 检索入口带 `project_id`：`hybrid` = 公共语料 + 该项目知识库；`project` = 仅库内。

- 隔离验证：项目 A 的文档不会出现在项目 B 的 `project_dense_search` 结果（回归 S2 PASS）。

- 删除文档：按 `doc_key` 定位清理全部向量分块 + 元数据 + 原始文件。

## 四、检索引擎：三引擎混合 + 精排降噪

召回阶段（S2）多路并进并经 RRF 融合：

| 路         | 说明                                                        |
| --------- | --------------------------------------------------------- |
| 稠密路       | bge-m3 向量检索公共语料（document/fact/summary）                    |
| 稀疏路       | BM25（jieba，语料域）                                           |
| 关键词路      | 改写关键词补一路 BM25（术语覆盖）                                       |
| 原始语料路     | 改写生效时保留原查询稠密锚点（防漂移，A/B 结论落地）                              |
| 项目知识库路    | 该项目 `user_doc` 稠密检索（跨项目隔离）                                |
| **相邻窗口路** | 命中块 ±window 邻块（按 meta 的 file/doc\_key + chunk 定位），补全跨块上下文 |

精排阶段（S3）降噪对比机制（`_noise_penalty`）：

- 稠密路命中且排名靠前 → `rerank_boost=1.0`（语义可信）；

- **仅稀疏路命中** → 软惩罚 `0.982`，标记 `noise_flag=sparse_only`（关键词重叠噪声）；

- 稠密命中但排名靠后 → 弱惩罚 `0.995`。

混合检索保底：项目知识库 Top-2 在相邻窗口二次融合**之后**注入精排候选，避免 1376 篇语料多路 RRF 把唯一项目路命中挤出 top20；最终排序仍由交叉编码器裁决（验证：RRF 查询下 kb.md 以 0.9945 排名第 2）。

## 五、Query 改写修复（历史痛点）

故障分析：本地改写器两类失效——① 拒答（"无法改写"）；② 语义漂移（改写偏离原查询、甚至换域）。此前失效直接回退原查询，召回增益为 0。

修复（三级）：

1. **关键词**：改由 jieba 词性过滤稳定提取（不依赖 LLM）；
2. **规则兜底**：学术场景前缀（开题/综述/答辩…）+ 术语同义池扩充；LLM 失败/拒答/过短/漂移（字符重合度 < 0.15）时回退规则改写而非原查询；
3. **策略标记**：返回 `strategy`（llm / rule / rule\_fallback / idle），便于观测。

实测：查询 "RRF" 时 agnes 改写为"色谱分析 Relative Response Factor"（换域漂移），重合度检测触发 → 回退规则改写 → 正确检索到倒数排名融合文档。

## 六、Planner：Plan-Execute-Replan

- `is_complex_task(user_input, intent)`：多动作词（≥3）或目标词（综述/开题/报告/大纲/方案…）或长输入+文献/写作意图 → supervisor 路由 `planner` 节点；

- Plan：LLM 产出 JSON（goal + ≤5 steps），action 限定为已注册治理工具或 `answer`；

- Execute：逐步经 `tool_registry.call()`（自动获得 RBAC / 限流 / 熔断 / 审计），前序产出累积为 evidence 注入后续步骤；

- Replan：步骤失败自动带"简化要求"重试一次，仍失败则记录并继续，部分成功不丢失；

- 汇总：Markdown 任务执行报告。

- 数值参数由 `_coerce_params` 归一化（`top_k`/`length` 等转 int），修复"切片 TypeError"类工具调用失败。

端到端验证（SSE 事件流）：`supervisor → planner(plan/step_event) → supervisor → final`，全部步骤 ✅。

## 七、结构化产物生成

`generate_artifact(kind, topic, requirement, references, project_id)`：

- `review_draft` 文献综述初稿（5 节骨架）、`proposal_report` 开题报告（6 节）、`defense_outline` 答辩大纲（6 节 + Q\&A≥8 条）；

- 生成前自动 RAG 检索证据并注入提示词，产物引用 \[编号] 标注来源；`evidence_count`/`sources` 随产物返回。

## 八、七大必测场景回归（evals/regression.py）

| 场景          | 覆盖                | 结果   |
| ----------- | ----------------- | ---- |
| S1 入库流水线    | 解析/去重/扫描件拒绝/分块落库  | PASS |
| S2 项目隔离     | B 项目检索不到 A 项目文档   | PASS |
| S3 三路召回     | RRF 融合顺序 + 相邻窗口语法 | PASS |
| S4 Query 改写 | 规则关键词 + 拒答回退策略    | PASS |
| S5  Planner | 复杂任务识别 + 节点装配     | PASS |
| S6 产物       | 模板覆盖 + 非法 kind 拒绝 | PASS |
| S7 治理       | 工具/配置一致性 + RBAC   | PASS |

运行：`envs\lunjiang\python.exe evals/regression.py`，结果落 `evals/regression_latest.json`。

## 九、实施中遇到的问题与修复（经验沉淀）

| # | 问题现象 | 根因 | 修复 |
| --- | --- | --- | --- |
| 1 | 入库时报 `_embed_chunks() takes 0 positional arguments but 1 given` | 调用处把首位参数按位置传，而函数签名是 keyword-only | 调用改为 `_embed_chunks(db=db, ...)` |
| 2 | 删除/相邻窗口查询报 `'BinaryExpression' object has no attribute 'astext'` | `memory_items.meta` 是 **JSON** 列（非 JSONB），只有 JSONB 支持 `.astext` | 全量改用 `func.json_extract_path_text(meta, key)`（按 `file`/`doc_key` + `chunk` 定位邻块） |
| 3 | Planner 步骤 `search_literature` 失败：先 "slice indices must be integers…"，降级后又 "missing required argument 'query'" | ① LLM 输出 `top_k:"5"` 字符串进 `fused[:top_k]` 触发切片 TypeError；② 治理栈 fallback_kwargs 整体替换入参，把 query 也换掉了 | 工具层 `search_literature` 强转并收敛 `top_k`；Planner `_coerce_params` 对 `top_k/length/max_tokens/window` 等数值参数归一化为 int |
| 4 | project 模式能命中 KB，但 hybrid 模式 KB 文档常不在 Top5 | 相邻窗口二次 RRF 融合（再次截断 top20）把"项目保底注入"的候选挤出 | 保底逻辑移到窗口融合**之后**注入精排候选，最终排序仍由精排裁决（kb.md 0.9945 入 Top-2 验证） |
| 5 | 回归脚本报 `relation "knowledge_documents" does not exist` | 表由 `main.py` lifespan 的 `create_all` 创建，独立脚本未建表 | 回归脚本入口先执行 `Base.metadata.create_all` |
| 6 | 临时脚本建 User 报 `'hashed_password' is an invalid keyword` | ORM 字段实为 `password_hash` | 使用正确字段名 |
| 7 | 端到端测试 multipart 多文件只上传了 1 个 | `httpx` 以 dict 传 `files` 时同名 key 相互覆盖 | 改用 `[("files", (filename, data, mime))]` 元组列表 |
| 8 | 冒烟时项目检索为空（hits=0） | 上传失败（#1/#7 连锁）导致无 user_doc 分块 | 修复上游后 project 模式 1 命中、hybrid 中 KB 入 Top-2 |

## 十、本轮修改文件清单

```
新增:
  infrastructure/models/knowledge.py          KnowledgeDocument 元数据模型
  services/rag/ingest/parsers.py              解析器工厂（PDF/DOCX/TXT/MD）
  services/rag/ingest/pipeline.py             上传→解析→分块→入库流水线
  services/agent/planner.py                   Plan-Execute-Replan 节点
  services/agent/artifacts.py                 结构化产物生成器
  evals/regression.py                         七大场景回归
修改:
  infrastructure/models/__init__.py           聚合注册新模型
  services/rag/retriever.py                   项目稠密检索 + 相邻窗口路
  services/rag/pipeline.py                    多路融合 + 保底 + 降噪
  services/rag/query_rewrite.py               规则兜底 + 漂移检测
  services/agent/builder.py / supervisor.py   planner 节点装配与路由
  services/governance/tools_impl.py           generate_artifact 注册
  configs/tools.yaml                          generate_artifact / topic_analysis 治理
  api/projects/router.py                      知识库管理 API（4 端点）
```

## 十一、验证清单

- [x] 上传 md/pdf/docx/txt 支持；MD5 同项目去重返回 skipped

- [x] 扫描版 PDF → failed + 明确错误，不污染检索

- [x] 项目知识库检索（project 模式）命中；跨项目隔离（回归 S2）

- [x] hybrid 模式知识库文档进入精排前 Top-2（保底生效）

- [x] 相邻窗口第三引擎 SQL 正确（meta JSON 列 json\_extract\_path\_text）

- [x] 改写拒答/漂移回退规则，关键词稳定产出

- [x] Planner 全事件流 success；结构化产物三类型骨架完整

- [x] 回归评测 16/16 PASS

