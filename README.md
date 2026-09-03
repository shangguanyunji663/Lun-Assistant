# 论匠 · LunJiang

论匠（LunJiang）是一套面向**毕业论文 / 学术论文写作全流程**的多智能体辅助平台：基于 LangGraph 主从式编排，一个主控 Supervisor 统一调度六类专项 Agent（选题 / 文献 / 写作 / 格式 / 查重 / 答辩），配合 Plan-Execute-Replan 规划器处理复合任务，覆盖选题分析 → 文献检索 → 论文写作 → 格式校验 → 查重降重 → 答辩准备，并配套**项目级知识库**、**四层记忆**、**三阶段 RAG**、**工具治理**与**全链路可观测**。前后端分离：后端 FastAPI 异步服务，前端 React 18 + Vite 单页应用。

> 技术栈：Python 3.11 + FastAPI + LangGraph + PostgreSQL(pgvector) + Redis + Ollama + React 18 + Vite（对话与嵌入均走本地 Ollama：qwen3:4b-ctx4096 + bge-m3）

## 文档导航

> ⚠️ **变更标注（2026-09-02 · 文档治理轮）**：前端版本演进文档（v8→v12）已统一归入 [`docs/frontend-versions/`](docs/frontend-versions/README.md)，原 `docs/`、`design-concepts/`、`frontend/` 下的迁移残留 stub 文档已清理。统一格式规范见 [`docs/FORMAT_STANDARD.md`](docs/FORMAT_STANDARD.md)。

### 通用 / 后端工程线（docs/）

| 文档                                        | 用途                                                                                                                            |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| [📖 学习指南](docs/LEARNING_GUIDE.md)         | **三部分**：设计推演（第 0–16 课）/ 八大能力模块解剖（第 0 课基础设施层地基 + 第 17–25 课，含最小可复现骨架）/ 从零复现（第 26–28 课）+ 四附录（调用链 / 依赖矩阵 / FAQ / 设计决策回溯）。推荐先读第一部分 |
| [📐 架构总览](#目录结构)                          | 分层结构与模块职责                                                                                                                     |
| [📋 目录结构审查](docs/ARCHITECTURE_REVIEW.md)  | 目录合理性评估（问题清单 + 优化建议）                                                                                                          |
| [📂 项目结构说明](docs/PROJECT_STRUCTURE.md)    | 目录与关键文件用途说明（2026-09-02 归档）                                                                                                    |
| [📐 统一格式规范](docs/FORMAT_STANDARD.md)      | 全部 Markdown 文档的格式规范                                                                                                           |
| [🛠 优化记录一](docs/OPTIMIZATION_ROUND1.md)   | 第一轮优化（性能/安全/体验）                                                                                                               |
| [🛠 优化记录二](docs/OPTIMIZATION_ROUND2.md)   | 第二轮优化（OOM 修复/结构重构方案）                                                                                                          |
| [🛠 优化记录三](docs/OPTIMIZATION_ROUND3.md)   | 第三轮优化（布尔陷阱/前端全按钮失效排查）                                                                                                         |
| [🛠 优化记录四](docs/OPTIMIZATION_ROUND4.md)   | 第四轮优化（RAG知识库/多引擎检索/Planner/结构化产物）                                                                                             |
| [🛠 优化记录五](docs/OPTIMIZATION_ROUND5.md)   | 第五轮优化（学术工具生态/并发压测/agnes对话底座）                                                                                                  |
| [🛠 优化记录六](docs/OPTIMIZATION_ROUND6.md)   | 第六轮优化（架构改进与工程化治理/P0修复/测试骨架）                                                                                                   |
| [🛠 优化记录十二](docs/OPTIMIZATION_ROUND12.md) | 第十二轮优化（静态检查接入CI/依赖锁定/前端Hooks/可移植性）                                                                                            |
| [🛠 优化记录十三](docs/OPTIMIZATION_ROUND13.md) | 第十三轮优化（审计参数合规/Query改写自适应/记忆召回排序/多实例部署）                                                                                        |
| [🚀 部署指南](docs/DEPLOY.md)                 | GitHub Pages 自动部署到 `https://shangguanyunji663.github.io/Lun-Assistant/`                                                       |
| [💡 常见问题](#常见问题)                          | 排障手册                                                                                                                          |

### 前端版本线（docs/frontend-versions/，v8 → v12）

| 文档                                                                 | 版本  | 用途                                        |
| ------------------------------------------------------------------ | --- | ----------------------------------------- |
| [🧭 版本线索引](docs/frontend-versions/README.md)                       | —   | 前端版本演进总索引（新增版本入口）                         |
| [🧩 版本模板](docs/frontend-versions/TEMPLATE.md)                      | —   | 新增版本直接套用                                  |
| [🎨 视觉三方向提案](docs/frontend-versions/VISUAL_DIRECTIONS.md)          | v8  | 青绿长卷 / 水墨改良 / 暗墨金线 提案                     |
| [📐 设计规范](docs/frontend-versions/DESIGN_SPEC.md)                   | v9  | 青绿长卷·放松版设计令牌规范                            |
| [🛠 优化记录七](docs/frontend-versions/OPTIMIZATION_ROUND7.md)          | v9  | 前端视觉重构：青绿长卷/会话卷册/山水浓度滑杆                   |
| [🛠 优化记录八](docs/frontend-versions/OPTIMIZATION_ROUND8.md)          | v10 | 前端功能同步 + 三主题切换（生产代码落地）                    |
| [🛠 优化记录九](docs/frontend-versions/OPTIMIZATION_ROUND9.md)          | v10 | 主题图 WebP 压缩 5.32→0.26MB + GitHub Pages 部署 |
| [🛠 优化记录十](docs/frontend-versions/OPTIMIZATION_ROUND10.md)         | v10 | v10 遗留项落地：内置模式 / B-C 装饰 / 音效 / 移动端 / 截图   |
| [📝 v11 变更（设计稿侧）](docs/frontend-versions/CHANGELOG-v11-design.md)  | v11 | 四主题 A/B/C/D · preview/tuner.html 重构       |
| [📝 v11 变更（生产侧）](docs/frontend-versions/CHANGELOG-v11-frontend.md) | v11 | 四主题 · frontend/ 端到端改造                     |
| [📝 v12 变更（设计稿侧）](docs/frontend-versions/CHANGELOG-v12.md)         | v12 | B 主题黑白瑞士 · 设计稿侧                           |
| [🛠 优化记录十一](docs/frontend-versions/OPTIMIZATION_ROUND11.md)        | v12 | B 主题由水墨留白翻转为黑白瑞士（修复 B↔D 区分度）              |

## 核心特性

| 模块      | 说明                                                                                                           | 关键实现                                    |
| ------- | ------------------------------------------------------------------------------------------------------------ | --------------------------------------- |
| 多智能体编排  | 1 主控 Supervisor 调度 6 类专项 Agent + **Plan-Execute-Replan 规划器**（复合任务），最大 3 跳防回环                                 | `services/agent/`                       |
| 意图预分类   | 规则 → 向量原型 → LLM 兜底三级，22 条样本 100% 准确（`evals/datasets/intent.jsonl`）                                           | `services/classifier/intent.py`         |
| 项目级知识库  | 多格式上传(PDF/DOCX/TXT/MD)→解析→分块→向量化入库，MD5去重/扫描件拒绝/跨项目隔离，`project`/`hybrid` 双模式检索                                | `services/rag/ingest/`                  |
| 三阶段 RAG | Query 改写(难度自适应 off/auto/on + 规则兜底+防漂移，返回策略标记) → 稠密+稀疏+**相邻窗口**多路 RRF 融合(项目保底) → 交叉精排+降噪对比                    | `services/rag/`                         |
| 结构化产物   | 综述初稿 / 开题报告 / 答辩大纲（模板骨架 + RAG 证据注入，治理工具 `generate_artifact`）                                                 | `services/governance/artifacts.py`      |
| 学术工具生态  | 翻译 / 润色 / 方法推荐 / 参考文献格式化 / 摘要生成 / 术语解析                                                                       | `services/governance/academic_tools.py` |
| 工具治理    | RBAC → 限流 → 熔断 → 三级容错（重试/降级/人机兜底）→ 分布式锁 → 审计 → 行为观测 → Skill（论文 8 类 + 学术 6 类共 14 个工具统一经治理栈，同步 handler 自动线程池化） | `services/governance/`                  |
| 四层记忆    | 短期(Redis)/结构化/长期(pgvector)/偏好 + 压缩                                                                           | `services/memory/`                      |
| SSE 流式  | EventHub 事件总线 + token 微缓冲                                                                                    | `services/streaming/hub.py`             |
| 人机介入    | LangGraph interrupt 挂起 → /resume 续跑                                                                          | `api/agent/router.py`                   |
| 全链路可观测  | Trace/Log/Memory/Action 统一 Span，树形回放                                                                         | `services/observability/`               |

## 快速开始

### 0. 环境准备

**依赖清单**（端口约定以本表为准：PG **5433** / Redis 6379 / Ollama 11434）

| 依赖         | 版本要求                           | 用途                   | 连接地址（默认）          |
| ---------- | ------------------------------ | -------------------- | ----------------- |
| Python     | 3.11（conda 环境 `envs/lunjiang`） | 后端运行时                | —                 |
| Node.js    | 18+                            | 前端构建（Vite 5）         | —                 |
| PostgreSQL | 15+（含 pgvector 扩展）             | 主存储：业务表 + 向量记忆 + 知识库 | `127.0.0.1:5433`  |
| Redis      | 6+                             | 短期记忆 / 限流窗口 / 分布式锁   | `127.0.0.1:6379`  |
| Ollama     | 最新版                            | 本地嵌入模型 bge-m3        | `127.0.0.1:11434` |

**启动基础设施（顺序：PG → Redis → Ollama）**

应用启动时会立即连接 PostgreSQL 建表（`main.py` lifespan），因此**必须先启动数据库**，否则后端会直接启动失败（`ConnectionRefusedError: [WinError 1225]`）。

```powershell
# 1) PostgreSQL（独立实例，端口 5433）
D:\Develop\DB\PostgreSQL16\Library\bin\pg_ctl -D D:\Develop\DB\PostgreSQL16\data start

# 2) Redis（端口 6379；若注册为 Windows 服务则直接 net start Redis）
redis-server

# 3) Ollama：新开窗口常驻启动，拉取嵌入与对话模型
ollama serve
ollama pull bge-m3
ollama pull qwen3:4b
ollama create qwen3:4b-ctx4096 -f configs\ollama\Modelfile.qwen3-ctx4096   # 固定 num_ctx=4096，防 KV Cache OOM（默认 default_provider=ollama 必需）
```

**停止 PostgreSQL**：`D:\Develop\DB\PostgreSQL16\Library\bin\pg_ctl -D D:\Develop\DB\PostgreSQL16\data stop`

**连通性自检**（可选）：

```powershell
netstat -ano | findstr ":5433 :6379 :11434"   # 看到 LISTENING 即正常
```

### 1. 初始化环境

```powershell
conda create -p envs\lunjiang python=3.11 -y
conda run -p envs\lunjiang pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
copy .env.example .env     # 修改 PG / Redis 连接信息（详见下文「配置方法」）
```

### 2. 初始化数据

```powershell
envs\lunjiang\python.exe scripts/check_env.py          # 连通性检查（Ollama/Redis/PG/pgvector；默认对话底座为本地 ollama，全项可直测）
envs\lunjiang\python.exe scripts/ingest_corpus.py      # data/corpus/*.txt 入库（--force 重建）
```

### 3. 启动应用

```powershell
# 后端（窗口1）
envs\lunjiang\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000

# 前端（窗口2，PowerShell 用 ; 分隔，不要用 &&）
cd frontend; npm install; npm run dev                   # 前端 5173，/api 代理到 8000
```

浏览器打开 <http://localhost:5173>：注册 → 登录 → 新建项目 → 发起对话。

### 4. 冒烟与评测

```powershell
envs\lunjiang\python.exe scripts/smoke_memory.py       # 四层记忆 + 压缩（需 PostgreSQL）
envs\lunjiang\python.exe scripts/smoke_rag.py          # 三阶段检索（需 PostgreSQL+Ollama，语料已入库）
envs\lunjiang\python.exe scripts/smoke_governance.py   # 治理栈自检（需 Redis/PostgreSQL/Ollama）
envs\lunjiang\python.exe scripts/smoke_trace.py        # Trace 回放（需 PostgreSQL）
envs\lunjiang\python.exe scripts/smoke_graph.py        # Agent 图编译检查（需 LLM 底座可达）
envs\lunjiang\python.exe scripts/smoke_api.py --topic  # 端到端（需 uvicorn 已启动）
envs\lunjiang\python.exe evals/harness.py              # 三项指标评测（需 PostgreSQL+Ollama）
envs\lunjiang\python.exe evals/regression.py           # 七大必测场景回归评测（需 PostgreSQL+LLM 底座）
envs\lunjiang\python.exe -m pytest tests/ -q           # 离线测试（治理/模型/改写/API 集成/评测口径等 89 用例，无外部依赖）
envs\lunjiang\python.exe -m ruff check .               # 静态检查（规则见 ruff.toml）
envs\lunjiang\python.exe scripts/load_test.py          # 知识库检索并发压测（需 uvicorn 已启动）
```

## 配置方法

### `.env`（本地环境变量，不入库）

> `.env` 缺失时配置层自动回退加载 `.env.example` 占位默认值（首次 clone 与 CI 可直接跑测试）；生产部署仍须复制 `.env.example` 为 `.env` 并覆盖真实密钥。

| 变量                                                          | 说明                                                                                |
| ----------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `SECRET_KEY`                                                | JWT 签名密钥，**生产环境必须修改**                                                             |
| `APP_HOST` / `APP_PORT` / `APP_DEBUG`                       | 应用监听地址、端口与调试开关                                                                    |
| `PG_HOST` / `PG_PORT` / `PG_USER` / `PG_PASSWORD` / `PG_DB` | PostgreSQL 连接信息（本项目端口为 **5433**）                                                  |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB`                    | Redis 连接信息（默认 6379/0）                                                             |
| `DEEPSEEK_API_KEY` / `ZHIPU_API_KEY` / `QWEN_API_KEY`       | 各云底座密钥（切换 provider 时填写；settings.yaml 无 openai provider，旧 `OPENAI_API_KEY` 为无效残留键） |
| `AGNES_BASE_URL` / `AGNES_API_KEY`                          | 云上备选对话底座 agnes-2.5-flash（OpenAI 兼容，切换 provider 时填写）                     |

### `configs/settings.yaml`（主配置）

- **对话 / 嵌入双底座**：默认 `llm.default_provider=ollama`（本地 qwen3:4b-ctx4096，离线可用）、`llm.embedding_provider=ollama`（本地 bge-m3）；`default_provider` 可切换 `deepseek` / `zhipu` / `qwen` / `agnes`（云上底座 Key 填 `.env`），两者可解耦。Ollama 的 `/v1` 兼容端点不认请求级 `options`，已用 Modelfile 给 `qwen3:4b` 建 `qwen3:4b-ctx4096` 镜像副本（blob 复用，几乎不占额外磁盘）固化 `num_ctx=4096`，防 16GB 内存机器 KV Cache OOM。切换操作与 embedding 维度变更的后果见 [学习指南第 6 课](docs/LEARNING_GUIDE.md#第-6-课-llm-接入层统一入口多底座切换)。

- **向量维度动态化**：pgvector 向量列维度由 `llm.providers.<底座>.embedding_dim` 动态决定（`infrastructure/config.get_embedding_dim()`）；嵌入底座返回维度不符时运行时抛错。已引入 Alembic 迁移骨架（`alembic/`），初始迁移待数据库环境就绪后生成，开发期沿用 `create_all` 兜底（见 [ROUND12](docs/OPTIMIZATION_ROUND12.md#五p0-2-alembic-迁移骨架暂停推进)）

- **RAG 参数**：`rag.rewrite_enabled`（Query 改写总开关）、`rag.rewrite_mode`（off/auto/on，默认 auto：短句简单查询跳过 LLM 仅规则关键词，口语化长尾才走 LLM 改写，见 [ROUND13](docs/OPTIMIZATION_ROUND13.md)）、`rag.sibling_window`（相邻窗口第三引擎半径，0=关闭）、`rag.max_upload_size_mb`（知识库单文件上限）、`rag.knowledge.upload_dir`（原始文件落盘目录，默认 `data/uploads/`，已 gitignore）、`rag.knowledge.min_text_chars`（低于该字数视为扫描件/空文档拒绝）

### `configs/tools.yaml`（工具治理参数）

14 个治理工具（论文 8 类 + 学术 6 类）各自的限流阈值（`rate_limit_rpm`）、熔断分组（`breaker`）与降级默认参数（`fallback_kwargs`），例如 `topic_analysis` 限流 10 rpm、`search_literature` 熔断分组 `rag_pipeline` 并降级 `top_k=5`。

### `configs/rbac.yaml`（角色策略）

YAML 驱动的 RBAC，`resource` 命名 `<域>:<动作>`，支持 `*` 与 `prefix:*` 通配：

- `student`：项目 CRUD、发起/介入 Agent 会话、全部论文工具（治理层另有限流/审计）

- `admin`：全量权限（含 Trace 回放）

- `anonymous`：仅注册与登录

### 知识库使用

`POST /api/projects/{id}/knowledge` 上传（PDF/DOCX/TXT/MD，可多文件）→ 自动解析分块向量化入库；`.../knowledge/search` 支持 `mode=project`（仅库内）与 `mode=hybrid`（公共语料+库内融合）。详细的调用示例见 [学习指南第 16 课](docs/LEARNING_GUIDE.md#第-16-课-项目知识库与复合任务规划第-45-轮扩展)。

## 目录结构

```
main.py              FastAPI 入口（启动命令 uvicorn main:app）
api/                 接口层（FastAPI 路由 + 共享依赖 + 响应模型）
  ├─ auth/           注册/登录/JWT（/me 当前用户）
  ├─ projects/       论文项目 CRUD（知识库已拆分至 knowledge/）
  ├─ knowledge/      项目级私有知识库（上传/列表/删除/库内检索，独立聚合根）
  ├─ agent/          /chat (SSE) /resume 人机介入（编排在 ConversationService）
  ├─ observability/  Trace 回放 + 运行指标（admin）
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
data/                corpus/（公共语料 txt） + uploads/（知识库原始文件落盘，已 gitignore）
evals/               评测 Harness + A/B + 七大场景回归 + 报告图表
scripts/             初始化 + 冒烟 + 压测脚本
frontend/            React 18 + Vite（SSE 对话 / Markdown / 时间线 / 项目知识库面板）
docs/                文档（学习指南 / 优化记录）
tests/               离线单元测试
alembic/             SQLAlchemy 迁移（异步 env.py 聚合全部模型，待生成初始迁移）
docker-compose.yml   PostgreSQL(pgvector) + Redis + app 后端服务编排（容器内走服务名；`--scale app=2` 起多实例）
Dockerfile           后端容器镜像（python:3.12-slim，非 root + /health 健康检查，见 [ROUND13](docs/OPTIMIZATION_ROUND13.md)）
```

依赖方向：`api → services → infrastructure → configs`，禁止反向。

## API 速览

| 分组       | 端点                                                                                                          | 鉴权                    |
| -------- | ----------------------------------------------------------------------------------------------------------- | --------------------- |
| Auth     | `POST /api/auth/register`、`POST /api/auth/login`、`GET /api/auth/me`                                         | 前两者免鉴权；`/me` 需 Bearer |
| Projects | `POST/GET /api/projects`、`GET/PATCH/DELETE /api/projects/{id}`                                              | Bearer                |
| 知识库      | `POST/GET/DELETE /api/projects/{id}/knowledge[/{doc_id}]`、`POST .../knowledge/search`                       | Bearer                |
| Agent    | `POST /api/agent/chat`（SSE）、`POST /api/agent/resume`                                                        | Bearer                |
| Trace    | `GET /api/observability/traces`、`GET /api/observability/traces/{trace_id}`、`GET /api/observability/metrics` | admin                 |

## 常见问题

- **后端启动报** **`ConnectionRefusedError: [WinError 1225]`**：应用启动时会立即连接 PostgreSQL 建表，该错误说明 **PostgreSQL（或 Redis）未启动**。按[快速开始第 0 节](#0-环境准备)的连通性自检确认监听，并依次启动依赖后重启。

- **`pg_ctl start`** **提示 another server might be running 并卡住**：多为异常退出残留 `postmaster.pid`（确认 5433 无监听、无 postgres 进程后）删除 `D:\Develop\DB\PostgreSQL16\data\postmaster.pid` 再启动。

- **Ollama 返回 500（KV Cache OOM）**：参考 [优化记录二](docs/OPTIMIZATION_ROUND2.md)（`num_ctx=4096` 已由 Modelfile 镜像 `qwen3:4b-ctx4096` 固化）；默认对话即走本地 Ollama，确认使用了该镜像而非裸 `qwen3:4b`。

- **端口冲突**：若本机 5433/6379 被占用，先释放端口，或调整 `.env` 与 `postgresql.conf` 保持一致。

- **`check_env.py`** **报错**：该脚本按 Ollama `/api/generate` 格式探测 LLM 底座，默认 `default_provider=ollama` 可直测；若临时切换到 OpenAI 兼容云端（如 agnes）会 404 属预期，以 `scripts/` 其余冒烟脚本与 `netstat` 端口检查为准。

- **中文乱码**：全部文件保持 UTF-8（已配 `.editorconfig` + IDE settings）。

- **知识库上传返回 failed（扫描件）**：扫描版 PDF 无可提取文本，本期不支持 OCR，接口返回 `status=failed` + 错误说明；请上传含文本层的 PDF 或 DOCX/TXT/MD。

