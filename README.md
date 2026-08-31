# 论匠 · LunJiang

基于 **LangGraph 主从多智能体架构** 的论文全流程智能助手：选题分析 → 文献检索 → 论文写作 → 格式校验 → 查重降重 → 答辩准备。配套 **四层记忆**、**三阶段 RAG**、**工具治理** 与 **全链路可观测**。

> 技术栈：Python 3.11 + FastAPI + LangGraph + PostgreSQL(pgvector) + Redis + Ollama + React 18 + Vite

## 文档导航

| 文档                                      | 用途                   |
| --------------------------------------- | -------------------- |
| [📖 学习指南](docs/LEARNING_GUIDE.md)       | 从零理解并重建本项目（推荐先读）     |
| [📐 架构总览](#目录结构)                        | 分层结构与模块职责            |
| [🛠 优化记录一](docs/OPTIMIZATION_ROUND1.md) | 第一轮优化（性能/安全/体验）      |
| [🛠 优化记录二](docs/OPTIMIZATION_ROUND2.md) | 第二轮优化（OOM 修复/结构重构方案） |
| [💡 常见问题](#常见问题)                        | 排障手册                 |

## 快速开始

### 0. 环境准备

依赖：Python 3.11（conda）、Node 18+、PostgreSQL 15+（pgvector）、Redis 6+、Ollama。

```powershell
# Ollama：新开窗口常驻启动，拉取模型，并创建 16GB 内存适配镜像
ollama serve
ollama pull qwen3:4b
ollama pull bge-m3
ollama create qwen3:4b-ctx4096 -f configs\ollama\Modelfile.qwen3-ctx4096   # 固定 num_ctx=4096，防 KV Cache OOM
```

> 💡 **16GB 内存机器**：Ollama 的 `/v1` 兼容端点不认请求级 `options`，因此用 Modelfile 给 `qwen3:4b` 建了 `qwen3:4b-ctx4096` 镜像副本（blob 复用，几乎不占额外磁盘）。`configs/settings.yaml` 的 `chat_model` 已指向该标签；内存更紧张可换 `qwen3.5:2b`。

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
envs\lunjiang\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
cd frontend && npm install && npm run dev              # 前端 5173，/api 代理到 8000
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
```

## 核心特性

| 模块      | 说明                                       | 关键实现                        |
| ------- | ---------------------------------------- | --------------------------- |
| 多智能体编排  | 1 主控 Supervisor 调度 6 类专项 Agent，最大 3 跳防回环 | `services/agent/`               |
| 意图预分类   | 规则 → 向量原型 → LLM 兜底三级，56ms / 100% 准确      | `services/classifier/intent.py` |
| 三阶段 RAG | Query 改写 → 稠密+稀疏 RRF 融合 → 交叉精排，含防漂移      | `services/rag/`                      |
| 工具治理    | RBAC → 限流 → 熔断 → 重试 → 分布式锁 → 审计 → Skill  | `services/governance/`               |
| 四层记忆    | 短期(Redis)/结构化/长期(pgvector)/偏好 + 压缩       | `services/memory/`                   |
| SSE 流式  | EventHub 事件总线 + token 微缓冲                | `services/streaming/hub.py`     |
| 人机介入    | LangGraph interrupt 挂起 → /resume 续跑      | `api/agent/router.py`       |
| 全链路可观测  | Trace/Log/Memory/Action 统一 Span，树形回放     | `services/observability/`            |

## 目录结构

```
main.py              FastAPI 入口（启动命令 uvicorn main:app）
api/                 接口层（FastAPI 路由 + 中间件）
  ├─ auth/           注册/登录/JWT
  ├─ projects/       论文项目 CRUD（原 gateway，命名纠偏）
  ├─ agent/          /chat (SSE) /resume 人机介入
  ├─ observability/  Trace 回放（admin）
  └─ middleware/     审计中间件（fire-and-forget）
services/            业务服务层（不得 import api/，可独立测试）
  ├─ agent/          LangGraph 主从图 + specialists/（6 个专项 Agent 独立文件）
  ├─ rag/            RAG 流水线（改写/召回/精排/语料入库）
  ├─ memory/         四层记忆 + 压缩
  ├─ governance/     工具治理（限流/熔断/重试/锁/RBAC/Skill）
  ├─ classifier/     三级意图分类
  ├─ streaming/      事件总线（SSE 微缓冲）
  ├─ checkpoint/     三级降级检查点
  ├─ llm/            LLM 统一接入（多 provider）
  └─ observability/  Trace Span
infrastructure/      基础设施层（地基，谁都得经过它）
  ├─ config.py       settings.yaml + .env + 单例
  ├─ db.py           SQLAlchemy 异步引擎
  ├─ redis_client.py asyncio Redis
  ├─ audit.py        审计写库（参数截断 + 指纹化）
  ├─ rbac/           角色策略
  └─ models/         ORM（users/projects/memory/trace/audit/skill）
configs/             settings.yaml / rbac.yaml / tools.yaml / ollama/Modelfile
evals/               评测 Harness + A/B 实验
scripts/             初始化 + 冒烟脚本（_archive/ 临时脚本）
frontend/            React 18 + Vite（SSE 对话 / Markdown / 时间线）
docs/                文档（学习指南 / 优化记录）
```

依赖方向：`api → services → infrastructure → configs`，禁止反向。

## 配置要点

- **`.env`**：`SECRET_KEY`（生产必改）、`APP_*`、`PG_*`、`REDIS_*`、云厂商 `*_API_KEY`（切换 provider 时填）

- **`configs/settings.yaml`**：`llm.default_provider` 一键切换 ollama/deepseek/zhipu/qwen；`rag.rewrite_enabled` 可按语料规模开关

## API 速览

| 分组       | 端点                                                           | 鉴权     |
| -------- | ------------------------------------------------------------ | ------ |
| Auth     | `POST /api/auth/register`、`POST /api/auth/login`             | 否      |
| Projects | `GET/POST /api/projects`、`GET/PUT/DELETE /api/projects/{id}` | Bearer |
| Agent    | `POST /api/agent/chat`（SSE）、`POST /api/agent/resume`         | Bearer |
| Trace    | `GET /observability/traces[/{id}]`                           | admin  |

## 常见问题

- **Ollama 返回 500**：参考 [FAQ Q1](docs/FAQ.md)（KV Cache OOM 已由 num\_ctx=4096 解决）

- **端口冲突**：项目 PG 固定 5433，独立于系统 5432

- **中文乱码**：全部文件保持 UTF-8（已配 `.editorconfig` + IDE settings）

***

<p align="center">详细教学与实现解析请阅读 <a href="docs/LEARNING_GUIDE.md">docs/LEARNING_GUIDE.md</a></p>
