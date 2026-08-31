# 论匠 LunJiang · 多智能体论文全流程辅助平台

基于 **LangGraph 主从多智能体架构** 的论文全流程智能助手：选题分析 → 文献检索 → 论文写作 → 格式校验 → 查重降重 → 答辩准备，配套 **四层记忆体系**、**三阶段 RAG**、**工具调用治理**、**全链路可观测** 与 **评测 Harness**。

> 技术栈：Python 3.11 + FastAPI + LangGraph + PostgreSQL(pgvector) + Redis + Ollama(qwen3/bge-m3) + React 18 + Vite

## 核心特性

| 模块 | 说明 | 关键实现 |
|---|---|---|
| 多智能体编排 | 1 个主控 Agent 调度 6 类专项 Agent，条件路由 + 最大跳数防回环 | `core/graph/`（LangGraph StateGraph，supervisor 中心路由） |
| 意图预分类 | 三层轻量分类：规则(0 token) → 向量原型 → LLM 兜底，实测 100% 准确率、56ms 均耗 | `core/classifier/intent.py` |
| SSE 流式输出 | asyncio.Queue 事件总线 + token 微缓冲，解决 token 流与节点事件时序错乱 | `core/streaming/hub.py` |
| 人机介入 | LangGraph interrupt 挂起 → 用户反馈 → Command(resume) 续跑 | `app/agent/router.py` `/chat` `/resume` |
| 四层记忆 | 短期对话(Redis) / 项目结构化 / 长期向量(pgvector) / 用户偏好 | `memory/` |
| 四级上下文压缩 | 分级留存 → 冗余去重 → 窗口截断 → LLM 摘要归档，实测压缩率 0.21（目标 ≤0.3） | `memory/compressor.py` |
| 三阶段 RAG | Query 改写 → 稠密(pgvector)+稀疏(BM25/jieba) 多路召回 RRF 融合 → 交叉编码器精排；含改写防漂移三件套（拒答回退 / 原查询稠密保底 / 双查询精排取 max） | `rag/` |
| 工具治理 | YAML RBAC → Redis 滑动窗口限流(ZSET+Lua) → 三态熔断 → 三级容错(重试/参数降级/人机兜底) → 分布式锁 → 审计 | `governance/` |
| Skill 沉淀 | 行为观测：同参数模式连续 3 次成功自动沉淀可复用 Skill，三维匹配召回 | `governance/skill.py` |
| 全链路可观测 | Trace/Log/Memory/Action 统一 Span 落库，时间序列 + 树形行为回放 | `observability/trace.py` `app/observability/router.py` |
| 评测 Harness | 意图分类准确率 / RAG Recall@5 / 压缩率，A/B 实验框架 | `evals/` |

## 快速开始

### 0. 环境准备

- Python 3.11（推荐用 conda，项目自带环境目录 `envs/`）
- Node 18+
- Ollama：`ollama pull qwen3:4b && ollama pull bge-m3`
- 交叉编码器首次运行自动从 HF 下载 `BAAI/bge-reranker-base`（可设 `HF_ENDPOINT=https://hf-mirror.com` 加速；检测到本地缓存后自动强制离线加载，不再探测网络）

### 1. 初始化环境

```powershell
# conda 环境创建在项目内 envs/ 目录，依赖隔离
conda create -p envs/lunjiang python=3.11 -y
conda run -p envs/lunjiang pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 配置
copy .env.example .env   # 修改数据库/Redis 连接信息
```

项目内 PG/Redis 实例（可选，用于完全隔离的开发环境）：`envs/pg` + `envs/pgdata`（端口 5433）。

### 2. 初始化数据

```powershell
# 连通性检查（Ollama/Redis/PG/pgvector 自动建库建扩展）
envs\lunjiang\python.exe scripts/check_env.py

# 语料入库：data/corpus/*.txt → 分块 → bge-m3 向量化 → pgvector + BM25 索引
envs\lunjiang\python.exe scripts/ingest_corpus.py
```

### 3. 启动

```powershell
# 后端（默认 8000）
envs\lunjiang\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 前端（5173，/api 代理到 8000）
cd frontend && npm install && npm run dev
```

浏览器打开 http://localhost:5173 注册/登录 → 新建项目 → 发起对话。

### 4. 冒烟与评测

```powershell
envs\lunjiang\python.exe scripts/smoke_memory.py       # 四层记忆 + 窗口压缩
envs\lunjiang\python.exe scripts/smoke_rag.py          # 三阶段检索
envs\lunjiang\python.exe scripts/smoke_governance.py   # 治理栈 9 项
envs\lunjiang\python.exe scripts/smoke_trace.py        # Trace + 行为回放
envs\lunjiang\python.exe scripts/smoke_api.py --topic  # 端到端（需 uvicorn 已启动）

envs\lunjiang\python.exe evals/harness.py              # 三项指标评测（intent/rag/compression）
envs\lunjiang\python.exe evals/ab.py                   # A/B 实验（简单集+长尾困难集+图表报告）
envs\lunjiang\python.exe evals/ab.py --report-only     # 仅从 ab_report.json 重生成图表与报告
```

## 架构总览

```
frontend/  React 18 + Vite（SSE 流式对话 / Markdown 渲染 / Agent 时间线 / Trace 回放）
app/       FastAPI 网关
  ├─ auth/        注册/登录/JWT/RBAC/登录限流（Redis 滑动窗口 5 次/分钟）
  ├─ gateway/     论文项目 CRUD
  ├─ agent/       /api/agent/chat|resume（SSE + interrupt）
  ├─ observability/  /observability/traces[/{id}]（回放，admin）
  ├─ middleware/  审计中间件（fire-and-forget 异步落库）
  └─ models/      ORM（users/projects/memory_items/trace_spans/skills/audit_logs）
core/
  ├─ graph/       LangGraph 主从图（supervisor + 6 专项 Agent + checkpointer）
  ├─ classifier/  三层意图预分类
  ├─ streaming/   EventHub 事件总线（token 微缓冲）
  ├─ checkpoint/  三级降级 Checkpointer（PG → Redis → 内存）
  └─ llm/         OpenAI 兼容统一接入（可一键换底座，客户端连接池复用）
memory/    四层记忆 + 四级压缩
rag/       Query 改写 / 混合召回(RRF) / 防漂移融合 / 交叉编码器精排 / 语料入库
governance/ 工具注册中心 + RBAC/限流/熔断/容错/分布式锁/Skill
observability/  全链路 Span 落库与回放查询
evals/     评测数据集（简单集+长尾困难集）+ Harness + A/B
docs/      改进记录（OPTIMIZATION_ROUND1.md）
```

## 关键设计决策

1. **主从图而非链式**：supervisor 集中意图分类与路由，专项 Agent 结果回流 supervisor 判定续链/收尾，`max_hops=3` 防回环；checkpointer 持久化图状态支撑 interrupt/断点恢复。
2. **事件总线统一时序**：所有 Agent 节点内通过 ContextVar 绑定的 EventHub emit 事件，token 经 4 条/32 字符微缓冲合并后入队，SSE 消费端保证按序渲染。
3. **治理前置**：工具调用必经 注册→RBAC→限流→熔断→容错→锁→审计 流水线，业务工具零感知；`configs/tools.yaml` 声明限流/锁/降级参数，`configs/rbac.yaml` 声明角色权限。
4. **记忆按需装配**：会话启动时仅装配 L1 近 8 轮 + L2 项目简报 + L3 向量召回 Top3 + L4 偏好 Top5，超阈值异步触发四级压缩，摘要归档长期记忆。

## 评测结果

| 指标 | 实测 | 目标 |
|---|---|---|
| 意图分类准确率 | 100%（22 条） | — |
| 意图分类均耗 | 56ms（rule 命中 73%，LLM 兜底 0 次） | — |
| RAG Recall@5 | 100%（简单集 8 条） | ≥ 90% |
| A/B：Query 改写 | 不提升召回（100%→100%）但改善排序（TOP1 5/8→7/8）；定位语义漂移/域外拒答两类失效模式，三重防漂移修复后困难集 MRR 0.917（基线 0.744） | — |
| 上下文压缩率 | 0.21 | ≤ 0.30 |
| 治理冒烟 | 9/9 通过 | — |

> A/B 报告：`evals/ab_report.json`；全量指标：`evals/results_latest.json`

## 声明

本项目为学习性质的全栈复刻实践，语料为自撰模拟文献，仅供演示。
