# 优化记录 · 第五轮（学术工具生态 + 并发压测 + 对话底座切换）

> ⚠️ **变更标注（2026-09-02 · 文档治理轮）**：本文档为混合轮次（主体 backend），其「五、前端：功能补齐与文墨山水画美化」一节属前端改进（文墨·浅黛主题源头，前端演进线 v8 前身），前端改进统一归档见 [`frontend-versions/README.md`](./frontend-versions/README.md)。

> 文档域：backend
> 文档类型：轮次记录
> 主题版本：—
> 轮次：ROUND5
> 日期：2026-09-01
> 状态：已落地

> 本轮 P2 阶段落地：学术工具生态（6 类）、并发压测与内存量化、agnes-2.5-flash 云上对话底座接入（对话/嵌入底座解耦）。

## 一、本轮改进总览

| 模块     | 内容                                                        | 关键文件                                                                                                                                                      |
| ------ | --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 学术工具生态 | 学术翻译 / 润色 / 研究方法推荐 / 参考文献格式化 / 摘要生成 / 术语解析                | [academic\_tools](file:///d:/PythonProject/Lun-Assistant/services/governance/academic_tools.py)                                                           |
| 治理接入   | 6 工具全部经 ToolRegistry（RBAC/限流/熔断/审计），tools.yaml 补齐配置       | [tools.yaml](file:///d:/PythonProject/Lun-Assistant/configs/tools.yaml)                                                                                   |
| 并发压测   | 知识库检索 QPS / 延迟 P50·P95 / 服务端内存采样，报告落盘                     | [load\_test](file:///d:/PythonProject/Lun-Assistant/scripts/load_test.py)                                                                                 |
| 对话底座   | 新增 agnes-2.5-flash（OpenAI 兼容）；**对话与嵌入底座解耦**，嵌入仍走本地 bge-m3 | [provider](file:///d:/PythonProject/Lun-Assistant/services/llm/provider.py)、[settings.yaml](file:///d:/PythonProject/Lun-Assistant/configs/settings.yaml) |
| 前端改造   | 知识库 UI 补齐（上传/列表/删除/检索+未命中回退）、Planner 事件渲染、**文墨山水画主题** | [App.jsx](file:///d:/PythonProject/Lun-Assistant/frontend/src/App.jsx)、[api.js](file:///d:/PythonProject/Lun-Assistant/frontend/src/api.js)、[styles.css](file:///d:/PythonProject/Lun-Assistant/frontend/src/styles.css) |
| 测试骨架/审计 | 治理层 call 流水线离线 pytest（9 用例）+ 发现 RBAC/限流拒绝不落审计盲区 → **已并入第六轮** | [OPTIMIZATION\_ROUND6](file:///d:/PythonProject/Lun-Assistant/docs/OPTIMIZATION_ROUND6.md) |

## 二、学术工具生态（P2-1）

| 工具                  | 类型      | 说明                           | 降级配置              |
| ------------------- | ------- | ---------------------------- | ----------------- |
| translate\_academic | LLM     | 中↔英学术翻译（术语规范译法）              | —                 |
| polish\_academic    | LLM     | 学术润色（formal/concise/plain）   | —                 |
| recommend\_method   | LLM+RAG | 研究方法推荐（证据检索 + 决策单）           | fallback question |
| format\_reference   | **规则**  | GB/T 7714 / APA 参考文献格式化，离线可用 | fallback style    |
| generate\_abstract  | LLM+RAG | 结构化摘要（目的/方法/结果/结论）           | fallback length   |
| term\_explain       | LLM+RAG | 术语两层解析（通俗 + 学术）              | —                 |

- 纯 LLM 工具限长输入（截 4000 字），防超时/OOM；

- 全部经治理栈调用：Planner 与专项 Agent 可直接编排；

- 回归 S7 校验"注册工具 ↔ tools.yaml 配置一一对应"（含历史遗漏的 `topic_analysis` 补录）。

## 三、并发压测（P2-2）

脚本：`scripts/load_test.py --concurrency 8 --total 40`（自动注册临时用户 → 建项目 → 上传样例 → 并发打 `/knowledge/search` → 采样服务进程内存）。

本机实测基线（Ollama bge-m3 本地 CPU + bge-reranker 精排，Linux 4 并发共 64 请求）：

| 指标                 | 数值                        |
| ------------------ | ------------------------- |
| 实际请求 / 成功率         | 64 / 100%                 |
| QPS                | 0.6                       |
| 延迟 P50 / P95 / Max | 4054ms / 9886ms / 16198ms |
| 服务端 RSS 内存         | 稳定 1497MB（增量为 0）          |

结论与口径：

- 检索含 bge-m3 稠密路（单次 CPU 嵌入 \~1s+）与交叉编码器精排（CPU 推理），并发下排队成为主瓶颈 → QPS 低是**本地 CPU 底座的天花板**，非代码缺陷；改造方向为 GPU 推理 / 向量缓存 / 异步队列（后续迭代）；

- 内存稳定（进程常驻、无泄漏迹象）；

- 报告自动写入 `evals/load_report.json`（并发/总数可配，便于在 GPU 或云端底座复测对比）。

## 四、agnes-2.5-flash 对话底座（配置切换）

背景：本机 Ollama 仅安装 bge-m3（嵌入手感良好），无本地对话模型；按用户授权接入云上 agnes-2.5-flash（OpenAI 兼容 `/v1/chat/completions`）。

关键设计——**对话与嵌入解耦**：

```yaml
llm:
  default_provider: agnes          # 对话底座（云端，KEY 在 .env AGNES_API_KEY）
  embedding_provider: ollama       # 嵌入底座（本地 bge-m3，离线可用）
```

- `LLMProvider` 分别解析对话与嵌入两套 client/model（`services/llm/provider.py`）；

- 嵌入维度仍取 `providers.ollama.embedding_dim=1024`，与既有 pgvector 表一致；

- 想回退纯本地：`ollama pull qwen3:4b && ollama create qwen3:4b-ctx4096 -f configs\ollama\Modelfile.qwen3-ctx4096`，再改 `default_provider: ollama`。

联通性实测：`chat_model=agnes-2.5-flash / embed_model=bge-m3`，对话与嵌入（1024 维）均正常。

> ⚠️ 安全提示：`.env` 中的 `AGNES_API_KEY` 为真实密钥，已被 `.gitignore` 排除（不会进入版本库）；团队共享时请勿复制该文件。

## 五、前端：功能补齐与文墨山水画美化

> 范围：前端对照后端新能力做一次"同步 + 美化"。后端能力在第四轮已就绪，但前端缺产品化入口；本轮补齐并整体换肤。

### 5.1 前端缺失项确认（对照后端能力）

| 后端能力 | 前端先前状态 | 本轮处理 |
| --- | --- | --- |
| 知识库 4 端点（上传/列表/删除/检索） | api.js 无 `knowledge*`，界面无入口 | 补齐 4 个 API + 知识库面板（见 5.2） |
| Planner 事件 `plan`/`step_event` | Timeline 未渲染、`NODE_TITLES` 无 planner | 事件过滤补 `plan`/`step_event`，节点名补 planner |
| 节点名对齐 | `writer_agent`/`defense_agent` 与代码 `writing_agent`/`ai_detect_agent` 不符 | 修正映射 + 补 ai_detect_agent |
| 结构化产物 / 学术工具 | 走对话触发即可 | 无需专门 UI，保留 |
| 项目删除 | `deleteProject` 有 API 无入口 | 暂不暴露（避免误删，聚焦本轮） |

### 5.2 补齐的功能

- **api.js**：`uploadKnowledge`（FormData 多文件，不手动设 Content-Type）、`listKnowledge`、`deleteKnowledge`、`searchKnowledge(projectId, query, top_k, mode)`；
- **KnowledgePanel**（App.jsx 新组件，挂在右栏"项目知识库"tab）：
  - 上传：点击 / 拖拽（drag & drop），格式 PDF/DOCX/TXT/MD、单文件 ≤20MB、同内容去重提示；逐文件返回 `ready / skipped / failed` 徽章与错误说明；
  - 资料清单：格式图标 + 状态徽章 + 分块数/字数 + 单行删除（confirm 二次确认，`ready` 才显示）；
  - 库内检索：输入 + `hybrid`/`库内` 模式切换；命中卡片标注来源（📄知识库 / 📚公共语料）、`score`、`noise_flag`；
  - **未命中回退**：`库内(project)` 模式无命中时自动再以 `hybrid` 检索公共语料兜底，并提示"已为你检索公共语料"（见 5.4 问题修复）；
- **时间线**：`plan`（📋 规划目标·步数）与 `step_event`（步骤 i/n · 动作 · ✓/⚠）事件渲染，时间线呈批注式墨点节点；
- 未选项目时知识库面板显示引导语（设计约束，保留）。

### 5.3 青绿设色山水主题（终版：文墨山水 · 浅黛）

方案比选：初版**学术文卷风**（暖米白宣纸）被否；改**墨韵山水·暗墨**被否（黢黑）；最终定为**青绿设色山水（浅黛版）**——冷调月白底让"山看得见"，避免米黄与黢黑两个极端，紧扣"论匠 = 论文全流程智能助手"定位（知识库只是项目辅助，不喧宾夺主）。

- **配色**：月白冷底 `#F2F3EF` → 次级面 `#E7E9E4`；墨青正文 `#26292E` / 次级 `#4E545C`；强调色仅**印泥红**（印章/落款），辅以竹青竖线、赭金题跋、黛青信息、青绿成功；
- **背景 = 真山水**：`body::before`/`::after` 用两叠 `clip-path` 锯齿山峦（远山淡青 → 近山黛青，`mix-blend-multiply` 近浓远淡）+ 顶部云气留白 radial 高光，画面是"画"而非纯底色；
- **字体**：标题/品牌楷体（`Kaiti SC/STKaiti`，题跋感）；正文黑体、代码等宽；
- **品牌**：顶栏"论匠"楷体大字 + 印泥红"论"字印章块（落款点睛）；
- **布局**：对话为主（左侧宽栏）、右栏双 tab（执行时间线 / 项目知识库）；用户气泡印泥红块面、助手气泡近白卡片 + 竹青左竖线（如卷边批注）；
- **交互**：卡片淡入 `fadeUp`、输入聚焦黛青晕染、语义色克制（青绿成功 / 赭金提醒 / 印泥红错误）。

视觉决策过程（用户参与）：学术文卷（A）→ 深色开发者（B）→ 清新工作台（C）→ 专业控制台（D）四选一偏好 A → 明确要求"文墨山水、不要米白宣纸"（暗墨亦否）→ 终版青绿设色山水（浅黛）；交互上要求"未命中也能检索默认资料"并已实现（见 5.4）。

### 5.4 发现的问题与解决（前端专项）

| 问题 | 根因 | 解决 |
| --- | --- | --- |
| 时间线看不到 Planner 步骤 | SSE 事件过滤未含 `plan`/`step_event`；`NODE_TITLES` 用了旧节点名（writer/defense） | 事件过滤补两类事件；节点名对齐 `writing_agent`/`ai_detect_agent` 并补 `planner` |
| 库内检索未命中只能看到"未命中" | 后端 `mode=project` 无命中即空结果，无预览 | 前端自动回退 `hybrid` 再查一次公共语料，提示"已为你检索公共语料"，命中卡片保留来源标注 |
| 主题两轮被否 | 初稿学术文卷风=暖米白宣纸；改墨韵山水=黢黑过头 | 最终青绿设色山水（浅黛）：冷月白底 + clip-path 山峦剪影 + 竹青/印泥点缀，浏览器实测底色 rgb(242,243,239)、山形可见（见 5.3） |
| 浏览器实测：未选项目时知识库面板不渲染上传区 | 产品设计约束（知识库以项目为作用域） | 保留引导提示"请先选择或新建论文项目"，属预期行为 |

验证：`npm run build`（285 模块编译通过）；浏览器实测登录页/对话页/知识库面板/检索接口全流程正常，无 JS 报错。

## 六、实施中遇到的问题与修复（经验沉淀）

| # | 问题现象                                           | 根因                                                                                   | 修复                                                                                                                                           |
| - | ---------------------------------------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | 改写/对话全部失败 `model 'qwen3:4b-ctx4096' not found` | 本机 Ollama 无本地对话模型（仅 bge-m3），旧配置指向不存在的镜像                                              | 接入 agnes-2.5-flash 云上对话底座（KEY 已填 .env），同时**对话/嵌入双底座解耦**：`default_provider=agnes` + `embedding_provider=ollama`，嵌入仍走本地 bge-m3，pgvector 维度保持一致 |
| 2 | 改写日志刷 `LLM 未返回 JSON`                           | agnes 在 json\_mode 下偶发返回非 JSON 文本                                                    | 由 rewrite\_query 的异常→规则兜底链路消化（不改主流程）；并实测验证**漂移检测**拦截了 RRF 被改写成"色谱分析"的换域误改                                                                    |
| 3 | 压测报告成功率 400%                                   | 脚本把并发×总数当成请求总数，统计分母错误                                                                | 计数实际完成请求 `done`，QPS=done/elapsed、成功率=ok/done（复测 64 请求 100%）                                                                                  |
| 4 | Windows 下 `psycopg ... ProactorEventLoop` 告警   | psycopg 异步连接池要求 Selector 事件循环；告警仅出现在部分子路径（checkpointer），主进程已在 main.py 设置 Selector 策略 | 记录为已知平台限制：checkpointer 三级降级到进程内存（开发模式可用），不影响业务主链路                                                                                            |

## 七、本轮修改文件清单

```
新增:
  services/governance/academic_tools.py    6 类学术工具
  scripts/load_test.py                     并发压测 + 内存采样 + 报告
  evals/load_report.json                   压测报告（本机基线）
修改:
  services/llm/provider.py                 对话/嵌入双底座解耦
  services/governance/tools_impl.py        注册 academic 工具
  configs/settings.yaml                    default_provider=agnes + embedding_provider
  configs/tools.yaml                       6 工具治理配置
  requirements.txt                         psutil
  .env / .env.example                      AGNES_BASE_URL / AGNES_API_KEY
  frontend/src/api.js                      知识库 4 接口（上传/列表/删除/检索）
  frontend/src/App.jsx                     KnowledgePanel + 事件渲染 + 节点名修正 + 未命中回退
  frontend/src/styles.css                  文墨山水画主题全量换肤
```

## 八、验证清单

- [x] 6 类学术工具注册并经治理栈调用（回归 S7 PASS）
- [x] format_reference GB/T 7714 与 APA 输出正确（纯规则、离线）
- [x] term_explain 串联 RAG+LLM 产出完整解释
- [x] 压测 100% 成功率，P50/P95/QPS 落盘，服务内存稳定
- [x] agnes 对话 + bge-m3 嵌入双底座联通（1024 维）
- [x] Query 改写漂移保护在 agnes 底座下同样生效（RRF 换域改写被拦截回退）
- [x] 前端 `npm run build` 编译通过（285 模块）
- [x] 浏览器实测：登录/注册/建项目 → 知识库面板（上传区/检索/清单）→ 库内检索接口全流程可用，无 JS 报错
- [x] `库内`模式未命中自动回退公共语料（hybrid）并给出提示

## 九、治理层测试骨架（已并入第六轮）

> 本节原有内容（治理层 `call()` 流水线离线 pytest 测试骨架 + 审计盲区发现）已并入 **第六轮** `OPTIMIZATION_ROUND6.md`（架构改进与工程化治理），避免跨轮重复。审计盲区的修复建议仍在第六轮第八节跟踪。

