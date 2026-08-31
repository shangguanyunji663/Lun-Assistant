# 论匠 · 学习指南（从零理解并重建本项目）

> 这份文档的目标：**让你从一张白纸开始，按"重新独立构建"的思维把整个项目推演出来**。
> 读懂它 = 理解了这个项目的全部设计决策；照着做 = 能在自己机器上逐步复现一个最小可用版本。
>
> 建议阅读方式：顺序阅读，每一课都留了「读代码」和「动手做」两个动作。全部通过只花一个晚上。

***

## 目录

- [第 0 课 先想清楚：一个论文助手要解决什么问题](#第-0-课-先想清楚一个论文助手要解决什么问题)

- [第 1 课 设计一张总数据流图](#第-1-课-设计一张总数据流图)

- [第 2 课 技术选型：每一块为什么是它](#第-2-课-技术选型每一块为什么是它)

- [第 3 课 从最小骨架起步：FastAPI + 配置层](#第-3-课-从最小骨架起步fastapi--配置层)

- [第 4 课 存储底座：PostgreSQL(pgvector) + Redis](#第-4-课-存储底座postgresqlpgvector--redis)

- [第 5 课 认证：JWT + bcrypt + 登录限流](#第-5-课-认证jwt--bcrypt--登录限流)

- [第 6 课 LLM 接入层：一个接口换四个底座](#第-6-课-llm-接入层一个接口换四个底座)

- [第 7 课 记忆体系：四层记忆 + 自动压缩](#第-7-课-记忆体系四层记忆--自动压缩)

- [第 8 课 三阶段 RAG：改写 → 召回 → 精排](#第-8-课-三阶段-rag改写--召回--精排)

- [第 9 课 意图预分类：规则 → 向量 → LLM 三级兜底](#第-9-课-意图预分类规则--向量--llm-三级兜底)

- [第 10 课 多智能体编排：LangGraph 主从图](#第-10-课-多智能体编排langgraph-主从图)

- [第 11 课 工具治理：限流 / 熔断 / 重试 / 锁 / RBAC / Skill](#第-11-课-工具治理限流--熔断--重试--锁--rbac--skill)

- [第 12 课 流式输出与全链路可观测](#第-12-课-流式输出与全链路可观测)

- [第 13 课 前端与端到端打通](#第-13-课-前端与端到端打通)

- [第 14 课 用评测体系守住质量](#第-14-课-用评测体系守住质量)

- [第 15 课 独立重建的最小路线图](#第-15-课-独立重建的最小路线图)

- [附录 关键类与调用链速查](#附录-关键类与调用链速查)

***

## 第 0 课 先想清楚：一个论文助手要解决什么问题

任何项目都起源于一个**具体而真实的痛点**。不要一上来就写代码，先回答三个问题：

### 0.1 用户是谁，要什么

| 问题          | 本项目的回答                                                                      |
| ----------- | --------------------------------------------------------------------------- |
| 服务谁？        | 需要写毕业/课程论文的本科生、研究生                                                          |
| 论文流程包含哪些环节？ | 选题分析 → 文献检索 → 论文写作 → 格式校验 → 查重降重 → 答辩准备                                     |
| 用户现在怎么做的？   | 搜索引擎 + 多个 AI 工具 + 手动调整格式，来回切换、上下文断裂                                         |
| 理想产品是什么？    | **一个会"干活"的助手**：你告诉它论文阶段和需求，它在内部调用检索、写作、格式、查重等"工具"，把结果合并成一份连贯输出，并且能记住你的项目上下文 |

答案是产品形态：**多智能体对话式助手**，而不是又一个"套壳聊天框"。

### 0.2 把需求翻译成系统能力

从上面的痛点反推，系统至少要具备 6 大能力，缺一不可：

```
① 理解我要什么     → 意图分类（选题？写作？查重？还是闲聊）
② 记住我们聊过啥   → 记忆（本次对话 + 这个项目的背景 + 用户的长期偏好）
③ 查得到文献资料   → 检索（针对用户项目语料的 RAG）
④ 真的会干活       → 工具（生成大纲 / 写章节 / 查格式 / 模拟查重）
⑤ 干活要可靠       → 治理（限流防滥用 / 出错重试 / 雪崩熔断 / 权限管控）
⑥ 干完了我看得见   → 可观测（这条请求里 Agent 每一步做了什么）

再加上：
⑦ 听我指挥         → 人机介入（关键步骤停下来问你，而不是自作主张）
⑧ 输出体验好       → 流式输出（打字机效果，而非死等 10 秒）
```

**这就是本项目目录的由来**——每一个顶层包都对应上述一个能力：

| 能力      | 顶层包                         |
| ------- | --------------------------- |
| ① 意图分类  | `services/classifier/`          |
| ② 记忆    | `services/memory/`                   |
| ③ 检索    | `services/rag/`                      |
| ④ 工具    | `services/governance/tools_impl.py`  |
| ⑤ 治理    | `services/governance/`               |
| ⑥ 可观测   | `services/observability/`            |
| ⑦ 人机介入  | `services/agent/`（interrupt 机制） |
| ⑧ 流式    | `services/streaming/`           |
| 编排所有智能体 | `services/agent/`               |

> 💡 学习心得：**好的项目结构是先有需求地图，再有代码目录**。你不需要背目录，只要记住这张能力表。

### 0.3 验收标准要可量化

写作项目的通病是"感觉能用"，无法向面试官/老板证明。本项目给每项能力定了量化指标（`evals/` 就是干这个的）：

| 指标            | 目标     | 定义                                 |
| ------------- | ------ | ---------------------------------- |
| 意图分类准确率       | ≥ 98%  | 三层分类器在 200 条测试样本上的正确率              |
| RAG Recall\@5 | ≥ 0.90 | 检索返回的 Top5 文档里包含正确答案的比例            |
| 上下文压缩比        | ≤ 0.30 | 压缩后 token 数 / 压缩前 token 数（省钱、省上下文） |

***

## 第 1 课 设计一张总数据流图

动手写代码前，画一张**一次对话请求**的完整旅程。这张图是全文最核心的心智模型：

```
用户输入 "帮我找几篇 RAG 可解释性的论文"
   │
   ▼
① FastAPI /api/agent/chat  （api/agent/router.py）
   │ 鉴权 → 建立 EventHub（stdout 事件总线）
   ▼
② AgentEngine.run()        （services/agent/engine.py）
   │
   ▼
③ 组装"记忆包"（services/memory/）：短期对话 + 项目信息 + 长期向量召回 + 用户偏好
   │
   ▼
④ Supervisor 意图分类     （services/agent/supervisor.py → services/classifier/intent.py）
   │  判定：literature（文献检索类）
   ▼
⑤ Specialist 文献 Agent    （services/agent/agents/specialists.py）
   │  需要调用"文献检索"工具
   ▼
⑥ 工具治理栈 ToolRegistry.call()  （services/governance/tool_registry.py）
   │  限流 → 熔断 → 重试 → 分布式锁 → 执行 search_literature()
   │                                        │
   │                                        └─▶ 三阶段 RAG（services/rag/pipeline.py）
   │                                             改写 → 召回 → 精排  → 返回片段
   ▼
⑦ LLM 把检索结果组织成最终回答
   │
   ▼
⑧ EventHub → SSE 流式推给前端（token 级打字机 + 节点事件）
   │
   ▼
⑨ 全程 Trace Span 落库（services/observability/trace.py）后台异步写审计日志
```

右边竖着读就是依赖方向：`api → graph → (services/memory/services/rag/governance) → llm`。

> 💡 学习心得：**把一次请求走通，胜过读一百个函数**。后面每一课都是在给这条流水线"加一站"。

***

## 第 2 课 技术选型：每一块为什么是它

| 选型                            | 为什么                                                                     | 替代方案与取舍                                        |
| ----------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------- |
| **FastAPI + uvicorn**         | 原生 async/await，配 SSE 流式输出最顺；自动 OpenAPI 文档方便联调                           | Flask 同步、Django 太重                             |
| **LangGraph**                 | 需要「主从多智能体 + 有条件分支 + 人机中断恢复」这三件事，LangGraph 的 StateGraph + interrupt 是现成的 | 手写状态机 = 重新造轮子且难维护                              |
| **PostgreSQL + pgvector**     | 论文检索需要**稠密向量相似度**，pgvector 让"向量检索 + 关系数据 + 事务"在一个库里完成                   | 单独上向量库（Milvus）引入新运维负担                          |
| **Redis**                     | 限流计数器（ZSET 滑动窗口）、短期对话窗口、分布式锁、熔断状态，都要**毫秒级且本身带 TTL**                     | 全用 PG 慢且浪费                                     |
| **Ollama（qwen3:4b + bge-m3）** | 本地推理：隐私可控、零 API 费用、演示不断网                                                | 云端 DeepSeek/智谱/通义：更聪明但花钱（本项目已做多 provider 一键切换） |
| **BM25（rank\_bm25 + jieba）**  | 向量检索"语义像但缺关键词"，BM25"抓关键词好用"，两者 RRF 融合效果显著优于单路                           | 只做向量 = 专业术语召回差（如 "KF 交叉验证"）                    |
| **React 18 + Vite**           | 交互密集（SSE 实时流 + Markdown + 时间线），前端生态最成熟                                  | 略重，但 demo 界面价值高                                |
| **SQLAlchemy 2.0**            | `Mapped/mapped_column` 类型化 ORM，配合 asyncpg 跑异步                           | 手写 SQL 维护成本高                                   |

> 💡 学习心得：选型理由就一句话——**每一项都对应一个明确痛点，没有一样是"为了炫技"**。面试被问"为什么用它"，就按痛点到方案回答。

***

## 第 3 课 从最小骨架起步：FastAPI + 配置层

### 3.1 目标

先让 `uvicorn` 能起一个返回 `{"status":"ok"}` 的服务——但配置不能硬编码。

### 3.2 配置层的设计（重要，全项目都从这里取配置）

看 [infrastructure/config.py](../infrastructure/config.py)，核心只做三件事：

```python
def _load_env_file(path):   # ① 读 .env 的 KEY=VALUE，不覆盖已有环境变量
def _interpolate(node):     # ② 递归替换字符串中的 ${VAR} 占位符，缺失即报错
@lru_cache
def get_settings():         # ③ 全局单例，读 configs/settings.yaml + 插值
```

设计细节（面试高频）：

- **`${VAR}`** **缺失即抛异常**，而不是留空——避免"配置错了但静默运行"的隐形故障；

- **`lru_cache`** **单例**——全项目各处调用 `get_settings()` 零开销，拿到的同一份配置；

- **配置分三层**：`.env`（密钥/端口这类按机器不同的）→ `configs/settings.yaml`（默认行为）→ 环境变量覆盖。

配好后全项目禁止在业务代码里硬编码 IP/端口/模型名，一律 `get_value("llm", "providers", ...)` 或 `get_settings()["..."]`。

### 3.3 动手

```powershell
# 复制环境变量模板
copy .env.example .env
# 起服务
envs\lunjiang\python.exe -m uvicorn app.main:app --port 8000
# 浏览器/curl: http://127.0.0.1:8000/health  → {"status":"ok","app":"lunjiang"}
```

**读代码**：[main.py](../main.py)（lifespan 生命周期：连接池预热/关闭）、[infrastructure/config.py](../infrastructure/config.py)。

***

## 第 4 课 存储底座：PostgreSQL(pgvector) + Redis

### 4.1 为什么是两个存储

- **PostgreSQL**：关系数据 + 向量，存**用户/项目/记忆/审计/轨迹**（有事务、长生命周期）；

- **Redis**：内存缓存，存**短期对话窗口/限流计数/熔断状态/分布式锁**（要极快、自带过期）。

### 4.2 ORM 建模（怎么建表）

看 [infrastructure/models/base.py](../infrastructure/models/base.py) 的 `IdMixin / TimestampMixin`——所有表共享的公共列（id 自增、created\_at/updated\_at），避免每张表重复写。

关键模型（[infrastructure/models/](../infrastructure/models/)）：

| 模型           | 表用途                                              |
| ------------ | ------------------------------------------------ |
| `user.py`    | 用户（密码哈希、角色）                                      |
| `project.py` | 论文项目（题目/领域/状态）                                   |
| `memory.py`  | **记忆条目**，含 `Vector(1024)` 列 —— 就是 pgvector 的用武之地 |
| `trace.py`   | 全链路追踪 Span                                       |
| `audit.py`   | 审计日志（参数截断 + 指纹化）                                 |
| `skill.py`   | 自动沉淀的可复用技能                                       |

### 4.3 建库建扩展的自动化

`scripts/check_env.py` 里有一段关键逻辑：连到 `postgres` 系统库 → 若目标库不存在则 `CREATE DATABASE` → 再 `CREATE EXTENSION IF NOT EXISTS vector`。**这就是"开箱即用"的关键**：用户不用手动建库建扩展。

### 4.4 动手

```powershell
envs\lunjiang\python.exe scripts/check_env.py   # 应看到 PostgreSQL/pgvector 全 PASS
```

**读代码**：[infrastructure/db.py](../infrastructure/db.py)（engine 工厂 + 两种 session 获取方式）、[infrastructure/models/memory.py](../infrastructure/models/memory.py)。

***

## 第 5 课 认证：JWT + bcrypt + 登录限流

### 5.1 三个安全决策（面试点）

| 决策                          | 为什么                                  | <br /> |
| --------------------------- | ------------------------------------ | :----- |
| 密码用 **bcrypt** 哈希           | 自带盐 + 慢哈希，防彩虹表/爆破                    | <br /> |
| 登录发 **JWT**（`access_token`） | 无状态、多实例部署友好，`{sub, role, exp}` 里带上角色 | <br /> |
| 登录接口 **限流 5 次/分钟（用户名+IP）**  | 防爆破；用治理层的滑动窗口限流器（见第 11 课）            | <br /> |

### 5.2 认证依赖注入

看 [api/auth/security.py](../api/auth/security.py)：`get_current_user()` 是一个 FastAPI 依赖——从请求头 `Authorization: Bearer <token>` 解码 → 查用户 → 返回 `User`。任何需要登录的接口只写 `user: User = Depends(get_current_user)` 即可，**不需要每个接口自己解析 token**。

角色控制同理：`require_role("admin")` 是依赖工厂，`/services/observability/traces` 就只对 admin 开放（[api/services/observability/router.py](../api/services/observability/router.py)）。

### 5.3 动手

```powershell
$body = @{username="demo"; password="Demo123!"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/register" -Method Post -Body $body -ContentType "application/json"

$body = @{username="demo"; password="Demo123!"} | ConvertTo-Json
$r = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login" -Method Post -Body $body -ContentType "application/json"
# $r.access_token 存起来，后面所有接口带上
```

**读代码**：[api/auth/security.py](../api/auth/security.py)、[api/auth/router.py](../api/auth/router.py)。

***

## 第 6 课 LLM 接入层：一个接口换四个底座

### 6.1 现成的仓库问题

项目要支持 Ollama / DeepSeek / 智谱 / 通义 四种模型，但它们都兼容 **OpenAI 协议**。所以正确做法是：**统一封装一层，内部切换 base\_url**。

### 6.2 LLMProvider 类（[services/llm/provider.py](../services/llm/provider.py)）

对外只暴露四个方法，全项目都只用它：

```python
class LLMProvider:
    async def chat(messages, *, temperature, max_tokens, json_mode) -> str
    async def chat_stream(messages) -> AsyncIterator[str]
    async def embed(texts) -> list[list[float]]        # 向量化
    async def chat_tools(messages, tools, executor) -> dict  # 工具调用循环
```

几个设计点：

- **客户端缓存**：按 `(provider, base_url, api_key)` 复用 `AsyncOpenAI` 实例（第一次审查优化加的），避免每次工具调用都重建 TCP 连接；

- **`_extra()`** **provider 特殊参数**：本地 Ollama 传 `think: False`（关掉 qwen3 的思考链，省时）和 `options.num_ctx=4096`（限制上下文防内存爆炸，第 2 轮优化加的）；

- **`json_mode`** **容错解析**：`_extract_json()` 剥掉 markdown 代码块再取第一对 `{ }`，因为 LLM 的输出格式不稳。

### 6.3 切换底座

改 [configs/settings.yaml](../configs/settings.yaml) 一行：

```yaml
llm:
  default_provider: ollama   # ← 改成 deepseek / zhipu / qwen 即在云端跑
```

代码零改动。

**读代码**：[services/llm/provider.py](../services/llm/provider.py) 全文（不算长，建议逐行读）。

***

## 第 7 课 记忆体系：四层记忆 + 自动压缩

### 7.1 为什么是"四层"而不是"一个聊天记录"

单轮对话是 **"短期对话"**（Redis），但如果用户第二天回来，Redis 过期了怎么办？如果用户换了个项目、或者问的是自己长期偏好呢？所以按**生命周期从短到长**分四层：

```
短期对话 services/memory/short_term.py    本轮/近 N 轮（Redis List + TTL 30 天）
项目结构化 services/memory/structured.py   该论文项目的题目/大纲/结论（PG）
长期向量   services/memory/long_term.py    历史沉淀的知识点（PG Vector 相似度召回）
用户偏好   services/memory/preference.py   用户长期习惯（"我偏好综述式回答"）
```

### 7.2 短期记忆怎么实现（[services/memory/short\_term.py](../services/services/memory/short_term.py)）

Redis 里一个 key 存一个会话的多条消息（`lunjiang:chat:{project}:{session}`），方法签名一览：

```python
async def append(project_id, session_id, role, content)
async def history(project_id, session_id, last_n=None) -> list[dict]
async def total_chars(project_id, session_id) -> int
async def evict_compressed(project_id, session_id, keep_last) -> list[dict]
```

### 7.3 上下文压缩（[services/memory/compressor.py](../services/services/memory/compressor.py)）

问题：聊久了上下文太大，塞不进 LLM 窗口、费 token。方案是**四级压缩流水线**：

```
① 分级留存（_is_high_value 保留关键信息）
     ↓
② 冗余去重（_dedup 去掉重复轮次）
     ↓
③ 窗口截断（只留最近 N 轮）
     ↓
④ LLM 摘要归档（把早期内容压成一段摘要，后面的对话继续用）
```

入口 `compress_window_if_needed()` 按 token 阈值自动触发，实测压缩比 0.21（目标 ≤0.3）。

### 7.4 动手

```powershell
envs\lunjiang\python.exe scripts/smoke_memory.py   # 四层 + 压缩全部自检
```

**读代码**：`services/memory/` 下每个文件都很短，全部读完约 30 分钟。先读 `short_term.py` + `compressor.py`。

***

## 第 8 课 三阶段 RAG：改写 → 召回 → 精排

### 8.1 为什么是三阶段（而非直接搜）

直接拿用户原话去搜有三大痛点，每一阶段解一个：

| 阶段         | 痛点                             | 解决                                              |
| ---------- | ------------------------------ | ----------------------------------------------- |
| ① Query 改写 | 用户话太口语（"那篇讲可解释性的"），直接搜匹配差      | 先让 LLM 改写成检索友好的查询（含防漂移三件套）                      |
| ② 混合召回     | 单路向量漏关键词，单路 BM25 漏同义改写         | 稠密(pgvector) + 稀疏(BM25/jieba) 双路召回，**RRF 分数融合** |
| ③ 交叉精排     | 召回 20 条里有 15 条噪音，直接进 LLM 浪费上下文 | bge-reranker-base 交叉编码器逐条打分，只留 Top5             |

### 8.2 各文件职责

```
services/rag/ingest/corpus_loader.py   语料 *.txt → 分块(512字符, 64重叠) → bge-m3 向量 → 入 pgvector + 重建 BM25
services/rag/retriever.py              HybridRetriever：dense_search / sparse_search / rrf_fuse
services/rag/reranker.py               Reranker：bge-reranker-base（CPU 多线程 + 本地缓存检测）
services/rag/query_rewrite.py          rewrite_query()：LLM 改写
services/rag/pipeline.py               RagPipeline.search()：把上面串成流水线
```

### 8.3 防漂移三件套（第 1 轮 A/B 实验的重要产出）

LLM 改写并不总是变好，两种典型翻车：

- **语义漂移**：改写后意思变了（召回错的东西）；

- **越域拒答**：改写模型说"这不归我管"返回空。

修复（[services/rag/pipeline.py](../services/services/rag/pipeline.py)）：

```
if 改写结果被判定为拒答(越域拒绝) → 回退用原查询
if 改写后召回结果太差 → 与原查询的稠密检索结果合并兜底
精排阶段 → 改写查询与原查询两份结果各订一遍，取打分更高的
```

A/B 数据支撑：Recall\@5 100% 恢复，MRR 0.917（比基准 +0.17）。**这就是"用评测说话"的范例**（见第 14 课）。

### 8.4 动手

```powershell
envs\lunjiang\python.exe scripts/ingest_corpus.py     # 先把语料入库
envs\lunjiang\python.exe scripts/smoke_rag.py         # 三阶段检索自检
```

**读代码**：[services/rag/retriever.py](../services/services/rag/retriever.py)（重点 `rrf_fuse`，理解 RRF 公式）、[services/rag/pipeline.py](../services/services/rag/pipeline.py)。

***

## 第 9 课 意图预分类：规则 → 向量 → LLM 三级兜底

### 9.1 为什么需要意图分类

Supervisor 要决定把请求路由给哪个专项 Agent（文献？写作？查重？……）。如果每次都用 LLM 判断，慢且费钱。**让简单请求零成本命中，复杂请求才花 LLM**。

### 9.2 三级流水线（[services/classifier/intent.py](../services/classifier/intent.py)）

```
第一级  规则层    正则匹配关键词（"参考文献/综述"→literature），0 token、几乎 0ms，命中即返回
     ↓ 未命中
第二级  向量层    把待分类文本和各类别的原型文本都 embedding，算 cosine 相似度，取最高的（>阈值才信）
     ↓ 未命中/置信不足
第三级  LLM 兜底  让 LLM 直接输出 JSON 类别（实时准确率兜底）
```

实测：56ms 平均耗时、100% 准确率（`evals/datasets/intent.jsonl` 上评测）。

### 9.3 动手

```powershell
envs\lunjiang\python.exe evals/harness.py     # 会跑 intent 准确率
```

**读代码**：[services/classifier/intent.py](../services/classifier/intent.py) —— 注意 `_ensure_prototypes`（原型向量怎么来的）和三层各自的条件阈值。

***

## 第 10 课 多智能体编排：LangGraph 主从图

### 10.1 "主从"是什么

一个 **Supervisor（主控）** 只负责"看意图 → 派活给哪个 Specialist（专项 Agent）→ 检查回环"；6 个 **Specialist** 各管一摊业务。就像主编不亲自写稿，只分配和审稿。

### 10.2 图结构（[services/agent/builder.py](../services/agent/builder.py) + [state.py](../services/agent/state.py)）

```
START → supervisor（意图分类 + 路由）
              │ 路由 edge（根据意图条件跳转）
              ▼
        literature │ writing │ review │ ...（6 个 specialist 节点）
              ▼
        supervisor 再评估：任务完成？→ END；还要继续？→ 再路由（≤3 跳防回环）
```

`AgentState`（TypedDict）是整个图的"共享黑板"，节点往里写、下个节点读。

### 10.3 人机介入到底怎么实现（面试点）

[services/agent/agents/specialists.py](../services/agent/agents/specialists.py) 里用 LangGraph 的 `interrupt()`：

- 专项 Agent 判断"这一步需要用户确认"（比如"确定用这个选题吗？"）→ 调用 `interrupt(payload)`；

- 图在此**挂起**，状态由 `TieredCheckpointer`（PG→Redis→内存三级降级）保存；

- 用户在前端看到问题并反馈 → 前端调 `/api/agent/resume` → LangGraph `Command(resume=feedback)` 从挂起点接着跑。

```python
# specialists.py 中伪代码示意
need_confirm = await _need_confirmation(state)
if need_confirm:
    feedback = interrupt({"question": "按这个大纲继续吗?"})
    # 用户反馈后从这里继续
```

### 10.4 动手

```powershell
envs\lunjiang\python.exe scripts/smoke_graph.py    # 路由 + 中断恢复自检
```

**读代码**：顺序读 `services/agent/state.py` → `builder.py` → `supervisor.py` → `agents/specialists.py`（第 4 个文件较长，先读 `SpecialistSpec` 类）。

***

## 第 11 课 工具治理：限流 / 熔断 / 重试 / 锁 / RBAC / Skill

### 11.1 为什么 LLM 调用工具要一层"治理栈"

LLM 会乱调工具（幻觉参数、重复调用、一次调几十次），外部工具也会失败、变慢。治理栈就是**给"AI 调用工具"这件事装安全气囊**：

```
services/governance/
├── tool_registry.py     注册中心：从 configs/tools.yaml 读取工具清单并缓存（类别属性级缓存）
├── rate_limiter.py      Redis ZSET 滑动窗口限流（1 分钟窗口）
├── circuit_breaker.py   三态熔断：CLOSED → OPEN(连续失败5次) → HALF_OPEN(30s后试探)
├── retry.py             指数退避重试（0.5s 起，最大 8s），三次后降级/抛人机兜底
├── dist_lock.py         分布式锁（SETNX + TTL + 续期），防并发重复执行
├── skill.py             行为观测：同模式成功 3 次 → 自动沉淀成 Skill
└── tools_impl.py        具体工具实现（search_literature / generate_section / check_format...）
```

### 11.2 一次工具调用完整的旅程（[services/governance/tool\_registry.py](../services/services/governance/tool_registry.py) 的 `ToolRegistry.call()`）

```
① RBAC 校验角色是否允许用这个工具（configs/rbac.yaml）
   ↓
② 限流 check_rate（Redis 滑动窗口）
   ↓
③ 熔断器 before_call（OPEN 直接拒）
   ↓
④ acquire 分布式锁
   ↓
⑤ resilient_call 重试（指数退避）
   ↓
⑥ 执行 tools.yaml 注册的 handler
   ↓
⑦ 熔断器 on_success/on_failure 更新状态
   ↓
⑧ 审计 write_audit（参数截断 200 字符 + 指纹化）—— fire-and-forget 异步
   ↓
⑨ Skill 观测 observe()（连续 3 次同模式成功 → 沉淀 Skill）
```

**这就是"治理栈 9 项"冒烟测试测的东西**（`scripts/smoke_governance.py`）。

### 11.3 动手

```powershell
envs\lunjiang\python.exe scripts/smoke_governance.py
```

**读代码**：先读 `rate_limiter.py`（Lua 脚本怎么保证原子性）和 `circuit_breaker.py`（状态机怎么落地），再啃 `tool_registry.py`。

***

## 第 12 课 流式输出与全链路可观测

### 12.1 SSE 流式：EventHub 事件总线（[services/streaming/hub.py](../services/streaming/hub.py)）

难点：Agent 图是异步多节点，token 是一个个出的，**节点事件（"正在写第 3 章"）和 token 流会时序交错**。解决思路：

- 一个 `asyncio.Queue` 发放全链路事件；

- 事件分两类：`token`（文本增量）和 `event`（节点开始/工具调用等元信息）；

- token 走**微缓冲**：攒一个小批次再推，避免"一段文字被切成几十个碎片"；

- 前端用 EventSource 订阅，同一队列出流，天然有序。

```python
hub.emit("event", {"node": "literature", "status": "running"})
async for chunk in provider.chat_stream(...):
    await hub.emit_token(chunk)     # 微缓冲
await hub.flush_tokens()
```

### 12.2 全链路可观测：Trace Span（[services/observability/trace.py](../services/services/observability/trace.py)）

`span(name)` 是上下文管理器，自动记录开始/结束/耗时/参数摘要，生成**树形嵌套**（父 span 包子 span）。全程落 PG `trace_spans` 表；后台 admin 接口可回放一棵"行为树"。

### 12.3 动手

```powershell
envs\lunjiang\python.exe scripts/smoke_trace.py
```

**读代码**：[services/streaming/hub.py](../services/streaming/hub.py)（关注 `emit_token` 的微缓冲阈值）、[services/observability/trace.py](../services/services/observability/trace.py)。

***

## 第 13 课 前端与端到端打通

前端（[frontend/src/](../frontend/src/)）= React 18 + Vite + SSE：

| 文件               | 职责                                    |
| ---------------- | ------------------------------------- |
| `main.jsx`       | 入口                                    |
| `App.jsx`        | 登录/注册、项目页、对话页 + 时间线；助手消息走 Markdown    |
| `api.js`         | fetch 封装：自动带 token、解析 SSE 事件流         |
| `styles.css`     | 全局样式（Markdown 排版）                     |
| `vite.config.js` | dev 代理 `/api → http://127.0.0.1:8000` |

SSE 消费侧要点：`api.js` 里把 `POST /api/agent/chat` 的事件流按类型分发——`event` 更新"Agent 正在做什么"，`token` 追加文本，`final` 收尾。

### 端到端自检

```powershell
envs\lunjiang\python.exe scripts/smoke_api.py --topic   # 注册→登录→建项目→对话，需先起 uvicorn
```

***

## 第 14 课 用评测体系守住质量

### 14.1 评测 = 三个数据集 + 一个 harness

`evals/` 的结构：

```
datasets/
├── intent.jsonl           意图分类测试集（200 条？看文件即知，格式 {"text":..., "label":...}）
├── retrieval.jsonl        RAG 常规检索测试集
├── retrieval_hard.jsonl   RAG 长尾困难集（绕口令式改写查询）
harness.py                 三项指标评测入口
ab.py                      A/B 实验：同一数据集，不同配置/策略对比，输出图表+报告
```

```powershell
envs\lunjiang\python.exe evals/harness.py     # 三项指标
envs\lunjiang\python.exe evals/ab.py          # A/B：简单集 vs 长尾困难集
```

### 14.2 用 A/B 学会"拿证据说话"

第 1 轮优化做了一个经典 A/B：**Query 改写开关对比**。

| 组  | 配置           | 长尾困难集 Recall\@5       |
| -- | ------------ | --------------------- |
| B  | 改写关          | 差（基准）                 |
| A₀ | 改写开（未修复）     | 漂移导致更低                |
| A₁ | 改写开 + 防漂移三件套 | **100% 恢复，MRR +0.17** |

结论：**"改写对简单查询是负优化，对长尾复杂查询是强优化"**——于是 README 与 settings.yaml 里写"小语料库建议关闭改写"。这就是"文档结论必须由数据支撑"的样本。

***

## 第 15 课 独立重建的最小路线图

如果你想**自己动手复刻一遍**（求职/毕设高价值），推荐按以下顺序，每一步都是可运行的最小版本：

| 阶段 | 做什么                                         | 时间投入 | 里程碑    |
| -- | ------------------------------------------- | ---- | ------ |
| 1  | FastAPI + /health + 配置层（课 3）                | 0.5h | 服务能起   |
| 2  | PG + Redis 连接 + 两张表（用户/项目）（课 4）             | 1h   | 数据能存   |
| 3  | 注册/登录 JWT + bcrypt（课 5）                     | 1h   | 认证闭环   |
| 4  | LLMProvider 封装 + 一个对话接口（课 6）                | 1h   | 能聊天    |
| 5  | 短期记忆（Redis）+ 压缩雏形（课 7）                      | 1h   | 有上下文   |
| 6  | 语料入库 + 双路召回 + RRF（课 8，可以先不做改写/精排）           | 2h   | 会检索    |
| 7  | 意图分类（先做规则层）（课 9）                            | 1h   | 会分流    |
| 8  | LangGraph supervisor + 1 个 specialist（课 10） | 2h   | 多智能体雏形 |
| 9  | 工具治理：限流 + 重试 两件（课 11）                       | 1.5h | 可靠     |
| 10 | EventHub + SSE（课 12）                        | 1h   | 打字机了   |
| 11 | 简单 React 页面（课 13）                           | 2h   | 能演示    |
| 12 | 评测集 + harness（课 14）                         | 1.5h | 有数据    |

自己重建时**先砍需求再迭代**：只保留 4 个 specialist、双路召回不做精排、治理只要限流+重试——先跑通再补全，最后逐项对齐本项目（本项目就是你的"参考答案"）。

***

## 附录 关键类与调用链速查

### 一次对话的调用链（对应文件）

```
api/agent/router.py → AgentEngine.run()
    → services/memory/（四层组装）
    → services/agent/engine.py：绑定 EventHub → 跑 LangGraph 图
        → supervisor_node（意图分类：services/classifier/intent.py）
        → specialists/xx 节点
            → services/governance/tool_registry.py: ToolRegistry.call()
                → rate_limiter / circuit_breaker / retry / dist_lock
                → tools_impl.search_literature()
                    → services/rag/pipeline.py: RagPipeline.search()
                        → query_rewrite → retriever(dense+sparse, RRF) → reranker
    → EventHub → SSE
services/observability/trace.py 全程 span 记录；api/middleware/audit.py 后台审计
```

### 类/函数速查表

| 你想找……       | 去哪里                                                                 |
| ----------- | ------------------------------------------------------------------- |
| 全局配置        | `infrastructure/config.py` `get_settings()`                                    |
| LLM 调用      | `services/llm/provider.py` `LLMProvider`                                |
| 向量化         | `LLMProvider.embed()`（bge-m3，1024 维）                                |
| 短期记忆        | `services/memory/short_term.py` `ShortTermMemory`                            |
| 记忆压缩        | `services/memory/compressor.py` `compress_window_if_needed()`                |
| RAG 入口      | `services/rag/pipeline.py` `RagPipeline.search()`                            |
| 双路召回 + RRF  | `services/rag/retriever.py` `HybridRetriever.rrf_fuse()`                     |
| 意图分类        | `services/classifier/intent.py` `IntentClassifier.classify()`           |
| 图构建         | `services/agent/builder.py` `build_graph()`                             |
| 主控节点        | `services/agent/supervisor.py` `supervisor_node()`                      |
| 专项 Agent 定义 | `services/agent/agents/specialists.py` `SpecialistSpec` / `SPECIALISTS` |
| 工具治理入口      | `services/governance/tool_registry.py` `ToolRegistry.call()`                 |
| 工具实现        | `services/governance/tools_impl.py` `register_all()`                         |
| 流式事件        | `services/streaming/hub.py` `EventHub`                                  |
| 检查点（中断恢复）   | `services/checkpoint/tiered.py` `TieredCheckpointer`                    |
| Trace       | `services/observability/trace.py` `span()`                                   |
| 语料入库        | `services/rag/ingest/corpus_loader.py` `ingest_corpus()`                     |
| 评测          | `evals/harness.py` / `evals/ab.py`                                  |

### 环境检查 5 项对应关系

`scripts/check_env.py` 的 5 个检查项 = 5 个"地基"：

| 检查项              | 对应第几课  | 失败时看哪里                                           |
| ---------------- | ------ | ------------------------------------------------ |
| Ollama 对话模型      | 课 6    | Ollama 是否 `ollama serve`；`num_ctx` OOM（见 FAQ Q1） |
| Ollama Embedding | 课 8    | 是否 `ollama pull bge-m3`                          |
| Redis            | 课 4/11 | 服务是否在 6379；只读内存                                  |
| PostgreSQL 连接    | 课 4    | 5433 实例启停命令（见 README）                            |
| pgvector 扩展      | 课 4    | 是否 `CREATE EXTENSION vector`（脚本自动建）              |

***

<p align="center">学完 15 课 + 附录，你就有能力独立搭建（甚至改进）一个多智能体论文助手。</p>
<p align="center">与实现不一致的地方，以实际代码为准——发现问题欢迎补充完善本文档。</p>
