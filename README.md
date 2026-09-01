# 论匠 · LunJiang

基于 **LangGraph 主从多智能体架构** 的论文全流程智能助手：选题分析 → 文献检索 → 论文写作 → 格式校验 → 查重降重 → 答辩准备。配套 **项目级知识库**、**四层记忆**、**三阶段 RAG**、**工具治理** 与 **全链路可观测**。

> 技术栈：Python 3.11 + FastAPI + LangGraph + PostgreSQL(pgvector) + Redis + Ollama + React 18 + Vite（对话底座可切换云端 agnes-2.5-flash，嵌入走本地 bge-m3）

## 文档导航

| 文档                                      | 用途                                |
| --------------------------------------- | --------------------------------- |
| [📖 学习指南](docs/LEARNING_GUIDE.md)       | 从零理解并重建本项目（推荐先读）                  |
| [📐 架构总览](#目录结构)                        | 分层结构与模块职责                         |
| [🛠 优化记录一](docs/OPTIMIZATION_ROUND1.md) | 第一轮优化（性能/安全/体验）                   |
| [🛠 优化记录二](docs/OPTIMIZATION_ROUND2.md) | 第二轮优化（OOM 修复/结构重构方案）              |
| [🛠 优化记录三](docs/OPTIMIZATION_ROUND3.md) | 第三轮优化（布尔陷阱/前端全按钮失效排查）             |
| [🛠 优化记录四](docs/OPTIMIZATION_ROUND4.md) | 第四轮优化（RAG知识库/多引擎检索/Planner/结构化产物） |
| [🛠 优化记录五](docs/OPTIMIZATION_ROUND5.md) | 第五轮优化（学术工具生态/并发压测/agnes对话底座）      |
| [🛠 优化记录六](docs/OPTIMIZATION_ROUND6.md) | 第六轮优化（架构改进与工程化治理/P0修复/测试骨架）       |
| [🛠 优化记录七](docs/OPTIMIZATION_ROUND7.md) | 第七轮修改（前端视觉重构：青绿长卷/会话卷册/山水浓度滑杆） |
| [📋 目录结构审查](docs/ARCHITECTURE_REVIEW.md) | 目录合理性评估（问题清单 + 优化建议）          |
| [💡 常见问题](#常见问题)                        | 排障手册                              |

## 快速开始

### 0. 环境准备

依赖：Python 3.11（conda）、Node 18+、PostgreSQL 15+（pgvector）、Redis 6+、Ollama（嵌入 bge-m3 必需）。

```powershell
# Ollama：新开窗口常驻启动，拉取嵌入模型（对话走默认云端 agnes，见第 5 轮优化记录）
ollama serve
ollama pull bge-m3

# （可选）本地对话回退：拉 qwen3 并创建 16GB 内存适配镜像，再把 default_provider 改回 ollama
ollama pull qwen3:4b
ollama create qwen3:4b-ctx4096 -f configs\ollama\Modelfile.qwen3-ctx4096   # 固定 num_ctx=4096，防 KV Cache OOM
```

> 💡 **对话/嵌入双底座**：默认 `llm.default_provider=agnes`（云端 agnes-2.5-flash，Key 在 `.env` 的 `AGNES_API_KEY`，`copy .env.example .env` 即含占位）；`llm.embedding_provider=ollama`（本地 bge-m3，离线可用）。16GB 内存机器如需全本地：Ollama 的 `/v1` 兼容端点不认请求级 `options`，用 Modelfile 给 `qwen3:4b` 建 `qwen3:4b-ctx4096` 镜像副本（blob 复用，几乎不占额外磁盘）并切换 provider。

### 1. 初始化环境

```powershell
conda create -p envs\lunjiang python=3.11 -y
conda run -p envs\lunjiang pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
copy .env.example .env     # 修改 PG / Redis 连接信息
```

独立 PostgreSQL（端口 5433）：`D:\Develop\DB\PostgreSQL16\Library\bin\pg_ctl -D D:\Develop\DB\PostgreSQL16\data start|stop`

### 2. 初始化数据

```powershell
envs\lunjiang\python.exe scripts/check_env.py          # 连通性检查（Ollama/Redis/PG/pgvector）
envs\lunjiang\python.exe scripts/ingest_corpus.py      # data/corpus/*.txt 入库（--force 重建）
```

### 3. 启动

```powershell
# 后端（窗口1）
envs\lunjiang\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000

# 前端（窗口2，PowerShell 用 ; 分隔，不要用 &&）
cd frontend; npm install; npm run dev                   # 前端 5173，/api 代理到 8000
```

浏览器打开 <http://localhost:5173>：注册 → 登录 → 新建项目 → 发起对话。

### 4. 冒烟与评测

```powershell
envs\lunjiang\python.exe scripts/smoke_memory.py       # 四层记忆 + 压缩
envs\lunjiang\python.exe scripts/smoke_rag.py          # 三阶段检索
envs\lunjiang\python.exe scripts/smoke_governance.py   # 治理栈 9 项
envs\lunjiang\python.exe scripts/smoke_trace.py        # Trace 回放
envs\lunjiang\python.exe scripts/smoke_api.py --topic  # 端到端（需 uvicorn 已启动）
envs\lunjiang\python.exe evals/harness.py              # 三项指标评测
envs\lunjiang\python.exe evals/regression.py           # 七大必测场景回归评测
envs\lunjiang\python.exe -m pytest tests/ -q           # 离线单元测试（治理/模型/改写等 48 用例，无外部依赖）
envs\lunjiang\python.exe scripts/load_test.py          # 知识库检索并发压测（需 uvicorn 已启动）
```

## 核心特性

| 模块      | 说明                                                                            | 关键实现                                    |
| ------- | ----------------------------------------------------------------------------- | --------------------------------------- |
| 多智能体编排  | 1 主控 Supervisor 调度 6 类专项 Agent + **Plan-Execute-Replan 规划器**（复合任务），最大 3 跳防回环  | `services/agent/`                       |
| 意图预分类   | 规则 → 向量原型 → LLM 兜底三级，56ms / 100% 准确                                           | `services/classifier/intent.py`         |
| 项目级知识库  | 多格式上传(PDF/DOCX/TXT/MD)→解析→分块→向量化入库，MD5去重/扫描件拒绝/跨项目隔离，`project`/`hybrid` 双模式检索 | `services/rag/ingest/`                  |
| 三阶段 RAG | Query 改写(规则兜底+防漂移，返回策略标记) → 稠密+稀疏+**相邻窗口**多路 RRF 融合(项目保底) → 交叉精排+降噪对比         | `services/rag/`                         |
| 结构化产物   | 综述初稿 / 开题报告 / 答辩大纲（模板骨架 + RAG 证据注入，治理工具 `generate_artifact`）                  | `services/governance/artifacts.py`   |
| 学术工具生态  | 翻译 / 润色 / 方法推荐 / 参考文献格式化 / 摘要生成 / 术语解析                                        | `services/governance/academic_tools.py` |
| 工具治理    | RBAC → 限流 → 熔断 → 三级容错（重试/降级/人机兜底）→ 分布式锁 → 审计 → 行为观测 → Skill（论文 8 类 + 学术 6 类共 14 个工具统一经治理栈，同步 handler 自动线程池化）        | `services/governance/`                  |
| 四层记忆    | 短期(Redis)/结构化/长期(pgvector)/偏好 + 压缩                                            | `services/memory/`                      |
| SSE 流式  | EventHub 事件总线 + token 微缓冲                                                     | `services/streaming/hub.py`             |
| 人机介入    | LangGraph interrupt 挂起 → /resume 续跑                                           | `api/agent/router.py`                   |
| 全链路可观测  | Trace/Log/Memory/Action 统一 Span，树形回放                                          | `services/observability/`               |

## 目录结构

```
main.py              FastAPI 入口（启动命令 uvicorn main:app）
api/                 接口层（FastAPI 路由 + 共享依赖 + 响应模型）
  ├─ auth/           注册/登录/JWT（/me 当前用户）
  ├─ projects/       论文项目 CRUD（知识库已拆分至 knowledge/）
  ├─ knowledge/      项目级私有知识库（上传/列表/删除/库内检索，独立聚合根）
  ├─ agent/          /chat (SSE) /resume 人机介入（编排在 ConversationService）
  ├─ observability/  Trace 回放（admin）
  ├─ deps.py         路由共享依赖（get_owned_project 项目归属校验）
  └─ middleware/     审计中间件（fire-and-forget）
services/            业务服务层（不得 import api/，可独立测试）
  ├─ agent/          LangGraph 主从图 + specialists/（6 专项 Agent）+ planner + conversation_service（对话编排）
  ├─ rag/            RAG 流水线（改写/多路召回/精排） + ingest/（语料与知识库入库）
  ├─ memory/         四层记忆 + 压缩
  ├─ governance/     工具治理与实现（限流/熔断/重试/锁/RBAC/Skill/学术工具 + artifacts 结构化产物）
  ├─ classifier/     三级意图分类
  ├─ streaming/      事件总线（SSE 微缓冲）
  ├─ checkpoint/     三级降级检查点
  ├─ llm/            LLM 统一接入（全项目统一 LLMProvider，无 langchain 适配层）
  └─ observability/  Trace Span
infrastructure/      基础设施层（地基，谁都得经过它）
  ├─ config.py       settings.yaml + .env + 单例
  ├─ paths.py        路径常量单一真源（PROJECT_ROOT/CONFIG_DIR/DATA_DIR/EVALS_DIR）
  ├─ db.py           SQLAlchemy 异步引擎
  ├─ redis_client.py asyncio Redis
  ├─ audit.py        审计写库（参数截断 + 指纹化）
  ├─ rbac/           角色策略
  └─ models/         ORM（users/projects/memory/trace/audit/skill/knowledge）
configs/             settings.yaml / rbac.yaml / tools.yaml / ollama/Modelfile
evals/               评测 Harness + A/B + 七大场景回归
scripts/             初始化 + 冒烟 + 压测脚本
frontend/            React 18 + Vite（SSE 对话 / Markdown / 时间线 / 项目知识库面板）
docs/                文档（学习指南 / 优化记录）
```

依赖方向：`api → services → infrastructure → configs`，禁止反向。

## 配置要点

- **`.env`**：`SECRET_KEY`（生产必改）、`APP_*`、`PG_*`、`REDIS_*`、云厂商 `*_API_KEY`（切换 provider 时填）、`AGNES_BASE_URL` / `AGNES_API_KEY`（默认对话底座）

- **`configs/settings.yaml`**：`llm.default_provider` 一键切换对话底座（ollama/deepseek/zhipu/qwen/**agnes**）；`llm.embedding_provider` 与对话解耦（推荐云端对话 + 本地 bge-m3 嵌入）；pgvector 向量列维度由 `llm.providers.<底座>.embedding_dim` **动态决定**（`infrastructure/config.get_embedding_dim()`，不再硬编码 1024），嵌入底座返回维度不符时运行时抛错，切换底座若维度变化需重建 `memory_items` 表或迁移数据（当前未引入 Alembic）

- **RAG 检索键**：`rag.rewrite_enabled`（Query 改写开关，可按语料规模调）、`rag.sibling_window`（相邻窗口第三引擎半径，0=关闭）、`rag.max_upload_size_mb`（知识库单文件上限）、`rag.knowledge.upload_dir`（原始文件落盘目录，默认 `data/uploads/`，已 gitignore）、`rag.knowledge.min_text_chars`（低于该字数视为扫描件/空文档拒绝）

- **知识库使用**：`POST /api/projects/{id}/knowledge` 上传（PDF/DOCX/TXT/MD，可多文件）→ 自动解析分块向量化入库；`.../knowledge/search` 支持 `mode=project`（仅库内）与 `mode=hybrid`（公共语料+库内融合）；详细的调用示例见 [学习指南第 16 课](docs/LEARNING_GUIDE.md#第-16-课-项目知识库与复合任务规划第-45-轮扩展)

## API 速览

| 分组       | 端点                                                                                    | 鉴权     |
| -------- | ------------------------------------------------------------------------------------- | ------ |
| Auth     | `POST /api/auth/register`、`POST /api/auth/login`、`GET /api/auth/me`                  | 前两者免鉴权；`/me` 需 Bearer |
| Projects | `POST/GET /api/projects`、`GET/PATCH/DELETE /api/projects/{id}`                        | Bearer |
| 知识库      | `POST/GET/DELETE /api/projects/{id}/knowledge[/{doc_id}]`、`POST .../knowledge/search` | Bearer |
| Agent    | `POST /api/agent/chat`（SSE）、`POST /api/agent/resume`                                  | Bearer |
| Trace    | `GET /api/observability/traces`、`GET /api/observability/traces/{trace_id}`            | admin  |

## 常见问题

- **Ollama 返回 500（KV Cache OOM）**：参考 [优化记录二](docs/OPTIMIZATION_ROUND2.md)（`num_ctx=4096` 已由 Modelfile 镜像固化）；当前对话默认走云端 agnes，此问题主要影响本地回退场景

- **端口冲突**：项目 PG 固定 5433，独立于系统 5432

- **中文乱码**：全部文件保持 UTF-8（已配 `.editorconfig` + IDE settings）

- **知识库上传返回 failed（扫描件）**：扫描版 PDF 无可提取文本，本期不支持 OCR，接口返回 `status=failed` + 错误说明；请上传含文本层的 PDF 或 DOCX/TXT/MD

***

<p align="center">详细教学与实现解析请阅读 <a href="docs/LEARNING_GUIDE.md">docs/LEARNING_GUIDE.md</a></p>
