# 论匠 · 学习指南（从零理解并重建本项目）

> 文档域：general
> 文档类型：操作手册 / 指南
> 主题版本：—
> 轮次：—
> 日期：2026-09-02
> 状态：已落地

> 这份文档的目标：**让你从一张白纸开始，按"重新独立构建"的思维把整个项目推演出来**。
> 读懂它 = 理解了这个项目的全部设计决策；照着做 = 能在自己机器上逐步复现一个最小可用版本。
>
> **文档分三部分，按需跳读：**
>
> | 部分 | 课次 | 回答什么问题 | 适合谁 |
> | --- | --- | --- | --- |
> | 第一部分 设计推演 | 第 0–16 课 | **为什么**这样设计？技术选型背后的取舍是什么？ | 第一次接触本项目，先建立整体认知 |
> | 第二部分 模块解剖 | 第 17–25 课 | 每个模块**具体怎么实现**？数据怎么流动？谁调谁？ | 已读过第一部分，要动手改代码 / 准备面试 |
> | 第三部分 从零复现 | 第 26–28 课 | 怎么在**自己机器上跑起来**并逐项验证？ | 要独立复现、复刻到毕设 / 作品集 |
>
> 每一课都留了「读代码」和「动手做」两个动作。第一部分通读约一个晚上；第二、三部分可以按需跳读。

***

## 目录

- [第 0 课 先想清楚：一个论文助手要解决什么问题](#第-0-课-先想清楚一个论文助手要解决什么问题)

- [第 1 课 设计一张总数据流图](#第-1-课-设计一张总数据流图)

- [第 2 课 技术选型：每一块为什么是它](#第-2-课-技术选型每一块为什么是它)

- [第 3 课 从最小骨架起步：FastAPI + 配置层](#第-3-课-从最小骨架起步fastapi--配置层)

- [第 4 课 存储底座：PostgreSQL(pgvector) + Redis](#第-4-课-存储底座postgresqlpgvector--redis)

- [第 5 课 认证：JWT + bcrypt + 登录限流](#第-5-课-认证jwt--bcrypt--登录限流)

- [第 6 课 LLM 接入层：统一入口，多底座切换](#第-6-课-llm-接入层统一入口多底座切换)

- [第 7 课 记忆体系：四层记忆 + 自动压缩](#第-7-课-记忆体系四层记忆--自动压缩)

- [第 8 课 三阶段 RAG：改写 → 召回 → 精排](#第-8-课-三阶段-rag改写--召回--精排)

- [第 9 课 意图预分类：规则 → 向量 → LLM 三级兜底](#第-9-课-意图预分类规则--向量--llm-三级兜底)

- [第 10 课 多智能体编排：LangGraph 主从图](#第-10-课-多智能体编排langgraph-主从图)

- [第 11 课 工具治理：限流 / 熔断 / 重试 / 锁 / RBAC / Skill](#第-11-课-工具治理限流--熔断--重试--锁--rbac--skill)

- [第 12 课 流式输出与全链路可观测](#第-12-课-流式输出与全链路可观测)

- [第 13 课 前端与端到端打通](#第-13-课-前端与端到端打通)

- [第 14 课 用评测体系守住质量](#第-14-课-用评测体系守住质量)

- [第 15 课 独立重建的最小路线图](#第-15-课-独立重建的最小路线图)

- [第 16 课 项目知识库与复合任务规划（第 4/5 轮扩展）](#第-16-课-项目知识库与复合任务规划第-45-轮扩展)

**第二部分 · 八大能力模块解剖（第 0 课基础设施层 + 第 17–25 课）**

- [第 0 课 基础设施层（infrastructure）· 九段骨架的地基](#第-0-课-基础设施层infrastructure-九段骨架的地基)

- [第 17 课 意图分类（classifier）](#第-17-课-意图分类classifier)

- [第 18 课 记忆体系（memory）](#第-18-课-记忆体系memory)

- [第 19 课 检索 rag](#第-19-课-检索-rag)

- [第 20 课 工具实现（tools_impl）](#第-20-课-工具实现tools_impl)

- [第 21 课 工具治理栈（governance）](#第-21-课-工具治理栈governance)

- [第 22 课 可观测（observability）](#第-22-课-可观测observability)

- [第 23 课 人机介入（interrupt）](#第-23-课-人机介入interrupt)

- [第 24 课 流式输出（streaming）](#第-24-课-流式输出streaming)

- [第 25 课 编排中枢（agent）](#第-25-课-编排中枢agent)

**第三部分 · 从零复现实操（第 26–28 课）**

- [第 26 课 环境准备：从裸机到全绿](#第-26-课-环境准备从裸机到全绿)

- [第 27 课 运行启动与端到端自检](#第-27-课-运行启动与端到端自检)

- [第 28 课 八大能力复现清单](#第-28-课-八大能力复现清单)

- [附录 关键类与调用链速查](#附录-关键类与调用链速查)

- [附录二 模块依赖矩阵](#附录二-模块依赖矩阵)

- [附录三 常见问题 FAQ](#附录三-常见问题-faq)

- [附录四 设计决策回溯：被否决的方案与代价](#附录四-设计决策回溯被否决的方案与代价)

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

| 能力      | 顶层包                                 |
| ------- | ----------------------------------- |
| ① 意图分类  | `services/classifier/`              |
| ② 记忆    | `services/memory/`                  |
| ③ 检索    | `services/rag/`                     |
| ④ 工具    | `services/governance/tools_impl.py` |
| ⑤ 治理    | `services/governance/`              |
| ⑥ 可观测   | `services/observability/`           |
| ⑦ 人机介入  | `services/agent/`（interrupt 机制）     |
| ⑧ 流式    | `services/streaming/`               |
| 编排所有智能体 | `services/agent/`                   |

> 💡 学习心得：**好的项目结构是先有需求地图，再有代码目录**。你不需要背目录，只要记住这张能力表。

### 0.3 验收标准要可量化

写作项目的通病是"感觉能用"，无法向面试官/老板证明。本项目给每项能力定了量化指标（`evals/` 就是干这个的）：

| 指标            | 目标     | 定义                                 |
| ------------- | ------ | ---------------------------------- |
| 意图分类准确率       | ≥ 98%  | 三层分类器在评测集（22 条）上的正确率              |
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
⑤ Specialist 文献 Agent    （services/agent/specialists/）
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
    ...

def _interpolate(node):     # ② 递归替换字符串中的 ${VAR} 占位符，缺失即报错
    ...

@lru_cache
def get_settings():         # ③ 全局单例，读 configs/settings.yaml + 插值
    ...

def get_value(*keys, default=None):     # ④ get_value("llm", "default_provider")
    ...
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
envs\lunjiang\python.exe -m uvicorn main:app --port 8000
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

角色控制同理：`require_role("admin")` 是依赖工厂，`/api/observability/traces` 就只对 admin 开放（[api/observability/router.py](../api/observability/router.py)）。

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

## 第 6 课 LLM 接入层：统一入口，多底座切换

### 6.1 现成的仓库问题

项目要支持 Ollama / DeepSeek / 智谱 / 通义 / agnes 等多种模型，但它们都兼容 **OpenAI 协议**。所以正确做法是：**统一封装一层，内部切换 base\_url**；同时**对话与嵌入可分离底座**（如默认对话走云端 agnes-2.5-flash、嵌入走本地 bge-m3）。

### 6.2 LLMProvider 类（[services/llm/provider.py](../services/llm/provider.py)）

对外只暴露四个方法，全项目都只用它：

```python
class LLMProvider:
    async def chat(messages, *, temperature, max_tokens, json_mode) -> str: ...
    async def chat_stream(messages) -> AsyncIterator[str]: ...
    async def embed(texts) -> list[list[float]]: ...            # 向量化
    async def chat_tools(messages, tools, executor) -> dict: ... # 工具调用循环
```

几个设计点：

- **客户端缓存**：按 `(provider, base_url, api_key)` 复用 `AsyncOpenAI` 实例（第一次审查优化加的），避免每次工具调用都重建 TCP 连接；

- **`_extra()`** **provider 特殊参数**：本地 Ollama 传 `think: False`（关掉 qwen3 的思考链，省时）和 `options.num_ctx=4096`（限制上下文防内存爆炸，第 2 轮优化加的）；

- **对话/嵌入双底座解耦**（第 5 轮优化加，第 6 轮升级）：`__init__()` 里按 `llm.embedding_provider` 单独解析嵌入 client 与模型（默认 ollama/bge-m3），chat 仍走 `default_provider`；pgvector 列维度不再硬编码，`models/memory.py` 用 `Vector(get_embedding_dim())` 按运行时底座读取 `providers.*.embedding_dim`（`infrastructure/config.py`），且 `embed()` 返回维度与配置不符时直接抛错——**换底座维度变化（如 zhipu 2048）也只在建表/迁移时处理，不再悄悄错**；

- **`json_mode`** **容错解析**：`_extract_json()` 剥掉 markdown 代码块再取第一对 `{ }`，因为 LLM 的输出格式不稳。

### 6.3 切换底座

改 [configs/settings.yaml](../configs/settings.yaml) 一行：

```yaml
llm:
  default_provider: agnes          # 对话底座 ← 可选 ollama / deepseek / zhipu / qwen
  embedding_provider: ollama       # 嵌入底座与对话解耦（本地 bge-m3）
```

代码零改动。

### 6.4 Function-Calling 循环：Agent 真正"干活"的地方（重点）

前面三个方法都是"一次问答"，而 `chat_tools()` 是整个 Agent 系统的主循环：**LLM 决定调什么工具 → 执行拿到结果 → 把结果喂回去继续决策**。第 20/25 课会讲工具怎么注册、节点怎么编排，这里把循环本身讲透。

看 [services/llm/provider.py](../services/llm/provider.py) 的 `chat_tools()`（L145-192）：

```python
for round_i in range(max_rounds):                          # ① 最多 3 轮
    resp = await client.chat.completions.create(..., tools=tools)
    msg = resp.choices[0].message
    if not msg.tool_calls:                                # ② LLM 决定收手 → 返回
        return {"content": msg.content, "tool_calls": all_calls, "rounds": round_i + 1}
    msgs.append(msg.model_dump(exclude_none=True))        # ③ "我要调工具"的答复也记入对话
    for tc in msg.tool_calls:
        name, args = tc.function.name, _extract_json(tc.function.arguments)
        result = await tool_executor(name, args)          # ④ 真正执行（接治理栈，见第 21 课）
        msgs.append({"role": "tool", "tool_call_id": tc.id,
                     "content": _stringify(result)})      # ⑤ 结果回灌
final = await self.chat(msgs, ...)                        # ⑥ 超限收尾：不带工具再问一次
```

四件关键事（面试高频，务必逐条看懂）：

1. **对话里出现第二种消息：`role="tool"`**。LLM 的工具调用与结果靠 **`tool_call_id` 一一配对**（L188-189）——id 对不上，LLM 就认不出"这是我刚才那个调用"的结果；工具结果还要经 `_stringify()` **截断 3000 字符**（L215-220），否则一次检索返回的片段就能把上下文撑爆；
2. **`max_rounds=3` 是防"贪玩"的闸**：LLM 可能一轮接一轮地调工具不收敛。超限后**不带工具再收尾一次**（L190-192），保证无论怎样都有一段正文交差；
3. **参数解析是容错的**（L180-184）：LLM 输出的 `arguments` 可能是非 JSON、可能是裸字符串，`_extract_json()` 失败一律回退 `{}`，绝不让循环崩；
4. **`chat()` 里还有个隐蔽坑**（L91-95）：qwen3 这类**思考型模型**会把 `max_tokens` 预算耗尽在 reasoning 上、正文返回空——所以"正文为空且有上限"时**去掉上限重试一次**。

**验证**（伪造一个 executor，观察轮次与调用记录；需 LLM 底座在线）：

```powershell
envs\lunjiang\python.exe -c "
import asyncio
from services.llm.provider import LLMProvider

async def fake_executor(name, args):
    print(f'  -> 工具被调: {name} {args}')
    return {'note': '这是工具结果，会被 _stringify 截断后回灌'}

async def main():
    p = LLMProvider()
    tools = [{'type': 'function', 'function': {
        'name': 'fake_tool', 'description': '测试工具',
        'parameters': {'type': 'object', 'properties': {'q': {'type': 'string'}}}}}]
    r = await p.chat_tools(
        [{'role': 'user', 'content': '请调用 fake_tool 查询一下（q=rag），然后一句话总结结果'}],
        tools, fake_executor, max_rounds=2)
    print('rounds =', r['rounds'], '| 调用过:', [c['name'] for c in r['tool_calls']])
asyncio.run(main())
"
```

预期：控制台先出现 `-> 工具被调: fake_tool {...}`（证明 ④ 真正执行了），随后打印 `rounds = 1`（LLM 拿到结果后决定收手，走 ② 分支）与本次调用清单。

**读代码**：[services/llm/provider.py](../services/llm/provider.py) —— 建议顺序：先读 `chat()` 与 `embed()` 熟悉调用方式，最后**重点读 6.4 讲的 `chat_tools()`（L145-192）**。

***

## 第 7 课 记忆体系：四层记忆 + 自动压缩

### 7.1 为什么是"四层"而不是"一个聊天记录"

单轮对话是 **"短期对话"**（Redis），但如果用户第二天回来，Redis 过期了怎么办？如果用户换了个项目、或者问的是自己长期偏好呢？所以按**生命周期从短到长**分四层：

```
短期对话 services/memory/short_term.py    本轮/近 N 轮（Redis List + TTL 30 天）
项目结构化 services/memory/structured.py   该论文项目的题目/大纲/结论（PG）
长期向量   services/memory/long_term.py    历史沉淀的知识点（PG Vector 相似度 + 重要度加权召回）
用户偏好   services/memory/preference.py   用户长期习惯（"我偏好综述式回答"）
```

### 7.2 短期记忆怎么实现（[services/memory/short\_term.py](../services/memory/short_term.py)）

Redis 里一个 key 存一个会话的多条消息（`chat:{project_id}:{session_id}`），方法签名一览：

```python
async def append(project_id, session_id, role, content): ...
async def history(project_id, session_id, last_n=None) -> list[dict]: ...
async def total_chars(project_id, session_id) -> int: ...
async def evict_compressed(project_id, session_id, keep_last) -> list[dict]: ...
```

### 7.3 上下文压缩（[services/memory/compressor.py](../services/memory/compressor.py)）

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

| 阶段         | 痛点                             | 解决                                                                         |
| ---------- | ------------------------------ | -------------------------------------------------------------------------- |
| ① Query 改写 | 用户话太口语（"那篇讲可解释性的"），直接搜匹配差      | 先改写成检索友好的查询：LLM 改写 + 规则字典兜底 + 拒答/漂移回退（防漂移，见 8.3）                           |
| ② 混合召回     | 单路向量漏关键词，单路 BM25 漏同义改写         | 稠密(pgvector) + 稀疏(BM25/jieba) + **相邻窗口**多路召回，**RRF 分数融合**（项目知识库场景另有项目路与保底） |
| ③ 交叉精排     | 召回 20 条里有 15 条噪音，直接进 LLM 浪费上下文 | bge-reranker-base 交叉编码器逐条打分，只留 Top5（含降噪对比）                                 |

### 8.2 各文件职责

```
services/rag/ingest/corpus_loader.py   语料 *.txt → 分块(512字符, 64重叠) → bge-m3 向量 → 入 pgvector + 重建 BM25
services/rag/ingest/parsers.py         项目知识库文档解析器工厂（PDF/DOCX/TXT/MD，扫描件拒绝）
services/rag/ingest/pipeline.py        知识库文档 上传→解析→分块→向量化入库（MD5去重/批量embedding）
services/rag/retriever.py              HybridRetriever：dense_search / sparse_search / project_dense_search / sibling_search / rrf_fuse
services/rag/reranker.py               Reranker：bge-reranker-base（CPU 多线程 + 本地缓存检测）
services/rag/query_rewrite.py          rewrite_query(mode=off|auto|on)：难度自适应（简单短句跳过 LLM），失败/拒答/漂移回退规则字典改写
services/rag/pipeline.py               RagPipeline.search()：把上面串成流水线（多路融合 + 项目保底 + 降噪）
```

### 8.3 防漂移三件套（第 1 轮 A/B 实验的重要产出）

LLM 改写并不总是变好，两种典型翻车：

- **语义漂移**：改写后意思变了（召回错的东西）；

- **越域拒答**：改写模型说"这不归我管"返回空。

修复（[services/rag/pipeline.py](../services/rag/pipeline.py) + [query\_rewrite.py](../services/rag/query_rewrite.py)）：

```
改写器拒答/输出过短/语义漂移（字符重合度<0.15） → 回退规则字典改写（第4轮升级，不再直接回退原查询）
改写生效时 → 原查询独立一路稠密召回参与 RRF 融合（语义锚点兜底）
精排阶段 → 改写查询与原查询两份分数取更高的
```

A/B 数据支撑：Recall\@5 100% 恢复，MRR 0.917（比基准 +0.17）。**这就是"用评测说话"的范例**（见第 14 课）。

### 8.4 动手

```powershell
envs\lunjiang\python.exe scripts/ingest_corpus.py     # 先把语料入库
envs\lunjiang\python.exe scripts/smoke_rag.py         # 三阶段检索自检
```

**读代码**：[services/rag/retriever.py](../services/rag/retriever.py)（重点 `rrf_fuse`，理解 RRF 公式）、[services/rag/ingest/pipeline.py](../services/rag/ingest/pipeline.py)、[services/rag/pipeline.py](../services/rag/pipeline.py)。

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

实测：`evals/datasets/intent.jsonl`（22 条）上 100% 准确（均值耗时约 56ms，随 LLM 底座波动）。

### 9.3 动手

```powershell
envs\lunjiang\python.exe evals/harness.py     # 会跑 intent 准确率
```

**读代码**：[services/classifier/intent.py](../services/classifier/intent.py) —— 注意 `_ensure_prototypes`（原型向量怎么来的）和三层各自的条件阈值。

***

## 第 10 课 多智能体编排：LangGraph 主从图

### 10.1 "主从"是什么

一个 **Supervisor（主控）** 只负责"看意图 → 派活给哪个 Specialist（专项 Agent）→ 检查回环"；6 个 **Specialist** 各管一摊业务，另有 1 个 **Planner** 处理"先检索、再撰写、最后出大纲"这类复合任务（第 4 轮加入）。就像主编不亲自写稿，只分配和审稿。

### 10.2 图结构（[services/agent/builder.py](../services/agent/builder.py) + [state.py](../services/agent/state.py)）

```
START → supervisor（意图分类 + 路由）
              │ 路由 edge（简单任务 → specialist；复合任务 → planner）
              ▼
        literature │ writing │ review │ ...（6 个 specialist 节点）│ planner
              ▼
        supervisor 收尾评估（stop_reason=done/max_hops）→ END
        （图内为"一次 supervisor → 单一专项"的单轮接力；复合任务由 planner 内部多步完成，无多 Agent 回环再分配）
```

`AgentState`（TypedDict）是整个图的"共享黑板"，节点往里写、下个节点读。

> 💡 **与第 6 课手写 Function-Calling 循环的关系**（思路传递关键点）：第 6.4 把"LLM 决定调哪个工具 → 执行 → 把结果喂回 → 再问"的**单轮工具调用机制**讲透了（`LLMProvider.chat_tools`）。本项目真正跑多智能体时用的却是 LangGraph——**两者不是替代，而是分层**：
> - **第 6 课是"发动机原理"**：`chat_tools` 负责"一次 FC 循环"这个原子动作。每个 specialist 节点内部，仍然是这一套循环——它直接调用 `LLMProvider`（不经过 langchain 的 ChatModel 适配层，见 `provider.py:1-10`），把工具调用转交给 `ToolRegistry` 治理栈（第 21 课）。
> - **LangGraph 是"底盘 + 变速箱"**：负责图执行、状态黑板（`AgentState`）、checkpoint 持久化、interrupt 人机挂起这些"编排与生命周期"的事。
> - **真正的差异在"下一步谁来定"**：手写循环里靠代码 `if/else` 决定；LangGraph 里 `route()` 读 `state["next_agent"]` 决定（判断逻辑放进节点，路由只做翻译，更可观测、可测试，见第 25.4 ②）。
> 所以**第 6 课没被丢弃，而是被包进了节点里**。先懂发动机，才看得懂底盘为什么这么设计。

### 10.3 人机介入到底怎么实现（面试点）

[services/agent/specialists/node\_factory.py](../services/agent/specialists/node_factory.py) 里用 LangGraph 的 `interrupt()`：

- 专项 Agent 判断"这一步需要用户确认"（比如"确定用这个选题吗？"）→ 调用 `interrupt(payload)`；

- 图在此**挂起**，状态由 `TieredCheckpointer` 保存（Redis→PG→内存三级降级；**这里先记结论，装配与降级细节在第 23 课完整展开**）；

- 用户在前端看到问题并反馈 → 前端调 `/api/agent/resume` → LangGraph `Command(resume=feedback)` 从挂起点接着跑。

```python
# specialists/node_factory.py 伪代码示意
# （真实 interrupt 载荷另含 type/agent/proposal 字段，完整结构见 node_factory.py L66）
need_confirm = await _need_confirmation(state)
if need_confirm:
    feedback = interrupt({"question": "按这个大纲继续吗?"})
    # 用户反馈后从这里继续
```

### 10.4 动手

```powershell
envs\lunjiang\python.exe scripts/smoke_graph.py    # 路由 + 中断恢复自检
```

**读代码**：顺序读 `services/agent/state.py` → `builder.py` → `supervisor.py` → `specialists/specs.py`（先读 `SpecialistSpec` 定义）→ `specialists/node_factory.py`，复合任务再看 `services/agent/planner.py`（`is_complex_task` / `planner_node`）。

***

## 第 11 课 工具治理：限流 / 熔断 / 重试 / 锁 / RBAC / Skill

### 11.1 为什么 LLM 调用工具要一层"治理栈"

LLM 会乱调工具（幻觉参数、重复调用、一次调几十次），外部工具也会失败、变慢。治理栈就是**给"AI 调用工具"这件事装安全气囊**：

```
services/governance/
├── tool_registry.py     注册中心：tools.yaml 治理配置进程内单次加载（lru_cache）+ register() 幂等（重复注册同 handler 直接跳过）；同步 handler 自动经线程池执行
├── rate_limiter.py      Redis ZSET 滑动窗口限流（1 分钟窗口）
├── circuit_breaker.py   三态熔断：CLOSED → OPEN(连续失败5次) → HALF_OPEN(30s后试探)
├── retry.py             指数退避重试（0.5s 起，最大 8s），三次后降级/抛人机兜底
├── dist_lock.py         分布式锁（SETNX + TTL + 续期），防并发重复执行
├── skill.py             行为观测：同模式成功 3 次 → 自动沉淀成 Skill
├── tools_impl.py        论文工具实现（search_literature / generate_section / check_format...）
└── academic_tools.py    学术工具生态（翻译 / 润色 / 方法推荐 / 参考文献格式化 / 摘要 / 术语解析，第 5 轮加入）
```

### 11.2 一次工具调用完整的旅程（[services/governance/tool\_registry.py](../services/governance/tool_registry.py) 的 `ToolRegistry.call()`）

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

> 注：③ 熔断按 `tools.yaml` 的 `breaker` 分组生效；④ 分布式锁**仅 `lock_key` 非空时启用**——当前内置 14 个工具均未配置，属预留能力（装配示例见 `tests/test_tool_registry_call.py::test_call_distributed_lock_assembled_for_locked_tool`）。

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

- 事件按类型分层：`token`（文本增量，微缓冲）与节点生命周期/路由事件（`node_start`/`node_end`/`intent`/`route`/`interrupt`/`final`/`done`/`error`；Planner 运行时另发 `plan`/`step_event`，见第 16 课）；

- token 走**微缓冲**：攒一个小批次再推，避免"一段文字被切成几十个碎片"；

- 前端用 `fetch + ReadableStream.getReader()` 逐行解析 SSE（`/api/agent/chat` 是 **POST**，EventSource 只能 GET，故不用 EventSource；见 `frontend/src/api.js`），同一队列出流，天然有序。

```python
hub.emit("node_start", {"agent": "literature", "title": "文献检索Agent"})
async for chunk in provider.chat_stream(...):
    await hub.emit_token(chunk)     # 微缓冲
await hub.flush_tokens()
```

### 12.2 全链路可观测：Trace Span（[services/observability/trace.py](../services/observability/trace.py)）

`span(name)` 是上下文管理器，自动记录开始/结束/耗时/参数摘要，生成**树形嵌套**（父 span 包子 span）。全程落 PG `trace_spans` 表；后台 admin 接口可回放一棵"行为树"。

### 12.3 动手

```powershell
envs\lunjiang\python.exe scripts/smoke_trace.py
```

**读代码**：[services/streaming/hub.py](../services/streaming/hub.py)（关注 `emit_token` 的微缓冲阈值）、[services/observability/trace.py](../services/observability/trace.py)。

***

## 第 13 课 前端与端到端打通

前端（[frontend/src/](../frontend/src/)）= React 18 + Vite + SSE：

| 文件               | 职责                                    |
| ---------------- | ------------------------------------- |
| `main.jsx`       | React 入口                                    |
| `App.jsx`        | 登录/注册、项目页、对话页 + 时间线；**项目知识库面板**（上传/清单/检索）；主题切换器（A 柔雾青绿/B 黑白瑞士/C 暗墨夜山/D 青绿金碧，localStorage 记忆）；状态逻辑拆分为 4 个自定义 hook（`useTheme`/`useSessions`/`useProjects`/`useChat`，见 `src/hooks/`） |
| `api.js`         | fetch 封装：自动带 token、`fetch + getReader` 逐行解析 SSE 事件流；项目/知识库 API（`knowledge*` 4 接口） |
| `styles.css`     | 全局样式 + 四主题 design tokens（`:root`=A 主题，`body[data-theme="b|c|d"]` 三个 token 块；ROUND11 起 B 为黑白瑞士） |
| `vite.config.js` | dev 代理 `/api → http://127.0.0.1:8000`；生产 `base` 适配 GitHub Pages（仅 `NODE_ENV=production` 生效） |

SSE 消费侧要点：`api.js` 里把 `POST /api/agent/chat` 的事件流按类型分发——`node_start/route/node_end` 更新 "Agent 正在做什么"，`token` 追加文本，`plan/step_event` 展示 Planner 的规划与步骤，`final` 收尾。

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
├── intent.jsonl           意图分类测试集（22 条，格式 {"text":...,"intent":...}）
├── retrieval.jsonl        RAG 常规检索测试集
├── retrieval_hard.jsonl   RAG 长尾困难集（绕口令式改写查询）
├── retrieval_paper_hard.jsonl  论文辅助语料口语化长尾集（第 4 轮前新增，Recall@5 96.2%）
harness.py                 三项指标评测入口
ab.py                      A/B 实验：同一数据集，不同配置/策略对比，输出图表+报告
regression.py              七大必测场景回归（知识库入库/项目隔离/多路召回/改写/Planner/产物/治理）
```

```powershell
envs\lunjiang\python.exe evals/harness.py     # 三项指标
envs\lunjiang\python.exe evals/ab.py          # A/B：简单集 vs 长尾困难集
envs\lunjiang\python.exe evals/regression.py  # 七大必测场景回归（第 4 轮加入）
```

### 14.2 用 A/B 学会"拿证据说话"

第 1 轮优化做了一个经典 A/B：**Query 改写开关对比**。

| 组  | 配置           | 长尾困难集 Recall\@5       |
| -- | ------------ | --------------------- |
| B  | 改写关          | 差（基准）                 |
| A₀ | 改写开（未修复）     | 漂移导致更低                |
| A₁ | 改写开 + 防漂移三件套 | **100% 恢复，MRR +0.17** |

结论：**"改写对简单查询是负优化，对长尾复杂查询是强优化"**——于是 README 配置要点里提示 `rag.rewrite_enabled` 可按语料规模开关。这就是"文档结论必须由数据支撑"的范例。（R13 起升级为 `rag.rewrite_mode=auto` 查询级难度自适应：简单短句跳过 LLM 仅规则关键词，口语化长尾才走 LLM 改写，无需再人工开关，见 [ROUND13](OPTIMIZATION_ROUND13.md)。）

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
| 6  | 语料/知识库入库 + 多路召回 + RRF（课 8，可以先不做改写/精排/相邻窗口）  | 2h   | 会检索    |
| 7  | 意图分类（先做规则层）（课 9）                            | 1h   | 会分流    |
| 8  | LangGraph supervisor + 1 个 specialist（课 10） | 2h   | 多智能体雏形 |
| 9  | 工具治理：限流 + 重试 两件（课 11）                       | 1.5h | 可靠     |
| 10 | EventHub + SSE（课 12）                        | 1h   | 打字机了   |
| 11 | 简单 React 页面（课 13）                           | 2h   | 能演示    |
| 12 | 评测集 + harness（课 14）                         | 1.5h | 有数据    |
| 13 | Dockerfile + compose（PG/Redis/app 编排，`--scale` 多副本）（ROUND13） | 1h   | 可多实例部署 |

自己重建时**先砍需求再迭代**：只保留 4 个 specialist、多路召回先不做相邻窗口与项目保底、治理只要限流+重试——先跑通再补全，最后逐项对齐本项目（本项目就是你的"参考答案"）。

***

## 第 16 课 项目知识库与复合任务规划（第 4/5 轮扩展）

> 前 15 课覆盖平台骨架；本节补充两个升级项的完整用法：**项目级知识库**（每篇论文项目自己的私有资料库）与**复合任务规划器（Planner）**，以及配套的新配置项。签名以当前代码为准。

### 16.1 两个知识域：公共语料 vs 项目知识库

| 知识域 | 来源 | 存储 | 可见范围 |
| --- | --- | --- | --- |
| 公共语料库 | `data/corpus/*.txt`（内置 81 篇 / 1376 块） | `MemoryItem(kind="document")`，BM25 索引同域 | 所有用户共享 |
| 项目知识库 | 用户上传 PDF/DOCX/TXT/MD | 分块 `MemoryItem(kind="user_doc")` + 元数据 `KnowledgeDocument` | 仅该项目（跨项目隔离） |

- 文件级元数据（文件名/格式/MD5/状态）落 `knowledge_documents` 表；向量分块**复用 `MemoryItem`**，直接并入同一套稠密/稀疏/精排链路（方案 A：避免双轨检索代码）；
- 原始文件落盘 `data/uploads/{project_id}/`（已 gitignore）。

### 16.2 知识库数据流与 API 示例

链路：`上传 → infer_type(魔数/扩展名) → 大小上限 20MB → MD5 同项目去重 → 解析(线程池) → 分块(512/64) → 批量向量化(32/批) → status=ready`。

```python
import httpx

BASE = "http://127.0.0.1:8000"
c = httpx.AsyncClient()

token = (await c.post(f"{BASE}/api/auth/login",
                      json={"username": "u", "password": "p"})).json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# 1) 上传（可多文件；返回逐文件结果）
up = await c.post(f"{BASE}/api/projects/{pid}/knowledge", headers=h, files=[
    ("files", ("笔记.md", "# 检索系统笔记\n…".encode("utf-8"), "text/markdown")),
])
# → {"project_id","uploaded","ready","results":[{"status":"ready"|"skipped"|"failed","chunks","word_count",...}]}
#   skipped=同项目已存在相同内容（MD5 去重）；failed=解析失败（如扫描件无可提取文本）

# 2) 文档列表
docs = (await c.get(f"{BASE}/api/projects/{pid}/knowledge", headers=h)).json()["documents"]
# → [{id, filename, file_type, size_bytes, status, error, chunk_count, word_count, created_at}]

# 3) 库内检索
r = await c.post(f"{BASE}/api/projects/{pid}/knowledge/search", headers=h,
                 json={"query": "交叉编码器精排怎么做", "top_k": 5, "mode": "hybrid"})
# mode=project 仅库内；mode=hybrid 公共语料+库内融合（默认）
# → {"query","rewritten","keywords","results":[{doc_id, filename, source, content, score, noise_flag}]}

# 4) 删除（连同向量分块与原始文件一并清理）
await c.delete(f"{BASE}/api/projects/{pid}/knowledge/{doc_id}", headers=h)
```

### 16.3 多路召回与精排降噪

`RagPipeline.search(query, *, top_k=None, use_rewrite=True, use_rerank=True, project_id=None, no_project_only=False, rewrite_mode=None)` 阶段 2 的召回路：

> `rewrite_mode ∈ on/auto/off`（R13 起支持，透传 Query 改写模式）；`None` 时 `use_rewrite=True` 走配置 `rag.rewrite_mode`（默认 auto），`use_rewrite=False` 等效 off。评测脚本显式传 `on/off` 保持 AB 组别口径。

```
dense(改写)  稀疏BM25(改写)  关键词BM25(首词)  [原查询dense,改写生效时]  [项目知识库dense,传project_id]
        └─────────────────── RRF 融合 ───────────────────┘
相邻窗口 sibling_search（命中块 ±window，第三引擎补跨块上下文）
        └── 项目保底：项目路 Top-2 在窗口融合之后注入精排候选（排序仍由精排裁决）
```

- **精排降噪对比**（结果带 `noise_flag`）：稠密命中且排名靠前=`ok`；仅稀疏命中=`sparse_only`（0.982 软惩罚，关键词重叠噪声）；稠密命中但排名靠后=`weak`（0.995）；
- `project_id=None` → 仅公共语料；`no_project_only=True` → 仅项目知识库（库内检索用）。

### 16.4 Query 改写返回策略标记

`rewrite_query()` 现在返回 `{"rewritten", "keywords", "strategy"}`，可观测走了哪条路：

| strategy | 含义 |
| --- | --- |
| `llm` | LLM 改写成功且通过漂移检查（与原查询字符重合度 ≥0.15） |
| `rule_fallback` | LLM 拒答/输出过短/漂移/异常 → 回退规则字典改写 |
| `skip` | `mode=auto` 且判定为简单短句查询 → 跳过 LLM，仅产出规则关键词（零 LLM 开销，R13） |
| `idle` | `mode=off` 或 `rag.rewrite_enabled=false`，直接原查询（规则关键词仍可用于召回路） |

### 16.5 复合任务规划：事件流示例

`is_complex_task(user_input, intent)`（动作词≥3 / 命中"综述·开题·大纲"等目标词 / 长输入+写作意图）→ supervisor 路由 `planner` 节点。SSE 事件序列（连通实测）：

```
node_start(intent判定) → intent → route → node_end
  → node_start(planner) → plan {goal, steps:[{action, params, note}]}
  → step_event {step,total,action,status} ×N → node_end
  → node_start(supervisor 收尾) → node_end → final{output} → done
```

- 步骤经 `ToolRegistry.call()` 执行（自动获得 RBAC / 限流 / 熔断 / 审计）；
- **Replan**：步骤失败 → 带"简化要求"重试一次 → 仍失败记录并继续，部分成功不丢失；
- 前序步骤产物累积为 evidence，注入后续 LLM 步骤；
- 数值参数（`top_k`/`length` 等）在 `planner._coerce_params()` 归一化为 int（修复 LLM 输出 `"5"` 导致的切片 TypeError）。

### 16.6 结构化产物工具

```python
# 治理工具 generate_artifact：可直接调用，也可作为 Planner 步骤 action=generate_artifact
from services.governance.tools_impl import generate_artifact

out = await generate_artifact(
    kind="review_draft",        # review_draft 综述初稿 / proposal_report 开题报告 / defense_outline 答辩大纲
    topic="图神经网络的推荐系统应用",
    requirement="本科毕业论文",
    project_id=123,             # 可选：把该项目知识库一并作为证据源
)
# → {"kind","artifact_name","topic","content"(Markdown),"evidence_count","sources":[{title,source}]}
```

产物骨架固定（综述 5 节 / 开题 6 节 / 答辩 6 节+QA≥8 条），生成前自动 RAG 检索证据并注入提示词，正文按 [编号] 标注来源。

### 16.7 新增配置项速查

| 配置键 | 默认 | 说明 |
| --- | --- | --- |
| `llm.default_provider` | `agnes` | 对话底座（agnes-2.5-flash，KEY 在 .env） |
| `llm.embedding_provider` | `ollama` | 嵌入底座与对话解耦（本地 bge-m3） |
| `rag.rewrite_enabled` | `true` | Query 改写总开关（false 时恒为 idle） |
| `rag.rewrite_mode` | `auto` | 难度自适应：off=关闭 / auto=短句简单查询跳过 LLM（strategy=skip），长尾才走 LLM / on=强制 LLM（R13） |
| `rag.sibling_window` | `1` | 相邻窗口半径（0=关闭第三引擎） |
| `rag.max_upload_size_mb` | `20` | 知识库单文件大小上限 |
| `rag.knowledge.upload_dir` | `data/uploads` | 原始文件落盘目录（gitignore） |
| `rag.knowledge.min_text_chars` | `30` | 低于该字数视为扫描件/空文档（拒绝+failed） |
| `memory.recall_semantic_weight` | `0.7` | 长期记忆召回：语义距离权重（0~1，importance 为次因子，R13） |
| `governance.audit.sanitize_chars` | `200` | 审计参数截断阈值：超该字符数 → 哈希指纹+摘要+长度（R13 合规） |

```yaml
# configs/settings.yaml 片段
rag:
  rewrite_enabled: true
  rewrite_mode: auto        # off/auto/on，简单短句跳过 LLM（R13）
  sibling_window: 1
  max_upload_size_mb: 20
  knowledge:
    upload_dir: data/uploads
    min_text_chars: 30
```

### 16.8 动手

```powershell
envs\lunjiang\python.exe evals/regression.py   # S1 入库/S2 隔离/S3 多路/S4 改写/S5 Planner…
envs\lunjiang\python.exe scripts/load_test.py  # 知识库检索并发压测（先起 uvicorn）
```

**读代码**：`services/rag/ingest/pipeline.py`（入库链路）→ `services/rag/pipeline.py`（多路+保底+降噪）→ `services/rag/query_rewrite.py`（规则兜底）→ `services/agent/planner.py`（规划器）→ `services/governance/artifacts.py`（产物模板）。

***

# 第二部分 · 八大能力模块解剖（第 0 课地基 + 第 17–25 课）

> 第一部分回答「为什么这么设计」，第二部分回答「**代码到底怎么写的、数据在里头怎么流动**」。
> 九大能力模块 + 第 0 课基础设施层（共十课）统一用同一个八段式模板，读熟一课后其余可跳读：

| 段 | 回答的问题 |
| --- | --- |
| N.1 问题与契约 | 输入是什么、输出是什么（**先定边界，再看代码**） |
| N.2 文件清单 | 包里每个文件干什么 |
| N.3 核心数据结构 | 关键字段逐个解释（基础薄弱者最容易卡在这一段） |
| N.4 代码走读 | 关键函数逐块讲解，全程带 `file:line` |
| N.5 调用关系 | 谁调用我、我调用谁 |
| **N.6 最小可复现骨架** | **把模块核心逻辑压成几十行代码（复用第 0 课基础设施层即可跑通）** |
| N.7 验证与预期输出 | 可复制的命令 + 应该看到什么 |
| N.8 面试点与坑 | 值得背下来的结论 / 实现里的已知边界 |

> 🎯 **N.6 是本部分的核心**：每一段骨架代码都刻意去掉了日志、降级等非本质代码，
> 只保留"这个模块之所以是它"的那部分逻辑；**配置读取由第 0 课基础设施层统一提供——本部分九段模块骨架 + 第 0 课 = 可运行后端**。**能独立写出「第 0 课 + 九段模块骨架」= 能独立复现本项目后端核心**。
> 建议学习方式是：先读第 0 课把地基搭好 → 读某课 N.4 → 关掉源码 → 自己照着 N.6 敲一遍（import 第 0 课）→ 跑 N.7 验证。

**能力表 → 本课 / 数据流站点对照**（站点编号对应第 1 课那张图）：

| 编号 | 能力 | 顶层包 | 本课 | 数据流站点 |
| --- | --- | --- | --- | --- |
| ⓪ | 基础设施层 | `infrastructure/` | 第 0 课 | ①（地基，其余课的前提） |
| ① | 意图分类 | `services/classifier/` | 第 17 课 | ④ |
| ② | 记忆 | `services/memory/` | 第 18 课 | ③ |
| ③ | 检索 | `services/rag/` | 第 19 课 | ⑥（工具内部） |
| ④ | 工具 | `services/governance/tools_impl.py` | 第 20 课 | ⑥ |
| ⑤ | 治理 | `services/governance/` | 第 21 课 | ⑥ |
| ⑥ | 可观测 | `services/observability/` | 第 22 课 | ⑨（旁路） |
| ⑦ | 人机介入 | `services/agent/`（interrupt） | 第 23 课 | 跨站（图挂起/恢复） |
| ⑧ | 流式 | `services/streaming/` | 第 24 课 | ⑧ |
| — | 编排所有智能体 | `services/agent/` | 第 25 课 | ②（中枢） |

> 💡 读代码的总原则：**先找「入口函数」，再顺藤摸瓜**。每课的 N.4 都会第一行就告诉你入口在哪。
>
> 📌 **file:line 引用说明**：文中行号以**当前代码快照**为准，会随代码演进漂移。定位时**以函数/类名为锚**、行号仅作辅助——发现行号对不上时，先全局搜函数名，再顺藤摸瓜。

***

## 第 0 课 基础设施层（infrastructure）· 九段骨架的地基

> 🧱 **这一课是后面所有模块骨架能"跑起来"的前提**。它不在你给的 8 能力表内，但**没有它，第 17–25 课的九段骨架只是逻辑示意，无法组成可运行后端**。
> 读完本课，你拥有的 `get_settings() / 异步 engine+session / redis 连接池 / SQLAlchemy 模型` 会被后续每一段骨架直接 `import` 复用——这正是第 28 课"从零复现后端"的起点。
> 本课同样用八段式模板，但重点不是"算法"，而是**把分散的依赖收口成一个可注入、可降级、可测试的地基**。

### 0.1 问题与契约

- **输入**：`configs/settings.yaml` + `.env`（环境变量插值）、PostgreSQL 连接串、Redis URL。
- **输出**：① 统一配置读取 `get_settings()/get_value()`；② 异步数据库引擎与会话工厂 `get_engine()/get_session_factory()`；③ Redis 客户端 `get_redis()`；④ 声明式 ORM 模型（`Base` + `MemoryItem` 等，含 pgvector 向量列）；⑤ RBAC 策略引擎 `check()`；⑥ 审计落库 `write_audit()`（含合规截断）。
- **边界**：本层**不承载业务逻辑**；记忆/检索/工具等业务模块只消费它提供的"配置 + 连接 + 模型"，不直接读环境变量或裸建连接。

### 0.2 文件清单

| 文件 | 行数 | 职责 |
| --- | --- | --- |
| `config.py` | 103 | YAML + `${ENV}` 插值，全局单例 `get_settings()` / `get_value()` / `get_embedding_dim()` |
| `db.py` | 45 | SQLAlchemy 2.0 异步引擎 + `async_sessionmaker` 工厂 + `get_db()` 依赖注入 |
| `redis_client.py` | 24 | 进程内单例 Redis 客户端（限流/熔断/锁/缓存共用） |
| `paths.py` | — | `PROJECT_ROOT` / `CONFIG_DIR` 等路径常量 |
| `models/base.py` | 21 | `Base`（声明基类）+ `IdMixin` / `TimestampMixin` |
| `models/memory.py` | 26 | `MemoryItem`：`pgvector` 向量列 + 四层记忆统一表 |
| `models/{trace,knowledge,project,user,audit,skill}.py` | — | 其余表（调用链/知识库/项目/用户/审计/技能沉淀） |
| `rbac/policy.py` | 41 | YAML 驱动的 RBAC 引擎：`check()` / `check_tool_permission()` |
| `audit.py` | 87 | 审计落库 + 超限参数截断（哈希指纹 + 摘要，合规硬约束） |

### 0.3 核心数据结构

**① 配置 = 嵌套 dict（`config.py:56-86`）**：`_interpolate()` 把 YAML 里 `${VAR}` 替换成环境变量；`get_value("a","b",default=...)` 按路径取值。配置只读一份（`@lru_cache`），全项目同一视图。

**② 异步引擎 / 会话（`db.py:12-36`）**：`create_async_engine` 建异步引擎（`pool_pre_ping=True` 防断连）；`async_sessionmaker` 产 `AsyncSession`；`get_db()` 是 `async generator`，供 FastAPI `Depends` 注入。

**③ `MemoryItem`（`models/memory.py:12-25`）**——四层记忆共用一张表，靠 `kind` 区分：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `kind` | `String(32)` | `fact`/`summary`/`document`/`preference`/`user_doc` |
| `content` | `Text` | 原文 |
| `embedding` | `Vector(get_embedding_dim())` | **pgvector 列，维度跟随配置** |
| `importance` | `Float` | 召回排序权重（偏好固定 0.8） |
| `meta` | `JSON` | 来源/标题/分块号等溯源信息 |

> ⚠️ **坑**：`embedding` 维度由 `get_embedding_dim()` 在**定义类时**求值（`models/memory.py:22`）。切换嵌入底座导致维度变化时，必须重建 `memory_items` 表或迁数据（当前未引 Alembic）——这是"换 embedding 模型先重建索引"的底层原因。

**④ 审计净化（`audit.py:23-51`）**：`detail` 里超 200 字符的字符串 → `{fp: sha256前16位, sum: 前200字, len: 原文长}`。纯函数 `sanitize_detail()`，覆盖 HTTP/认证/工具三条入口，**合规硬约束**。

### 0.4 代码走读

**① 配置加载与插值（`config.py:39-61`）**——缺失环境变量即报错，不静默降级：

```python
_VAR_PATTERN = re.compile(r"\$\{([^}^{]+)\}")
def _interpolate(node):
    if isinstance(node, str):
        def _repl(m):
            val = os.environ.get(m.group(1).strip())
            if val is None:
                raise RuntimeError(f"配置所需环境变量缺失: {m.group(1)}")
            return val
        return _VAR_PATTERN.sub(_repl, node)
    ...  # dict/list 递归
@lru_cache
def get_settings() -> dict:
    return _interpolate(yaml.safe_load((PROJECT_ROOT/"configs/settings.yaml").read_text()))
```

**② 异步会话工厂（`db.py:12-36`）**——懒加载单例，避免导入期建连：

```python
def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_value("storage","postgres","async_dsn"), pool_pre_ping=True)
    return _engine
async def get_db():                       # FastAPI 依赖注入
    async with get_session_factory()() as s:
        yield s
```

**③ Redis 单例（`redis_client.py:9-16`）**——限流/熔断/锁全项目共用一个连接池：

```python
def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(get_value("storage","redis","url"), decode_responses=True)
    return _redis
```

**④ 模型声明（`models/base.py:8-20` + `models/memory.py:12-25`）**——Mapped 注解即"类型即列"：

```python
class Base(DeclarativeBase): pass
class MemoryItem(Base):
    __tablename__ = "memory_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    embedding = mapped_column(Vector(get_embedding_dim()))   # pgvector 向量列
```

**⑤ RBAC 引擎（`rbac/policy.py:19-41`）**——`denied` 优先于 `allowed`，支持 `*` 与前缀通配：

```python
def check(role, resource):
    rules = load_policy()["roles"].get(role, {})
    if any(_match(p, resource) for p in rules.get("denied", [])):
        return False
    return any(_match(p, resource) for p in rules.get("allowed", []))
def check_tool_permission(role, tool):   # 工具级权限：tool:xxx
    return check(role, f"tool:{tool}")
```

**⑥ 审计落库（`audit.py:53-71`）**——失败只记日志不阻断业务：

```python
async def write_audit(db, *, user_id, action, resource="", detail=None, ip=""):
    try:
        if detail is not None and not isinstance(detail, str):
            detail = json.loads(json.dumps(sanitize_detail(detail)))  # 合规截断
        db.add(AuditLog(...)); await db.commit()
    except Exception:
        logger.exception("审计写入失败"); await db.rollback()
```

### 0.5 调用关系

```
config.py  ← db.py / redis_client.py / models/* / rbac / audit / 所有业务模块
db.py      ← api 层 Depends(get_db) / 业务模块的会话
redis_client.py ← governance 限流·熔断·锁 / 记忆短期缓存
models/*   ← 所有读写 PG 的模块
rbac/policy.py ← api 中间件 / governance 工具注册中心(check_tool_permission)
audit.py   ← api 认证 / 工具治理（被拒也要写）
```

> 全项目只有这一层直接碰"环境变量 / 连接串 / 向量类型"。**后续 17–25 课每段骨架只要 `from infrastructure.config import get_value` 等即可，不必重复收口。**

### 0.6 最小可复现骨架

> 本骨架等价于 `infrastructure/` 真实实现（精简可读版）。**后续 17–25 课的 N.6 直接复用它**——这就是"九段骨架 + 本层 = 可运行后端"的含义。
> 前置：`pip install sqlalchemy[asyncio] asyncpg pgvector redis pyyaml`；`configs/settings.yaml` + `.env` 已配 PG/Redis。

```python
# 最小可复现：基础设施层（≈80 行，等价于 infrastructure/ 真实实现）
import os, re, json, yaml, redis.asyncio as aioredis
from functools import lru_cache
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Float
from pgvector.sqlalchemy import Vector

ROOT = Path(__file__).resolve().parent
_VAR = re.compile(r"\$\{([^}^{]+)\}")

# ---- ① 配置：YAML + 环境变量插值，全局单例 ----
@lru_cache
def get_settings() -> dict:
    raw = yaml.safe_load((ROOT/"configs/settings.yaml").read_text(encoding="utf-8"))
    def _it(n):
        if isinstance(n, str):
            return _VAR.sub(lambda m: os.environ[m.group(1)], n)
        if isinstance(n, dict): return {k:_it(v) for k,v in n.items()}
        if isinstance(n, list): return [_it(v) for v in n]
        return n
    return _it(raw)
def get_value(*keys, default=None):
    n = get_settings()
    for k in keys:
        if not isinstance(n, dict) or k not in n: return default
        n = n[k]
    return n
def get_embedding_dim() -> int:
    ps = get_value("llm","providers") or {}
    name = get_value("llm","embedding_provider") or get_value("llm","default_provider")
    return int((ps.get(name) or {}).get("embedding_dim") or 0)

# ---- ② 数据库：异步引擎 + 会话工厂 ----
_engine=None; _factory=None
def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_value("storage","postgres","async_dsn"), pool_pre_ping=True)
    return _engine
def get_session_factory():
    global _factory
    if _factory is None: _factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _factory

# ---- ③ Redis 单例 ----
_redis=None
def get_redis():
    global _redis
    if _redis is None: _redis = aioredis.from_url(get_value("storage","redis","url"), decode_responses=True)
    return _redis

# ---- ④ 模型：Base + pgvector 向量列 ----
class Base(DeclarativeBase): pass
class MemoryItem(Base):
    __tablename__ = "memory_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    content: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(get_embedding_dim()))
    importance: Mapped[float] = mapped_column(default=0.5)
```

### 0.7 验证与预期输出

```powershell
# 1) 配置层真的能读（预期：打印 settings 顶层键，如 llm/storage/app/rag/...）
envs\lunjiang\python.exe -c "from infrastructure.config import get_settings; print(list(get_settings()))"
# 2) 引擎能建（预期：无异常，返回 AsyncEngine）
envs\lunjiang\python.exe -c "from infrastructure.db import get_engine; print(type(get_engine()).__name__)"
# 3) Redis 能连（预期：True）
envs\lunjiang\python.exe -c "import asyncio, infrastructure.redis_client as r; print(asyncio.run(r.get_redis().ping()))"
```

> 以上为**真实可跑**命令（结构示意，具体键名取决于你的 settings.yaml）。三项全绿 = 地基就绪，可进入第 17 课。

**→ 主动练习（改一行看变化）**：把 `configs/settings.yaml` 里某个 `${VAR}` 故意写错（如 `${NOPE}`），重跑第 1 条——观察是否抛出 `配置所需环境变量缺失: NOPE`。这印证了"缺失即报错、不静默降级"的设计。

### 0.8 面试点与坑

- **pgvector 维度绑定**：`Vector(get_embedding_dim())` 在类定义时定值；换嵌入底座维度变了必须重建表——这是"改 embedding 先重建索引"的底层原因。
- **异步依赖注入**：`get_db()` 必须是 `async generator` 且返回 `AsyncIterator`，否则 FastAPI `Depends` 注入的会话会在请求结束前被关掉。
- **RBAC 优先级**：`denied` 命中即拒，再判 `allowed`；`tool:xxx` 是工具级资源的命名约定。
- **审计合规**：`_sanitize_value`（`audit.py:23-40`）对超长字符串只存指纹+摘要，覆盖三条入口，避免论文全文进日志。
- **连接单例**：engine/redis 都是懒加载进程内单例，测试里要 `dispose_engine()/close_redis()` 才能干净退出。

***

## 第 17 课 意图分类（classifier）

> 🔗 复习锚点：第 9 课讲过「为什么需要意图分类 + 三级兜底」的**动机**，本课讲这段代码**怎么写**——两遍是递进，不是重复。

### 17.1 问题与契约

| 项 | 内容 |
| --- | --- |
| 输入 | 一句用户自然语言（`str`） |
| 输出 | `IntentResult(intent, confidence, layer)` |
| 硬约束 1 | 高频、带明显关键词的指令要 **0 token、毫秒级**返回 |
| 硬约束 2 | **永不失败**——三层全挂也必须返回一个类别，绝不能让请求 500 |
| 调用时机 | 每次对话的首个节点（supervisor 首次进入） |

一句话概括设计思想：**让便宜的判定挡在前面，贵的 LLM 只处理剩下的**。

### 17.2 文件清单

整个包只有一个文件，132 行，是全项目最适合"第一次读源码"的入口：

| 文件 | 行数 | 职责 |
| --- | --- | --- |
| `services/classifier/intent.py` | 132 | 三层分类器全部逻辑 + 模块级单例 |

### 17.3 核心数据结构

**`IntentResult`**（`intent.py:37-41`）——模块唯一的输出：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `intent` | `str` | 7 类意图之一（见下） |
| `confidence` | `float` | 0~1 置信度。**注意：只用于可观测与调试，不参与路由决策** |
| `layer` | `str` | `rule` / `vector` / `llm`，用来统计"多少请求省下了 LLM" |

**7 类意图**（`intent.py:16-23`）：`topic_analysis` 选题分析、`literature_search` 文献检索、`writing` 论文写作、`format_check` 格式校验、`plagiarism_reduce` 查重降重、`ai_detect` AI 检测、`chitchat` 闲聊/其他。

**L1 规则表**（`intent.py:26-34`）——7 条正则，**顺序敏感**：

| 顺序 | 意图 | 触发示例 |
| --- | --- | --- |
| 1 | `format_check` | 格式、排版、目录、页码、字体 + 检查/校验/规范 |
| 2 | `literature_search` | 找/查/检索/搜 + 文献/论文/资料、参考文献、文献综述 |
| 3 | `plagiarism_reduce` | 查重、重复率、降重、抄袭 |
| 4 | `ai_detect` | AI 检测、AI 率、AI 味、降 AI |
| 5 | `topic_analysis` | 选题/题目/方向 + 分析/推荐/确定、开题 |
| 6 | `writing` | 写/扩写/润色/修改/大纲/提纲（后三组均可省略，命中率很高） |
| 7 | `chitchat` | 整句仅为「你好 / 谢谢 / 在吗」等问候 |

### 17.4 代码走读

**入口：`classify()` — `intent.py:64-75`**。整个函数只有 11 行，就是一个三级瀑布：

```python
async def classify(self, text: str) -> IntentResult:
    text = text.strip()
    # L1 规则
    for intent, pattern in _RULES:                      # L67-69
        if pattern.search(text):
            return IntentResult(intent, 0.95, "rule")   # 命中即返回，0 token
    # L2 向量原型相似
    result = await self._vector_layer(text)             # L71
    if result and result.confidence >= 0.62:            # L72 阈值
        return result
    # L3 LLM 兜底
    return await self._llm_layer(text)                  # L75
```

三层各自的细节：

- **L1 规则层**（L67-69）：`re.search` 而非 `match`，命中即 `return`。置信度**硬编码 0.95**（不是算出来的），因为关键词命中的可信度本来就高。
- **L2 向量层**（`_vector_layer` L92-106）：
  1. `_ensure_prototypes()`（L78-84）**懒加载**：首次调用才把 24 句原型句 `embed` 成向量，之后缓存在 `self._proto_vecs` 里，**永不失效**；
  2. 待分类文本 embed → 与每个意图的原型句逐一算余弦，取 `max`（L99，"与该类最像的那句"代表该类）；
  3. 余弦值直接当置信度（L103，clamp 到 0~1），**≥0.62 才采信**，否则继续下沉到 L3；
  4. 整层包在 `try/except` 里，异常时 `return None` → 自动落到 L3。
- **L3 LLM 兜底**（`_llm_layer` L109-129）：`json_mode=True`、`temperature=0.0`、`max_tokens=64`（三个参数都是为了"稳定且便宜"）；拿到的 `intent` 若不在 7 类白名单内 → 强制 `chitchat`（L124-125）；**连异常都兜住**（L127-129）返回 `chitchat/0.3/llm`。

> 这就是为什么说它"永不失败"：**三层的每一层都有兜底，最坏情况是返回 chitchat，而不是抛异常**。

### 17.5 调用关系

```
上游：services/agent/supervisor.py:40   supervisor_node 首次进入时调用
        │
        ▼
  intent_classifier.classify(text)
        │
        ├── L1 无依赖（纯正则）
        ├── L2 → LLMProvider.embed()    （本地 bge-m3，见第 6 课）
        └── L3 → LLMProvider.chat(json_mode=True)
```

模块底部 `intent.py:132` 直接实例化了单例 `intent_classifier`，全项目共享（因此原型向量只算一次）。

### 17.6 最小可复现骨架

把配置读取、日志、单例都剥掉，本模块的核心就是下面这些。**自己敲一遍即可跑通**：

```python
# 最小可复现：三层意图分类器（≈50 行）
import re
from dataclasses import dataclass

INTENTS = ["topic_analysis", "literature_search", "writing",
           "format_check", "plagiarism_reduce", "ai_detect", "chitchat"]

RULES = [                                    # ① 顺序敏感：更具体的模式排前面
    ("format_check", re.compile(r"(格式|排版|目录|页码|字体).*(检查|校验|规范|对|错)")),
    ("literature_search", re.compile(r"(找|查|检索|搜)(一些|几篇|相关)?(文献|论文|资料)|参考文献")),
    ("plagiarism_reduce", re.compile(r"(查重|重复率|降重|抄袭)")),
    ("ai_detect", re.compile(r"(AI(检测|率|痕迹|味)|降AI)")),
    ("topic_analysis", re.compile(r"(选题|题目|方向).*(分析|推荐|确定|纠结)|开题")),
    ("writing", re.compile(r"(写|扩写|续写|润色|修改)|大纲|提纲")),
    ("chitchat", re.compile(r"^(你好|您好|hi|hello|在吗|谢谢)[!！。~\s]*$", re.I)),
]
PROTOTYPES = {                               # ② 每类 3~4 句"原型句"作为向量锚点
    "topic_analysis": ["帮我确定毕业论文选题方向", "这个研究题目可行吗", "开题报告题目怎么定"],
    "literature_search": ["帮我检索相关领域文献", "找几篇核心期刊论文", "这个主题有哪些参考文献"],
    "writing": ["帮我写论文摘要", "扩写这一段正文", "润色这段话的表达", "生成论文大纲"],
    "format_check": ["检查我的论文格式是否规范", "参考文献格式对不对", "目录页码符合要求吗"],
    "plagiarism_reduce": ["这段话重复率太高帮我降重", "改写句子避免查重", "同义替换这段内容"],
    "ai_detect": ["检测这段文字的AI痕迹", "AI率会不会很高", "帮我降低AI味"],
    "chitchat": ["你好呀", "你能做什么", "谢谢帮助"],
}

@dataclass
class IntentResult:
    intent: str
    confidence: float
    layer: str                               # rule / vector / llm


def _cos(a, b):
    na, nb = sum(x * x for x in a) ** 0.5, sum(x * x for x in b) ** 0.5
    return sum(x * y for x, y in zip(a, b)) / (na * nb or 1)


class IntentClassifier:
    def __init__(self, embed_fn, chat_fn):
        self.embed, self.chat = embed_fn, chat_fn     # ③ 底座注入，便于单测
        self._proto_vecs = None                       # ④ 懒加载 + 进程内缓存

    async def _ensure_prototypes(self):
        if self._proto_vecs is None:
            flat = [(i, s) for i, ss in PROTOTYPES.items() for s in ss]
            vecs = await self.embed([s for _, s in flat])
            self._proto_vecs = {}
            for (intent, _), v in zip(flat, vecs):
                self._proto_vecs.setdefault(intent, []).append(v)

    async def classify(self, text: str) -> IntentResult:
        text = text.strip()
        # L1 规则层：0 token、毫秒级，命中即返回
        for intent, pattern in RULES:
            if pattern.search(text):
                return IntentResult(intent, 0.95, "rule")
        # L2 向量层：与原型句比余弦，取每类最高分，≥0.62 才采信
        try:
            await self._ensure_prototypes()
            q = (await self.embed([text]))[0]
            best = max(((i, max(_cos(q, v) for v in vs))
                        for i, vs in self._proto_vecs.items()), key=lambda x: x[1])
            if best[1] >= 0.62:
                return IntentResult(best[0], min(1.0, max(0.0, best[1])), "vector")
        except Exception:
            pass                                      # ⑤ 异常不抛，下沉到 L3
        return await self._llm(text)

    async def _llm(self, text: str) -> IntentResult:
        # L3 LLM 兜底：json_mode + temperature=0 + max_tokens=64 求稳求省
        try:
            data = await self.chat([{"role": "user", "content":
                f"分类到 {INTENTS} 之一，只输出 JSON {{\"intent\":\"...\",\"confidence\":0.xx}}: {text}"}],
                json_mode=True, temperature=0.0, max_tokens=64)
            intent = data.get("intent", "chitchat")
            return IntentResult(intent if intent in INTENTS else "chitchat",
                                float(data.get("confidence", 0.5)), "llm")
        except Exception:
            return IntentResult("chitchat", 0.3, "llm")   # ⑥ 最坏情况也不抛异常
```

**复现要点（缺一不可）**：① 规则表顺序敏感；② 原型句每类 3~4 句；③ 底座用函数注入方便单测；
④ 原型向量懒加载且**只算一次**；⑤ ⑥ 任何一层失败都要向下沉，**整个分类器不允许抛异常**。

### 17.7 验证与预期输出

下面三条都是 **L1 规则层命中**，不需要 LLM 和向量服务，可离线验证：

```powershell
envs\lunjiang\python.exe -c "
import asyncio
from services.classifier.intent import intent_classifier as c
async def main():
    for t in ['参考文献格式对不对', '帮我给这段话降重', '你好']:
        r = await c.classify(t)
        print(f'{t!r:24} -> intent={r.intent:20} conf={r.confidence} layer={r.layer}')
asyncio.run(main())
"
```

预期输出（三行 `layer=rule` 即证明**这一轮分类 0 token**）：

```
'参考文献格式对不对'    -> intent=format_check        conf=0.95 layer=rule
'帮我给这段话降重'      -> intent=plagiarism_reduce  conf=0.95 layer=rule
'你好'                  -> intent=chitchat           conf=0.95 layer=rule
```

> 第一条最能说明问题：「参考文献格式对不对」同时命中 `literature_search`（含"参考文献"）和 `format_check`（含"格式…对"），**因为 format_check 在 `_RULES` 里排第 1，所以判为 format_check**。

**→ 主动练习（改一行看变化）**：往 classifier 的规则词典里加一条你自己的关键词（或调低向量层触发阈值），重跑 17.7 的三类样本——观察某条问句从 vector 层落到 rule 层命中，`intent_layer` 字段随之变化。

### 17.8 面试点与坑

| 点 | 说明 |
| --- | --- |
| 面试点：为什么分三层 | 请求分布是"少量高频模板 + 长尾口语"。规则层吃掉高频（0 成本），向量层吃近义改写（低成本），只有真正长尾才付 LLM 的钱。这是**成本分层**的典型范式。 |
| 面试点：confidence 不参与决策 | 只有 L2 的 0.62 阈值真正影响路由；L1 的 0.95 与 L3 的置信度都只是可观测数据。**不要说"用置信度做路由"**，会被追问。 |
| 坑：原型向量缓存永不失效 | 改了 `_prototypes` 里的句子必须**重启进程**才生效。 |
| 坑：writing 规则极宽 | `writing` 正则的后三组全是可选 `?`，句中出现「写/扩写/润色/修改/大纲/提纲」任一即命中。所以**真正决定分流的是排在它前面的 5 条规则**，调顺序会直接改变分类结果。 |
| 坑：0.62 是经验值 | 不同 embedding 模型（bge-m3 vs 云端）的余弦分布不同，换底座后这个阈值应重新标定。 |

***

## 第 18 课 记忆体系（memory）

> 🔗 复习锚点：第 7 课讲过「四层记忆为什么存在」，本课讲四层**各自怎么落库、怎么召回、怎么压缩**。

### 18.1 问题与契约

第 7 课讲了"为什么分四层"，这里给出**可核对的契约表**：

| 层 | 文件 | 生命周期 | 存储 | 写入时机 | 读取时机 | 失败影响 |
| --- | --- | --- | --- | --- | --- | --- |
| L1 短期对话 | `short_term.py` | 最近 N 轮，**TTL 7 天** | Redis List | 对话前后各一次（`conversation_service.py:73/87`） | 每轮组装上下文（`engine.py:131`） | 降级为空历史 |
| L2 项目结构化 | `structured.py` | 跟随项目 | PG `projects.structured_memory`（JSON 列） | 决策归档时（`conversation_service.py:57`） | 同上（`engine.py:143`） | 降级为空 brief |
| L3 长期向量 | `long_term.py` | 永久 | PG `memory_items` 表 + pgvector | 压缩归档 / 决策归档 | 每轮按语义召回 top3（`engine.py:149`） | 跳过 |
| L4 用户偏好 | `preference.py` | 永久 | PG `memory_items`（`kind="preference"`） | 命中触发词时（`conversation_service.py:94`） | 每轮 top5（`engine.py:157`） | 跳过 |

> ⚠️ **变更标注（2026-09-02）**：旧版文档称短期记忆「TTL 30 天」，与实现不符。实际为 `expire(key, 7 * 24 * 3600)`，即 **7 天**（`services/memory/short_term.py:19`）。

### 18.2 文件清单

| 文件 | 行数 | 职责 |
| --- | --- | --- |
| `short_term.py` | 45 | Redis List 读写 + 窗口裁剪 + 逐出 |
| `structured.py` | 46 | 项目结构化记忆（4 个 section）+ 渲染成提示词摘要 |
| `long_term.py` | 85 | pgvector 写入与「距离×重要度」加权召回 |
| `preference.py` | 39 | 偏好条目写入与按重要度召回 |
| `compressor.py` | 158 | 四级压缩流水线 + 窗口维护入口 |

### 18.3 核心数据结构

**Redis 里的短期记忆**（`short_term.py:8-18`）：

```
key     = "chat:{project_id}:{session_id}"      # 注意：没有 "lunjiang:" 前缀
value   = List，每个元素是一条 JSON：
          {"role": "user"|"assistant", "content": "...", "ts": 1712345678.0}
裁剪     = ltrim(key, -max_turns*2, -1)          # 每轮 user+assistant 两条，故 ×2
TTL      = 7 天（每次 append 都续期）
```

> ⚠️ **变更标注（2026-09-02）**：旧版文档写作 `lunjiang:chat:{project}:{session}`，实际 key 为 `chat:{project_id}:{session_id}`，无 `lunjiang:` 前缀。

**项目结构化记忆的 4 个 section**（`structured.py:6-11`）：

| section | 类型 | 存什么 |
| --- | --- | --- |
| `topic` | `dict` | 选题结论：`{"title": ..., "rationale": ...}` |
| `outline` | `list` | 论文章节大纲 |
| `facts` | `list` | 关键约束（字数、格式要求等） |
| `progress` | `dict` | 各章节完成状态 |

`get()`（L15-21）用 `dict(DEFAULT)` 打底再 `update`，**保证永远返回全部 4 个 key**，调用方不用做 `.get(..., [])`。

**`MemoryItem` 的 `kind` 枚举**（全项目共用一张表，靠 `kind` 区分域，见 `infrastructure/models/memory.py`）：

| kind | 谁写 | 谁读 |
| --- | --- | --- |
| `document` | 公共语料入库（`rag/ingest/corpus_loader.py`） | RAG 稠密路 + BM25 |
| `user_doc` | 项目知识库入库（`rag/ingest/pipeline.py`） | RAG 项目路 |
| `summary` | 上下文压缩归档（`compressor.py:150`） | L3 长期召回 |
| `decision` | 人机介入决策归档（`conversation_service.py:52`） | L3 长期召回 |
| `fact` | 事实沉淀 | RAG 稠密路 |
| `preference` | L4 偏好（`preference.py:24`） | 偏好召回 |

### 18.4 代码走读

**① 短期记忆写入 — `short_term.py:12-19`**（入口 `append`）：

```python
await r.rpush(key, json.dumps({...}))        # L16  追加一条
await r.ltrim(key, -max_turns * 2, -1)       # L18  只留最近 max_turns 轮（×2 条）
await r.expire(key, 7 * 24 * 3600)           # L19  TTL 7 天
```

三步合成一次调用，靠 Redis 单线程语义天然原子。`max_turns` 取自配置 `memory.short_term_max_turns`（默认 20 → 保留 40 条）。

**② 上下文压缩 — `compressor.py:68-122`**（入口 `ContextCompressor.compress`）。四级流水线：

```
L76  第 0 级：体积 ≤ memory.compress_trigger_tokens（默认 3000）→ 直接原样返回，不压缩
L82  第 1 级 分级留存：命中 _HIGH_VALUE_MARKERS（纠正/不对/改成/记住/重要/必须/要求）的消息全保留
L86  第 2 级 冗余去重：_dedup 按「去掉所有非文字字符后的内容」判重，合并相邻重复
L89  第 3 级 窗口截断：rest 只留最近 keep_recent 条，其余进 evicted
L98  第 4 级 LLM 摘要：把 evicted 最后 12 条压成 ≤400 token 摘要
L112 重排输出顺序：[历史摘要] → 高价值消息 → 近期窗口   ← 这个顺序是有讲究的
```

**为什么摘要放最前？** LLM 对系统位置的指令敏感度最高，把"历史结论"放在最前面，后续消息就不会把它挤掉。

降级也写得很实（L107-109）：LLM 摘要失败 → 退化成「首条前 150 字 + ……（后续已截断）」的**截断式保留**，宁可丢信息也不崩。

**③ 长期记忆加权召回 — `long_term.py:16-34`**（本模块最值得讲的一段）：

```python
# min-max 归一后混合排序，纯函数便于单测
score = alpha * (1 - (d - d_min) / span) + (1 - alpha) * importance
#       └── 语义距离分（越小越像 → 归一后越大）      └── 重要度
# alpha 默认 0.7（配置 memory.recall_semantic_weight）
```

`recall()`（L57-78）的关键细节：

1. 先按 `cosine_distance` 排序取 `top_k * 2` 个候选（L65），再在候选集内混合重排（L78）——**先粗筛再精排**，避免全表扫；
2. 作用域过滤是「本项目 + 全局」并集：`project_id == pid OR project_id IS NULL`（L67-68），用户维度同理；
3. L74 那行注释是实战经验：必须用 `.all()` 而不是 `.scalars()`，否则拿不到距离列。

### 18.5 调用关系

```
写入侧（services/agent/conversation_service.py）
  stream_chat  → short_term.append(user)          L73
               → stream 结束后 short_term.append(assistant)   L87
               → _fire(_compress_window)           L93   后台压缩
               → _fire(_learn_preference)          L95   命中触发词才写
  stream_resume→ _fire(_archive_decision)          L122  写 long_term(kind=decision) + structured.topic

读取侧（services/agent/engine.py:_assemble_memory  L123-163）
  L1 short_term.history()  → history_text（取最后 8 条）
  L2 structured.get+render_brief → memory_brief
  L3 long_term.recall_text(kinds=["summary","decision","fact"], top_k=3)
  L4 preference.recall(top_k=5)
  ⚠️ 每一层都包在 try/except 里，失败只 warning 不中断（L135 / L160）
```

### 18.6 最小可复现骨架

四层记忆的代码量很大，但**真正的核心只有三块**：短期窗口、四级压缩、加权召回。下面把这三块压成 ~70 行：

```python
# 最小可复现：四层记忆核心（≈70 行，省略配置读取与降级）
import json, re, time
import redis.asyncio as aioredis

KEY = "chat:{pid}:{sid}"                    # 注意：无 lunjiang: 前缀
HIGH_VALUE = ("纠正", "不对", "改成", "记住", "重要", "必须", "要求")


class ShortTerm:                            # ---------- L1 短期对话（Redis List）
    def __init__(self, url):
        self.r = aioredis.from_url(url, decode_responses=True)

    async def append(self, pid, sid, role, content, max_turns=20, ttl=7 * 24 * 3600):
        k = KEY.format(pid=pid, sid=sid)
        await self.r.rpush(k, json.dumps({"role": role, "content": content, "ts": time.time()}))
        await self.r.ltrim(k, -max_turns * 2, -1)      # 每轮 user+assistant 两条 → ×2
        await self.r.expire(k, ttl)                    # TTL 7 天，每次写入续期

    async def history(self, pid, sid, last_n=20):
        raw = await self.r.lrange(KEY.format(pid=pid, sid=sid), 0, -1)
        return [json.loads(x) for x in raw][-last_n * 2:]


def dedup(msgs):                            # ---------- 压缩第 2 级：归一化判重
    seen, out = set(), []
    for m in msgs:
        key = re.sub(r"[\s\W_]+", "", m.get("content", ""))   # 去掉标点空格后比较
        if key and key in seen:
            continue
        seen.add(key)
        out.append(m)
    return out


async def compress(messages, keep_recent, summarize_fn, trigger=3000):
    """四级压缩：第0级达标不压 → 第1级分级留存 → 第2级去重 → 第3级截断 → 第4级摘要"""
    original = sum(len(m.get("content", "")) for m in messages)
    if original <= trigger:                                    # 第 0 级
        return messages, "", 1.0
    high = [m for m in messages
            if any(k in m.get("content", "") for k in HIGH_VALUE)]   # 第 1 级
    rest = dedup([m for m in messages if m not in high])             # 第 2 级
    evicted, kept = (rest[:-keep_recent], rest[-keep_recent:]) if keep_recent else (rest, [])  # 第 3 级
    summary = await summarize_fn(evicted[-12:]) if evicted else ""   # 第 4 级
    out = ([{"role": "system", "content": f"[历史摘要] {summary}"}] if summary else []) \
        + high + kept                       # ← 顺序有讲究：摘要 → 高价值 → 近期窗口
    return out, summary, sum(len(m["content"]) for m in out) / max(1, original)


def hybrid_rank(rows_dists, alpha=0.7, top_k=5):
    """L3 召回：语义距离 × 重要度 加权（先 min-max 归一，再线性混合）"""
    rows = [(r, d) for r, d in rows_dists if isinstance(d, (int, float))]
    if not rows:
        return []
    d = [x[1] for x in rows]
    lo, hi = min(d), max(d)
    span = (hi - lo) or 1.0
    scored = [(alpha * (1 - (dist - lo) / span) + (1 - alpha) * float(r.importance or 0.5), r)
              for r, dist in rows]          #         ↑ 距离越小越像 → 归一后越大
    return [r for _, r in sorted(scored, key=lambda x: x[0], reverse=True)[:top_k]]


DEFAULT_STRUCTURED = {"topic": {}, "outline": [], "facts": [], "progress": {}}   # L2 项目结构化

# L4 偏好：就是 kind="preference" 的 MemoryItem，importance 固定 0.8，
#        召回时 ORDER BY importance DESC, id DESC LIMIT top_k —— 不参与语义计算
```

**复现要点**：① `ltrim(-2N, -1)` 保证只留最近 N 轮；② 压缩的**顺序**不能变（先保高价值再抽象）；
③ `hybrid_rank` 的 α 默认 0.7，语义主导、重要度兜底；④ L2 永远用 `dict(DEFAULT)` 打底再 `update`，
保证 4 个 section 齐全。

### 18.7 验证与预期输出

```powershell
envs\lunjiang\python.exe scripts/smoke_memory.py    # 四层 + 压缩全自检
```

单独验证压缩比（无需数据库，纯函数级）：

```powershell
envs\lunjiang\python.exe -c "
import asyncio
from services.memory.compressor import context_compressor
msgs = [{'role':'user','content':f'第{i}轮：帮我看看这一段怎么写 '+ '内容'*30} for i in range(20)]
r = asyncio.run(context_compressor.compress(msgs, keep_recent=0, force=True))
print(f'原始 {r.original_chars} 字 -> 压缩后 {r.compressed_chars} 字, ratio={r.ratio:.2f}')
print('摘要前 80 字:', r.summary[:80])
"
```

预期：`ratio` 显著小于 0.30（目标值），且 `original_chars` 远大于 `compressed_chars`。

**→ 主动练习（改一行看变化）**：把 `memory.recall_semantic_weight`（alpha，默认 0.7）改成 0.3，重跑 18.7 召回——准备一对"语义相近但重要度低"与"语义一般但重要度高"的候选，观察两者排序互换，体会 alpha 在调和什么。

### 18.8 面试点与坑

| 点 | 说明 |
| --- | --- |
| 面试点：四级压缩的顺序 | 留存 → 去重 → 截断 → 摘要。**先保住高价值信息再抽象**，反过来做会把关键纠正语一起压掉。 |
| 面试点：为什么 L3 用「距离×重要度」而不是纯向量 | 纯向量会让"语义最像但一次性的闲聊"顶掉"语义稍远但用户反复强调的结论"。`hybrid_rank` 用 α=0.7 让语义主导、重要度兜底（ROUND13 修复点）。 |
| 坑：`compress_trigger_tokens` 名不副实 | 名字叫 token，**实际比的是字符数**（`compressor.py:72/76/135`）。没有接 tokenizer，是刻意简化。 |
| 坑：`project_id=None` 时读写 key 不一致 | 写入侧 `conversation_service.py:70` 用 `pid = project_id or 0` → key `chat:0:{sid}`；读取侧 `engine.py:131` 直接用原始 `project_id` → key `chat:None:{sid}`。**不带项目发对话时历史读不到**。这是真实存在的不一致，排查"记忆没生效"时优先看这里。 |
| 坑：记忆层失败是静默的 | `engine.py:135/160` 只 `logger.warning`，前端完全无感。验证记忆是否生效要看日志里的 `短期记忆不可用` / `DB 记忆层不可用`。 |

***

## 第 19 课 检索 rag

> 🔗 复习锚点：第 8 课讲过「三阶段 RAG 为什么比直接搜好」，本课把改写→召回→精排**逐函数拆开**（含 ⑤ 入库写路径）。

### 19.1 问题与契约

| 项 | 内容 |
| --- | --- |
| 输入 | `query: str`、`top_k: int`、`project_id: int \| None`、`rewrite_mode: "on"\|"auto"\|"off"` |
| 输出 | `{"rewritten": str, "keywords": list[str], "results": [候选块...]}` |
| 质量指标 | Recall@5 ≥ 0.90（普通集）；长尾口语集 ≥ 0.96（见第 14 课） |
| 关键约束 | ① 精排是 CPU 阻塞，**绝不能跑在事件循环线程上**；② 改写器失效时必须回退，不能让召回归零 |

入口函数：**`RagPipeline.search()` — `services/rag/pipeline.py:64`**。

### 19.2 文件清单

| 文件 | 行数 | 职责 |
| --- | --- | --- |
| `pipeline.py` | 151 | **主入口**：S1 改写 / S2 多路融合 / S3 精排降噪，三段串起来 |
| `query_rewrite.py` | 193 | S1：LLM 改写 + 规则兜底 + jieba 关键词 + 难度自适应 |
| `retriever.py` | 173 | S2：稠密 / 稀疏 / 项目 / 相邻窗口 四路召回 + RRF 融合 |
| `reranker.py` | 82 | S3：bge-reranker 交叉编码器（**线程池执行**） |
| `ingest/corpus_loader.py` | 89 | 公共语料 `data/corpus/*.txt` → 分块 → 向量化入库 |
| `ingest/parsers.py` | 163 | PDF/DOCX/TXT/MD 解析器工厂（扫描件拒绝） |
| `ingest/pipeline.py` | 193 | 项目知识库：上传 → 去重 → 解析 → 分块 → 批量向量化 |

### 19.3 核心数据结构

**候选块（chunk）在流水线中字段逐步"加厚"**，理解这张表就理解了整条链路：

| 阶段 | 新增字段 | 含义 |
| --- | --- | --- |
| 稠密路产出 | `dense_score` | pgvector 余弦相似度 |
| 稀疏路产出 | `sparse_score` | BM25 分数（未归一） |
| 相邻窗口产出 | `sibling_score` | 邻块标记 |
| **RRF 融合后** | `rrf_score` | 多路排名融合分（**唯一跨路可比分**） |
| 降噪后 | `rerank_boost`、`noise_flag` | 噪声惩罚系数、噪声类型 |
| 精排后 | `rerank_score` | 交叉编码器分 × boost，**最终排序依据** |

`noise_flag` 三态（`pipeline.py:39-60`）：

| 值 | 判定 | 惩罚 |
| --- | --- | --- |
| `ok` | 稠密路命中且排名靠前（前 35%） | ×1.0 |
| `weak` | 稠密路命中但排名靠后 | ×0.995 |
| `sparse_only` | **稠密路完全没命中**，只有 BM25 命中（关键词重叠噪声） | ×0.982 |

### 19.4 代码走读

**S1 改写（`pipeline.py:84-88`）**：

```python
if use_rewrite and get_value("rag", "rewrite_enabled", default=True):
    rw = await rewrite_query(query, mode=rewrite_mode)
    rewritten, keywords = rw["rewritten"], rw["keywords"]
    if _is_rejection(rewritten):        # 拒答/空泛 → 直接回原查询
        rewritten = query
```

改写器内部的四道防线（`query_rewrite.py:154-194`）是**第 1 轮 A/B 实验的核心产出**，务必逐条看懂：

| 防线 | 位置 | 触发条件 | 动作 |
| --- | --- | --- | --- |
| 难度自适应 | `L166-169` | `mode=auto` 且 `is_rewrite_worthwhile()` 判为简单短句 | 跳过 LLM，`strategy="skip"`（零开销） |
| 拒答检测 | `L182-185` | 输出过短（<8 字）或前 60 字含"无法/无关/抱歉/不能/不适合" | 回退规则改写 |
| 漂移检测 | `L186-189` | 字符重合度 `< 0.15` | 回退规则改写 |
| 异常兜底 | `L192-194` | 任何异常 | 回退规则改写 |

> 关键在于：**失效时回退到「规则字典改写」而不是「原始查询」**。早期版本直接回原查询，召回增益归零；改成规则回退后 Recall@5 才恢复 100%。

`is_rewrite_worthwhile()`（`L137-151`）的判定逻辑（零 LLM）：命中口语化词表（"咋/啥/怎么破/心里慌"）→ 长尾，值得改写；短句（≤40 字）且无口语信号 → 简单，跳过；其余长句 → 保守走 LLM。

**S2 多路召回（`pipeline.py:92-130`）**，一共最多 6 路：

```
① dense(改写后查询)            公共语料稠密        retriever.py:33
② sparse(改写后查询)           BM25 关键词         retriever.py:94
③ sparse(keywords[0])          改写关键词补一路    pipeline.py:97   （术语覆盖）
④ dense(原始查询)              仅当改写生效时      pipeline.py:99   ← 防漂移锚点
⑤ project_dense_search()       项目私有知识库      pipeline.py:106
⑥ sibling_search()             命中块 ±1 邻块     pipeline.py:115  ← 第三引擎
        └── 全部经 RRF 融合 ──┘
```

`rrf_fuse()`（`retriever.py:159-170`）的公式就一行：

```python
rrf = 1.0 / (k + rank + 1)     # k=60，rank 从 0 开始
```

**为什么用 RRF 而不是分数归一？** 稠密的余弦在 0~1、BM25 分数可以上到 20+，两者量纲不可比；RRF 只用**排名**，天然免疫量纲问题，且实现只有 8 行。代价是丢掉了分数信息——所以后面必须有 S3 精排补回精度。

**S3 精排（`pipeline.py:133-143`）** 两个动作：① 打降噪 boost；② `reranker.rerank(query, fused, alt_query=rewritten)`——**主查询和改写查询各打一次分，取 max**（`reranker.py:50-53`），这样"改写万一漂移了"也不会拖累结果。

**⑤ 入库写路径（ingest/）——RAG 的另一半**：19.4 讲的是"文档怎么被查出来"，这里讲"文档怎么进去"。两条链路共用 `chunk_text` 与 `MemoryItem`，保证分块口径一致。

- **公共语料**（`corpus_loader.ingest_corpus`，`ingest/pipeline.py` 调用）：读 `data/corpus/*.txt` → `chunk_text` 分块 → `provider.embed` 批量向量化写 `MemoryItem(kind="document")` → 末了 `hybrid_retriever.rebuild_bm25()` 重建稀疏索引。
- **项目知识库**（`ingest/pipeline.ingest_document`，`ingest/pipeline.py:62-134`）——五步流水线：

```python
# ingest/pipeline.py:62-134（精简）
async def ingest_document(*, db, project_id, user_id, filename, data):
    file_type = infer_type(filename, data)                 # 0 类型推断 + 大小上限
    content_hash = sha256_fingerprint(data)
    dup = await db.scalar(select(KnowledgeDocument).where(   # 1 MD5 去重：同项目跳过
        KnowledgeDocument.project_id == project_id,
        KnowledgeDocument.content_hash == content_hash))
    if dup: return {"status": "skipped"}   # ...其余字段（id/reason）省略
    doc = KnowledgeDocument(...); db.add(doc); await db.commit()   # 2 建元数据记录
    parsed = await asyncio.to_thread(parse_document, ...)   # 3 解析（CPU 密集→线程池，不阻塞事件循环）
    chunks = chunk_text(parsed.text, chunk_size, overlap)   # 4 分块
    await _embed_chunks(db=db, project_id=project_id, doc_id=doc.id, chunks=chunks)   # 4 批量向量化→MemoryItem(kind="user_doc")
    _save_raw_file(...); doc.status = "ready"               # 5 落盘原文件 + 定版
```

- **解析工厂**（`parsers.parse_document`，`ingest/parsers.py:113-141`）：按 `txt/md/pdf/docx` 分派；PDF 用 PyMuPDF 逐页提取，扫描件（无可提取文本）抛 `DocumentParseError`；`normalize()`（`parsers.py:39-52`）压缩空白、识别标题、字数 < `min_text_chars` 即判扫描件。`sha256_fingerprint`（`parsers.py:144-146`）做去重指纹。
- **删除**（`delete_document`，`ingest/pipeline.py:173-188`）：按 `doc_key="udoc:{doc.id}"` 定位 `MemoryItem(kind="user_doc")` 向量分块一并清，再删元数据与原文件——保证"删文档即删索引"，不污染检索。

> 关键设计：**解析放进 `asyncio.to_thread`**（`ingest/pipeline.py:100`）——PyMuPDF/python-docx 是同步 CPU 密集，直接跑会卡死异步事件循环；这是"异步服务里调同步库"的标准解法，值得记住。

### 19.5 调用关系

```
上游：services/governance/tools_impl.py:20   search_literature()  ← 唯一的业务调用方
      services/governance/tools_impl.py:93   check_plagiarism()   ← 直接调 hybrid_retriever
      services/governance/artifacts.py       generate_artifact()  ← 生成产物前取证据
        │
        ▼
  RagPipeline.search()                       pipeline.py:64
        ├── rewrite_query()  → LLMProvider.chat(json_mode)
        ├── hybrid_retriever.dense_search()  → PG pgvector
        ├── hybrid_retriever.sparse_search() → BM25（进程内索引）
        ├── hybrid_retriever.sibling_search()→ PG json_extract_path_text
        └── reranker.rerank()                → CrossEncoder（线程池）
```

### 19.6 最小可复现骨架

```python
# 最小可复现：三阶段 RAG（≈70 行）
import asyncio

REJECT = ("无法", "无关", "抱歉", "不能", "不适合")
SYNONYM = {"大模型": "大模型 大语言模型 LLM 预训练语言模型",
           "检索增强": "检索增强 RAG 检索增强生成 知识检索",
           "向量": "向量 embedding 嵌入 稠密检索"}


async def rewrite_query(q, llm_json, enabled=True, mode="auto"):
    """S1 改写：四道防线（自适应 / 拒答 / 漂移 / 异常）全部回退到规则改写"""
    rule = q
    for term, expand in SYNONYM.items():                 # 规则兜底：术语同义扩充
        if term.lower() in q.lower() and expand.lower() not in rule.lower():
            rule = f"{rule} {expand}"
            break
    if not enabled or mode == "off":
        return q, "idle"
    if mode == "auto" and len(q) <= 40 and not any(m in q for m in ("咋", "啥", "怎么破")):
        return rule, "skip"                              # 简单短句 → 跳过 LLM，零开销
    try:
        data = await llm_json(q)
        rw = (data.get("rewritten") or "").strip()
        low = rw.lower()
        if len(rw) < 8 or any(m in low[:60] for m in REJECT):
            return rule, "rule_fallback"                 # 拒答
        if len(set(q) & set(rw)) / max(1, len(set(q))) < 0.15:
            return rule, "rule_fallback"                 # 语义漂移（字符重合度过低）
        return rw, "llm"
    except Exception:
        return rule, "rule_fallback"                     # 异常也回退，绝不返回空


def rrf_fuse(*result_lists, k=60, top_k=20):
    """S2 RRF：score(d) = Σ 1/(k + rank_i(d))。只用排名，免疫量纲差异"""
    fused = {}
    for results in result_lists:
        for rank, item in enumerate(results):
            fused.setdefault(item["id"], {**item, "rrf_score": 0.0})
            fused[item["id"]]["rrf_score"] += 1.0 / (k + rank + 1)
    return sorted(fused.values(), key=lambda x: x["rrf_score"], reverse=True)[:top_k]


async def search(query, top_k=5, recall_k=20, project_id=None):
    rewritten, strategy = await rewrite_query(query, llm_json)
    dense = await dense_search(rewritten, recall_k)      # 路① 稠密（向量）
    sparse = await sparse_search(rewritten, recall_k)    # 路② 稀疏（BM25）
    roads = [dense, sparse]
    if rewritten != query:
        roads.append(await dense_search(query, recall_k))  # 路④ 原查询锚点：防漂移
    if project_id is not None:
        roads.append(await project_dense_search(query, project_id, recall_k))  # 路⑤ 项目库
    fused = rrf_fuse(*roads, top_k=recall_k)
    fused = rrf_fuse(fused, await sibling_search(fused, window=1), top_k=recall_k)  # 路⑥ 邻块

    # S3-a 降噪：仅稀疏命中的 = 关键词重叠噪声，软惩罚
    dense_rank = {r["id"]: i for i, r in enumerate(dense, 1)}
    for item in fused:
        rank = dense_rank.get(item["id"])
        if rank is None:
            item["rerank_boost"], item["noise_flag"] = 0.982, "sparse_only"
        elif rank > max(1, int(len(dense_rank) * 0.35)):
            item["rerank_boost"], item["noise_flag"] = 0.995, "weak"
        else:
            item["rerank_boost"], item["noise_flag"] = 1.0, "ok"

    # S3-b 精排：主查询与改写查询双打分取 max
    out = await rerank(query, fused, top_k=top_k,
                       alt_query=rewritten if rewritten != query else None)
    for r in out:
        r["rerank_score"] *= r.get("rerank_boost", 1.0)
    return {"rewritten": rewritten, "strategy": strategy,
            "results": sorted(out, key=lambda x: x["rerank_score"], reverse=True)}


async def rerank(query, candidates, top_k=5, alt_query=None, model=None):
    """⚠️ 交叉编码器是 CPU 阻塞（首载 10~60s，推理 5~30s），必须 to_thread"""
    def _sync():
        scores = model.predict([(query, c["content"]) for c in candidates])
        if alt_query and alt_query != query:
            alt = model.predict([(alt_query, c["content"]) for c in candidates])
            scores = [max(s, a) for s, a in zip(scores, alt)]
        return scores
    scores = await asyncio.to_thread(_sync)               # ← 关键：丢线程池
    for c, s in zip(candidates, scores):
        c["rerank_score"] = float(s)
    return sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)[:top_k]
```

**复现要点**：① 改写失效必须回退**规则改写**而非原查询；② RRF 只用排名不用分数；
③ 改写生效时一定要保留**原查询稠密路**当锚点；④ 精排必须 `asyncio.to_thread`，
否则整个 FastAPI 事件循环被冻结（SSE 断流、所有请求挂起）——这是本项目踩过的最大的坑。

### 19.7 验证与预期输出

```powershell
envs\lunjiang\python.exe scripts/ingest_corpus.py     # 先入库（81 篇 → 约 1376 块）
envs\lunjiang\python.exe scripts/smoke_rag.py         # 三阶段检索自检
```

验证改写策略标记（观察 `strategy` 字段走的是哪条路）：

```powershell
envs\lunjiang\python.exe -c "
import asyncio
from services.rag.query_rewrite import rewrite_query, is_rewrite_worthwhile
async def main():
    for q in ['大模型微调', '我这心里慌得一批，开题报告咋整才站得住脚']:
        r = await rewrite_query(q)
        print(f'{q[:16]:18} worthwhile={is_rewrite_worthwhile(q)!s:5} strategy={r[\"strategy\"]:14} -> {r[\"rewritten\"][:50]}')
asyncio.run(main())
"
```

预期：短术语「大模型微调」走 `skip`（零 LLM 开销），长尾口语「心里慌得一批…」走 `llm` 或 `rule_fallback`。

**→ 主动练习（改一行看变化）**：把 `sparse_only` 的噪声惩罚 ×0.982 改成 ×0.5，重跑 19.7——观察仅 BM25 命中的候选是否被压到尾部；再把 `rag.chunk_size` 512 改 256 重跑入库，对比召回差异，体会分块粒度的权衡。

### 19.8 面试点与坑

| 点 | 说明 |
| --- | --- |
| 面试点：为什么是三阶段而不是直接向量搜 | 直接搜同时吃三个亏：口语查询匹配差（需改写）、专业术语召回差（需 BM25）、Top20 里 15 条噪音（需精排）。三阶段各解一个。 |
| 面试点：RRF vs 加权求和 | RRF 只用排名，不需要归一化、不需要调权重、对单路分数分布不敏感；代价是丢掉分数精度，所以后面接交叉编码器补回。这是工业界"召回便宜、精排昂贵"的标准分工。 |
| 坑：BM25 索引是进程内的 | `retriever._bm25` 存在内存里，服务重启后为空。已做双保险：`main.py:68` 启动后台预热 + `retriever.py:84` 首次查询懒重建。**但多副本部署时每个副本各建一份**，知识库更新后不会自动同步，需要重启或加失效机制。 |
| 坑：精排阻塞事件循环 | 见 N.6 要点④。`reranker.py:3-5` 的模块 docstring 专门写了这个警告。 |
| 坑：`sibling_search` 强绑定 PostgreSQL | 用了 `json_extract_path_text`（`retriever.py:140/142/147`），换数据库要重写这段。 |
| 已知边界：精排后才有语义精度 | 若关闭精排（`use_rerank=False`），结果直接用 RRF 分截断，质量下降明显——RRF 只是"多路投票"，不理解语义。 |

***

> 🏁 **里程碑 1**：①意图分类 + ②记忆 + ③检索——三大「输入侧」能力骨架已齐。**你现在能跑通一次完整 RAG 查询（19.7），并说清每一条候选的排名是怎么来的**。接下来是把 LLM 的"手"（工具）装上护栏。

***

## 第 20 课 工具实现（tools_impl）

> 🔗 复习锚点：第 6.4 课讲过「Function-Calling 循环」这个**调用机制**，本课讲 14 个工具的**函数体本身**怎么写（含 ④ 结构化产物实例）。

### 20.1 问题与契约

「工具」= **Agent 真正能干的事**。契约极其简单：

| 项 | 内容 |
| --- | --- |
| 输入 | 具名参数（全部可被 JSON 序列化） |
| 输出 | `str` / `dict` / `list`（**必须可 JSON 序列化**，因为要回灌给 LLM、要写审计） |
| 约束 | ① 可以是 `async def` 也可以是普通 `def`（同步的自动丢线程池）；② **工具内部不得自己 try 掉所有异常**——交给治理栈重试；③ 来自 LLM 的参数一律当成"不可信输入"先收敛 |

### 20.2 文件清单

| 文件 | 行数 | 职责 |
| --- | --- | --- |
| `tools_impl.py` | 192 | 8 个核心论文工具 + `register_all()` 注册入口 |
| `academic_tools.py` | 129 | 6 个学术工具（翻译/润色/方法推荐/参考文献格式化/摘要/术语） |
| `artifacts.py` | 110 | 结构化产物生成（综述初稿 / 开题报告 / 答辩大纲） |
| `../agent/specialists/schemas.py` | 49 | 由注册表反推 OpenAI function-calling schema |

### 20.3 核心数据结构

**14 个已注册工具全清单**（限流/熔断/降级参数来自 `configs/tools.yaml`）：

| # | 工具名 | 签名 | 依赖 | rpm | 熔断组 | 降级参数 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `search_literature` | `(query, top_k=5)` | RAG | 20 | rag_pipeline | `top_k=5` |
| 2 | `rewrite_query` | `(query)` | RAG 改写 | 60 | llm_light | — |
| 3 | `topic_analysis` | `(major, interest, requirement="")` | LLM | 10 | llm_main | — |
| 4 | `generate_section` | `(section, outline, references, preferences)` | LLM | 10 | llm_main | — |
| 5 | `check_format` | `(text, strict=True)` | 规则 + LLM | 15 | llm_main | `strict=false` |
| 6 | `check_plagiarism` | `(text, granularity="paragraph")` | 检索 | 10 | rag_pipeline | `granularity=paragraph` |
| 7 | `detect_ai_text` | `(text, mode="standard")` | 启发式 + LLM | 10 | llm_main | `mode=fast` |
| 8 | `generate_artifact` | `(kind, topic, requirement, project_id=None)` | RAG + 模板 | 6 | llm_main | `kind=review_draft` |
| 9 | `translate_academic` | `(text, target="en")` | LLM | 15 | llm_main | — |
| 10 | `polish_academic` | `(text, style="formal")` | LLM | 15 | llm_main | — |
| 11 | `recommend_method` | `(question)` | LLM/RAG | 15 | rag_pipeline | `question=…` |
| 12 | `format_reference` | `(authors, title, journal, …)` **同步** | 纯规则 | 60 | default | `style=gb7714` |
| 13 | `generate_abstract` | `(topic, keywords, …)` | LLM | 10 | llm_main | `length=200` |
| 14 | `term_explain` | `(term)` | LLM/RAG | 20 | rag_pipeline | — |

> 注意 #12 `format_reference` 是**普通 `def`（同步函数）**——它是"同步 handler 自动走线程池"这条设计的现成例子，见 20.4。

### 20.4 代码走读

**入口：`register_all()` — `tools_impl.py:154`**。就是 8 次 `tool_registry.register(ToolSpec(...))` + 调用 `_register_academic()`（L178）再注册 6 个学术工具。

**值得学的三个实现细节**：

**① LLM 参数必须收敛**（`tools_impl.py:16-19`）——LLM 经常把 `top_k` 传成字符串 `"5"`：

```python
try:
    top_k = int(top_k or 5)
except (TypeError, ValueError):
    top_k = 5
top_k = max(1, min(top_k, 20))     # 收敛到合法窗口，防字符串/越界
```

这是"不可信输入"原则：LLM 输出的一切参数都要**先夹到合法区间**再用，否则会出现 `arr[: "5"]` 这类 TypeError。

**② 规则 + LLM 双通道**（`check_format` L58-82）：纯规则抓硬伤（正文<200 字、缺摘要、缺参考文献、段落>800 字、连续标点），LLM 抓软伤（结构完整性、标题层级、语言规范）。最终 `pass = not issues and "通过" in llm_review`（L82）——**规则与 LLM 都认可才算过**，比单通道稳得多。

**③ 启发式与 LLM 加权融合**（`detect_ai_text` L126-145）：

```python
heuristic = min(1.0, (hits / max(1, len(sentences))) * 0.6 + (0.3 if var < 80 else 0))
#                     ↑ 高频AI词密度                      ↑ 句长方差过小（AI 文本特征）
return {"ai_probability": round(0.4 * heuristic + 0.6 * llm_prob, 3),
        "heuristic_signals": {"sentence_len_variance": round(var, 1), "ai_word_hits": hits}}
```

**为什么不让 LLM 直接给结论？** 因为纯 LLM 判定不可复现、也无法解释。给一个可解释的启发式分（句长方差 + AI 高频词命中）再与 LLM 加权，既提高稳定性，又能在前端展示"判定信号"。

**④ 查重用字符 bigram Jaccard**（`_char_sim` L108-115）：不额外加载模型，两个字符集合的交/并即相似度，轻量且对中文友好。

**④ 结构化产物（`artifacts.py`）——"模板 + 证据"而非裸生成**：20.4 前面走的是"怎么调用工具"，这里看一个**典型工具体内部**怎么写（14 个工具里的 #8 `generate_artifact`，注册参数见 20.3 表）。

```python
# services/governance/artifacts.py:71-111（精简）
async def generate_artifact(kind, topic, *, requirement="", references="",
                            project_id=None) -> dict:
    if kind not in _ARTIFACT_TEMPLATES:                 # ① kind 白名单校验
        raise ValueError(f"不支持的产物类型: {kind}，可选: {KINDS}")
    tmpl = _ARTIFACT_TEMPLATES[kind]                    # 模板: review_draft / proposal_report / defense_outline
    out = await rag_pipeline.search(topic, top_k=6, project_id=project_id)   # ② 先检索证据
    evidence = "\n".join(f"[{i}] (来源: ...) {r['content'][:260]}"
                         for i, r in enumerate(out["results"], 1)) \
               or "(未检索到直接证据，请基于常识…撰写并提示核实)"           # ③ 证据为空也给兜底话术
    prompt = (f"请生成《{tmpl['name']}》\n研究主题: {topic}\n"
              f"【章节骨架（必须完整覆盖）】\n" + "\n".join(tmpl["outline"]) + "\n\n"
              f"【检索证据（引用请标注[编号]）】\n{evidence}\n\n【生成要求】\n{tmpl['instruction']}")
    content = await LLMProvider().chat([{"role":"user","content":prompt}], max_tokens=2500)
    return {"kind": kind, "artifact_name": tmpl["name"], "content": content,
            "evidence_count": len(out["results"]), "sources": [...]}
```

三个值得学的点：
- **骨架固定，让 LLM 填空**（`artifacts.py:14-66`）：综述/开题/答辩三类产物各有一套 `outline`+`instruction`，结构完整性由模板保证，不赌模型自觉——这与 20.4 ②"规则抓硬伤"同源：**能用确定性手段锁住的，就不交给概率**。
- **先生成证据再生成文**（`artifacts.py:82-87`）：把 RAG 检索结果编成 `[编号]` 注入提示词，逼模型引用来源，抑制空泛编造；检索为空时**显式降级话术**而不是硬编。
- **证据截断 260 字/条、top_k=6**（`artifacts.py:83-85`）：控制上下文长度——产物是长文，证据必须省着用。

### 20.5 调用关系

```
注册（进程启动时）
  main.py:64-65  lifespan → register_all()
  agent/engine.py:42-43  get_graph() 内兜底再注册一次（脚本/评测入口不经过 lifespan）

调用
  专项 Agent：node_factory.py:51-54   executor() → tool_registry.call(**args)
  Planner：   planner.py:188-190      逐步执行 → tool_registry.call(**params)
  schemas.py:5-22                     从注册表反推 OpenAI function-calling schema
```

> **注册是幂等的**（`tool_registry.py:63-67` 用 `existing.handler is spec.handler` 判同），所以两处都调 `register_all()` 不会重复注册。

### 20.6 最小可复现骨架

```python
# 最小可复现：工具层（≈35 行）
from services.governance.tool_registry import ToolSpec, tool_registry


async def search_literature(query: str, top_k: int = 5):
    """① LLM 给的参数一律先收敛：字符串 / 越界 / 负数都要夹回来"""
    try:
        top_k = int(top_k or 5)
    except (TypeError, ValueError):
        top_k = 5
    top_k = max(1, min(top_k, 20))
    out = await rag_pipeline.search(query, top_k=top_k)
    return {"query": out["rewritten"],
            "results": [{"title": (r.get("meta") or {}).get("title", "未知"),
                         "content": r["content"][:300],
                         "score": round(r.get("rerank_score", 0), 4)}
                        for r in out["results"]]}


async def detect_ai_text(text: str, mode: str = "standard"):
    """② 启发式（可解释）× 0.4 + LLM × 0.6 加权，比纯 LLM 判定更稳"""
    sentences = [s for s in re.split(r"[。！？]", text) if len(s.strip()) > 5]
    lens = [len(s) for s in sentences] or [0]
    mean = sum(lens) / len(lens)
    var = sum((x - mean) ** 2 for x in lens) / len(lens)
    hits = sum(text.count(w) for w in ["首先", "其次", "总之", "综上所述", "值得注意的是", "赋能"])
    heuristic = min(1.0, (hits / max(1, len(sentences))) * 0.6 + (0.3 if var < 80 else 0))
    llm = await provider.chat([...], json_mode=True, temperature=0.1)
    return {"ai_probability": round(0.4 * heuristic + 0.6 * float(llm["ai_probability"]), 3),
            "heuristic_signals": {"sentence_len_variance": round(var, 1), "ai_word_hits": hits}}


def format_reference(authors: str = "", title: str = "", journal: str = "", style: str = "gb7714"):
    """③ 同步函数也能注册：治理层自动用 asyncio.to_thread 执行，不阻塞事件循环"""
    ...


def register_all() -> None:
    """④ 幂等注册：同一个 handler 重复注册会被直接跳过"""
    for name, desc, handler in [
        ("search_literature", "三阶段RAG文献检索", search_literature),
        ("detect_ai_text", "AI痕迹检测", detect_ai_text),
        ("format_reference", "参考文献格式化(GB/T 7714/APA)", format_reference),
    ]:
        tool_registry.register(ToolSpec(name=name, description=desc, handler=handler))
```

**复现要点**：① 参数收敛（`max(1, min(x, 20))`）；② 规则/启发式与 LLM 双通道融合而非纯 LLM；
③ 同步函数照注册不误，同步→线程池的适配在治理层做（`tool_registry.py:87-92`），工具作者不用关心；
④ `register_all()` 必须幂等。

### 20.7 验证与预期输出

```powershell
envs\lunjiang\python.exe -c "
import asyncio
from services.governance.tools_impl import register_all
from services.governance.tool_registry import tool_registry
register_all(); register_all()          # 连调两次验证幂等
print('已注册工具数:', len(tool_registry.tools))
print(sorted(tool_registry.tools))
"
```

预期：`已注册工具数: 14`，且两次 `register_all()` 后数量不变。

单独跑一个工具（绕过 Agent，直接看输出）：

```powershell
envs\lunjiang\python.exe -c "
import asyncio, json
from services.governance.tools_impl import check_format, register_all
register_all()
r = asyncio.run(check_format('摘要：本文研究检索增强生成。'))
print(json.dumps(r, ensure_ascii=False, indent=2)[:400])
"
```

预期：返回 `{"rule_issues": [...], "llm_review": "...", "strict": true, "pass": false}`。

**→ 主动练习（改一行看变化）**：把 `check_format` 的规则阈值「正文 < 200 字」改成 < 400 字，喂一篇 300 字短文——观察判定从"通过"翻转为"不通过"，体会**规则阈值即产品行为**。

### 20.8 面试点与坑

| 点 | 说明 |
| --- | --- |
| 面试点：为什么工具不自己重试 | 重试/限流/熔断是每个工具都要的横切关注点。放在工具里 = 14 份重复代码且无法统一观测；放在治理层 = 一处实现，全部生效。这就是**横切关注点下沉**。 |
| 面试点：为什么输出必须可 JSON 序列化 | 三个下游都要它：① 回灌 LLM 上下文；② 写审计日志（`_safe()` 做 `json.dumps`）；③ SSE 推给前端。不可序列化会同时炸三处。 |
| 坑：同步函数忘记 `async` 不会报错 | `format_reference` 就是同步的，靠 `_invoke_handler` 的 `asyncio.to_thread` 兜住（`tool_registry.py:89-92`）。**但如果同步函数里有 CPU 密集循环，线程池会被占满**，需要单独评估。 |
| 坑：`top_k` 类参数 | LLM 输出的类型不可信。所有数值参数都要 `int()` + 夹区间，Planner 侧另有 `_coerce_params()` 兜底（`planner.py:65-79`）。 |

***

## 第 21 课 工具治理栈（governance）

> 🔗 复习锚点：第 11 课讲过「为什么 LLM 调工具要一层治理栈」，本课把六步流水线**每一步的实现**拆开看。

> 这是整个项目**工程含量最高**的包，也是面试最容易被深挖的部分。建议放慢读。

### 21.1 问题与契约

LLM 调用工具有四类失范，治理栈逐个防：

| 失范 | 后果 | 防线 |
| --- | --- | --- |
| 乱调/越权 | 学生调用了管理员工具 | RBAC |
| 短时间狂调 | 打爆下游、烧钱 | 滑动窗口限流 |
| 下游已瘫还在调 | 雪崩、超时堆积 | 三态熔断 |
| 偶发失败 | 一次抖动就前功尽弃 | 三级容错（重试→降级→人机） |

契约：**任何一次工具调用，必须且只能经过 `ToolRegistry.call()`**（`tool_registry.py:95`）。

### 21.2 文件清单

| 文件 | 行数 | 职责 |
| --- | --- | --- |
| `tool_registry.py` | 161 | **统一入口**：注册 + 六步调用流水线 |
| `rate_limiter.py` | 41 | Redis ZSET 滑动窗口限流（Lua 原子） |
| `circuit_breaker.py` | 98 | 三态熔断（CLOSED/OPEN/HALF_OPEN，Lua 原子） |
| `retry.py` | 94 | 三级容错：指数退避重试 → 默认参数降级 → 人机兜底 |
| `dist_lock.py` | 66 | 分布式锁（SET NX PX + Lua 校验释放） |
| `skill.py` | 138 | 行为观测 + Skill 自动沉淀 + 三维匹配 |
| `tools_impl.py` / `academic_tools.py` / `artifacts.py` | 431 | 工具实现（见第 20 课） |

### 21.3 核心数据结构

**`ToolSpec`**（`tool_registry.py:45-53`）——注册表里的一条目：

| 字段 | 默认 | 含义 |
| --- | --- | --- |
| `name` | — | 工具名（全局唯一键） |
| `description` | — | 给 LLM 看的描述，会进 function-calling schema |
| `handler` | `None` | 同步或异步函数 |
| `rate_limit_rpm` | 30 | 每分钟次数（**会被 `tools.yaml` 覆盖**） |
| `lock_key` | `None` | 非空则启用分布式锁（当前 14 个工具均未配置，属预留能力） |
| `fallback_kwargs` | `{}` | 第二级容错的降级参数 |
| `breaker` | `"default"` | 熔断分组名（同组共享一个熔断器） |

**熔断三态**（`circuit_breaker.py`，状态存 Redis Hash `breaker:{name}`，多实例共享同一视图）：

```
CLOSED ──连续失败 5 次──▶ OPEN ──30s 后──▶ HALF_OPEN
   ▲                                          │
   │                              连续成功 2 次│ 任一失败
   └──────────────────────────────────────────┘
```

配置默认值（`circuit_breaker.py:68-73`）：`failure_threshold=5`、`recovery_timeout=30s`、`half_open_successes=2`。

### 21.4 代码走读

**入口：`ToolRegistry.call()` — `tool_registry.py:95-139`**。六步流水线：

```python
spec = self.get(name)                                   # L99  未注册直接 KeyError
# ① RBAC + ② 限流（放同一个 try：被拒也要写审计）
try:
    if not rbac_policy.check_tool_permission(user_role, name):
        raise PermissionError(...)                      # L104-105
    await check_rate(f"{name}:{user_id}", spec.rate_limit_rpm)   # L106
except (PermissionError, RateLimitExceeded) as e:       # L107
    await self._finalize(name, ok=False, error=str(e))  # L108  ← 拒绝也要留痕
    raise
# ③ 熔断检查
await breaker.before_call()                             # L115  OPEN 直接抛 CircuitOpenError
# ④ 分布式锁（仅 lock_key 非空时启用）
lock = DistributedLock(spec.lock_key) if spec.lock_key else None      # L120
cm = lock if lock is not None else nullcontext()        # L121  ← 无锁时零开销
async with cm:
    result = await resilient_call(_run, tool_name=name,
                                  fallback_kwargs=spec.fallback_kwargs or None, **kwargs)  # L123
# ⑤ 成功：更新熔断 + 落审计 + 行为观测
await breaker.on_success()                              # L128
await self._finalize(name, ok=True, error="")           # L129
```

**设计亮点：L107-108 把"鉴权/限流被拒"也写进审计**。安全相关事件不能因为"没执行成功"就不留痕，这是合规视角的考量。

**三级容错**（`retry.py:78-94`）是治理栈的灵魂：

```
第一级 attempt(args, kwargs)          原参数 + 指数退避重试 3 次
        ↓ 全失败
第二级 attempt(fallback_args/kwargs)  换成 YAML 里的默认安全参数再重试一轮
        ↓ 仍失败
第三级 raise HumanInterventionRequired  抛给上层 → Agent 图转 interrupt 人工介入
```

退避公式（`retry.py:73`）：`delay = min(max_delay, base_delay * 2**i) * (0.5 + random())`，
即 0.5s → 1s → 2s（上限 8s），**再乘 0.5~1.5 的随机抖动**防惊群。

另外 `retry.py:63` 每次 attempt 都套了 `asyncio.wait_for(fn(...), timeout=call_timeout)`，
默认 120s（`retry.py:32`）——**总超时天花板**，即使底层忘记配 timeout 也不会永久挂起。

**Skill 自动沉淀**（`skill.py:36-54`）：监听每次调用，把 `(agent, tool, 参数的"形状")` 做 sha1 摘要当 key（`L27-32`，只保留参数名和类型、屏蔽具体取值），Redis 累计 `total/ok`。**同模式连续 3 次成功且无失败** → 落库成 Skill（`L53`）。匹配时三维加权（`L130-134`）：`0.5×意图语义相似度 + 0.3×参数名重合率 + 0.2×成功率频度分`。

**审计净化：超限参数的三件套**（[infrastructure/audit.py](../infrastructure/audit.py)）

合规硬约束：**审计日志不得存整段正文**（论文全文/长文本入参不能进库）。净化在唯一落库口 `write_audit` 统一完成（L63-66），覆盖 HTTP/认证/工具三条入口。核心是 `_sanitize_value`（L23-40）这个递归纯函数：

```python
if isinstance(value, str) and len(value) > chars:          # chars 默认 200
    return {"fp": hashlib.sha256(value.encode("utf-8")).hexdigest()[:16],
            "sum": value[:200],                            # 摘要：前 200 字，可读
            "len": len(value)}                             # 长度：统计超限占比
```

- **指纹 `fp`**：sha256 前 16 位。相同原文 → 相同指纹，人工审计时可"对账"是否同一份长文本，而不暴露内容；
- **摘要 `sum`**：保留前 200 字，兼顾可读性与信息量；**长度 `len`**：用于统计超限字段占比；
- 递归处理 dict/list，**只有超限字符串被替换**，其余字段（状态码/耗时/工具名）原样保留（`test_audit_sanitize.py` 覆盖）。

**请求级审计中间件**（[api/middleware/audit.py](../api/middleware/audit.py)，`main.py:82` 全局挂载）：与工具审计（21.4 步骤⑧）共用 `write_audit` 这一个落库口，对**每个 API 请求**（白名单 `/`、`/health`、`/docs`、`/openapi.json`、`/favicon.ico` 除外）留一条审计：

```python
response = await call_next(request)               # 先放行，不阻塞响应
...                                              # 尽力解析 Authorization（不校验过期，仅留痕）
asyncio.get_running_loop().create_task(self._persist(
    action="api_request", resource=f"{method} {path}", detail={...}))   # fire-and-forget
response.headers["X-Process-Time-Ms"] = str(duration_ms)
```

- **请求级只记"元数据"**（方法/路径/状态码/耗时/用户/IP），正文内容在请求级不做记录——凡涉及长文本内容的审计才走 `write_audit` 的净化逻辑，两级职责不同；
- **`X-Process-Time-Ms` 响应头**是排障利器：curl/前端直接看到每个请求的真实耗时，不用翻日志。

### 21.5 调用关系

```
上游：node_factory.py:52  专项 Agent 的 executor()
      planner.py:188      Planner 逐步执行
        │
        ▼
  ToolRegistry.call()   ← 唯一入口
        ├── infrastructure/rbac.policy          RBAC（configs/rbac.yaml）
        ├── rate_limiter.check_rate()           → Redis ZSET
        ├── circuit_breaker.before_call()       → Redis Hash
        ├── dist_lock.DistributedLock           → Redis SET NX PX
        ├── retry.resilient_call()              → 真正的 handler
        ├── infrastructure.audit.write_audit()  → PG 审计表
        └── skill.BehaviorTracker.observe()     → Redis Hash → PG skills 表
```

### 21.6 最小可复现骨架

```python
# 最小可复现：治理栈（≈60 行）
import asyncio, random, time
from contextlib import nullcontext


async def call(self, name, *, user_id, user_role, call_context=None, **kwargs):
    """六步流水线：RBAC → 限流 → 熔断 → 锁 → 三级容错 → 审计+观测"""
    spec = self.get(name)
    started = time.perf_counter()
    # ① ② RBAC + 限流：被拒也写审计（安全事件不可遗漏）
    try:
        if not rbac_policy.check_tool_permission(user_role, name):
            raise PermissionError(f"角色 {user_role} 无权调用 {name}")
        await check_rate(f"{name}:{user_id}", spec.rate_limit_rpm)
    except (PermissionError, RateLimitExceeded) as e:
        await self._finalize(name, ok=False, error=str(e))
        raise
    breaker = self._breakers[spec.breaker]
    try:
        await breaker.before_call()                       # ③ 熔断检查
        lock = DistributedLock(spec.lock_key) if spec.lock_key else None
        async with (lock or nullcontext()):               # ④ 互斥锁（无锁零开销）
            result = await resilient_call(                # ⑤ 三级容错
                lambda **kw: invoke(spec, **kw), tool_name=name,
                fallback_kwargs=spec.fallback_kwargs or None, **kwargs)
        await breaker.on_success()
        await self._finalize(name, ok=True)
        return result
    except HumanInterventionRequired as e:
        await breaker.on_failure()                        # 容错耗尽才算真失败
        await self._finalize(name, ok=False, error=str(e))
        raise
    except Exception as e:
        await breaker.on_failure()
        await self._finalize(name, ok=False, error=str(e))
        raise


async def resilient_call(fn, *, tool_name, fallback_kwargs=None,
                         max_attempts=3, base_delay=0.5, max_delay=8.0,
                         call_timeout=120, **kwargs):
    """三级容错：重试 → 降级参数重试 → 抛人机介入"""
    last = None
    async def attempt(**kw):
        nonlocal last
        for i in range(max_attempts):
            try:
                return await asyncio.wait_for(fn(**kw), timeout=call_timeout)  # 总超时天花板
            except Exception as e:
                last = e
                if i == max_attempts - 1:
                    break
                delay = min(max_delay, base_delay * (2 ** i)) * (0.5 + random.random())  # 抖动
                await asyncio.sleep(delay)
        raise last
    try:
        return await attempt(**kwargs)                    # 第一级：原参数
    except Exception:
        pass
    if fallback_kwargs:                                   # 第二级：默认安全参数
        try:
            return await attempt(**fallback_kwargs)
        except Exception:
            pass
    raise HumanInterventionRequired(tool_name, last)      # 第三级：人机兜底
```

**复现要点**：① 鉴权/限流**被拒也要写审计**；② `nullcontext()` 让无锁路径零开销；
③ `asyncio.wait_for` 作为总超时天花板；④ 退避必须带**随机抖动**（否则多个请求同时重试，形成惊群）；
⑤ 只有"三级容错都耗尽"才算熔断失败，短暂抖动不该触发熔断。

### 21.7 验证与预期输出

```powershell
envs\lunjiang\python.exe scripts/smoke_governance.py    # 治理栈 9 项冒烟
```

逐项验证六个治理件（需 Redis 在跑）：

```powershell
envs\lunjiang\python.exe -c "
import asyncio
from services.governance.circuit_breaker import CircuitBreaker
from services.governance.rate_limiter import check_rate, RateLimitExceeded
async def main():
    b = CircuitBreaker('smoke_test')
    for _ in range(5): await b.on_failure()          # 连续 5 次失败
    print('连续失败 5 次后状态:', await b.state())     # 期望 OPEN
    try:
        await b.before_call()
    except Exception as e:
        print('熔断生效:', type(e).__name__, e)
    for _ in range(2): await b.on_success()          # 需先等 30s 进入 HALF_OPEN
asyncio.run(main())
"
```

预期：状态 `OPEN`，`before_call()` 抛 `CircuitOpenError`。

**→ 主动练习（改一行看变化）**：把 `failure_threshold` 从 5 改成 2，对一个会失败的下游工具连续调用两次——观察 CLOSED→OPEN、30s 后 HALF_OPEN、连续 2 次成功回 CLOSED 的完整状态机（对照 21.3 的状态图）。

### 21.8 面试点与坑

| 点 | 说明 |
| --- | --- |
| 面试点：限流为什么用 Lua | `ZREMRANGEBYSCORE` + `ZCARD` + `ZADD` 三步必须原子。分三次调用会有并发竞态（两个请求同时读到 count=9，都通过，实际放进 11 个）。Lua 脚本在 Redis 里单线程执行，天然原子。 |
| 面试点：为什么熔断状态存 Redis 而不是进程内 | 多副本部署时，进程内熔断只能保护自己那个副本；下游已经瘫了，其他副本还在疯狂调用。存 Redis 才能**全局共享同一熔断视图**。 |
| 面试点：三级容错的顺序 | 原参数重试 → 降级参数重试 → 人机介入。**"降级"是关键中间层**：LLM 传的 `top_k=50` 导致超时，换成默认 `top_k=5` 往往就成了，不必一上来就麻烦用户。 |
| 坑：分布式锁目前是预留能力 | `configs/tools.yaml` 里 14 个工具**都没有配 `lock_key`**，所以 `call()` 里的锁分支实际不走。装配正确性由单测 `tests/test_tool_registry_call.py::test_call_distributed_lock_assembled_for_locked_tool` 保证。面试时说"我们实现了分布式锁"要补一句"目前是预留"。 |
| 坑：Skill 沉淀阈值是"连续成功" | 条件是 `ok_cnt >= 3 and ok_cnt == total`（`skill.py:53`）——中间失败过一次就清零重来。这是刻意的：只沉淀"从未失败"的模式。 |
| 坑：审计是 fire-and-forget | `_finalize` 里的审计与观测失败只记日志（`tool_registry.py:151-152`），**不会阻断业务**。所以审计缺失时不会报错，要看日志。 |

***

> 🏁 **里程碑 2**：④工具 + ⑤治理——LLM 的"手"已装上护栏。**任何工具调用都走完 RBAC→限流→熔断→锁→重试→审计 六步**，具备生产可用的容错面。

***

## 第 22 课 可观测（observability）

> 🔗 复习锚点：第 12.2 课讲过「Trace Span 是什么」，本课讲 span 怎么**跨异步任务传递、怎么落库、怎么还原成树**。

### 22.1 问题与契约

多智能体系统最大的调试痛点是：**"它到底为什么给出这个答案？"** 传统日志是平铺的文本流，无法还原"哪个节点调用了哪个工具、花了多久、消耗多少 token"。

| 项 | 内容 |
| --- | --- |
| 输入 | 代码里任意一处 `with span(name, kind, input_data=...):` |
| 输出 | 树形嵌套的 Span 记录，落 PG `trace_spans` 表 |
| 硬约束 | **记录行为不得阻塞主流程**（否则拖慢每一次对话） |
| 设计目标 | 按 `trace_id` 拉出一棵树 = 这次请求的完整"行为回放" |

### 22.2 文件清单

| 文件 | 行数 | 职责 |
| --- | --- | --- |
| `services/observability/trace.py` | 164 | Span 记录、异步落库、行为回放查询 |
| `api/observability/router.py` | — | 管理端查询接口（admin 专属） |

### 22.3 核心数据结构

**`_SpanCtx`**（`trace.py:73-99`）一次调用记录的全部字段：

| 字段 | 含义 |
| --- | --- |
| `trace_id` | 一次请求的全局 ID，由 `contextvars` 透传 |
| `span_id` / `parent_span_id` | 构成树形结构（父 span 包子 span） |
| `kind` | 类型：`agent_node` / `llm` / `tool` / `retrieval` |
| `name` | 名称，如 `agent.supervisor`、`agent.literature_agent` |
| `input` / `output` | 入参/出参（经 `_safe()` 序列化） |
| `status` | `ok` / `error` |
| `error` | 异常字符串（仅失败时） |
| `tokens_in` / `tokens_out` / `cost_usd` | 成本三元组 |
| `latency_ms` | 耗时（毫秒） |

### 22.4 代码走读

**入口：`span()` 上下文管理器 — `trace.py:36-61`**。三个关键设计：

**① `contextvars` 自动透传**（`L43-49`）：

```python
trace_id = _current_trace.get() or uuid.uuid4().hex   # 没有就新建（根 span）
parent = _current_span.get()                          # 当前 span 自动成为父节点
span_id = uuid.uuid4().hex
token_t = _current_trace.set(trace_id)
token_s = _current_span.set(span_id)
```

**这就是嵌套自动成树的秘密**：进入 span 时把"当前 span"设成自己，`with` 块内新建的子 span 自然会把自己当父节点；退出时 `reset`（L59-60）恢复上一层。**在 async 环境下 `contextvars` 会随任务传播，跨 `await` 也不会串**。

**② 异常也要记录**（`L53-56`）：

```python
# span() 内部的 try / except / finally 结构（trace.py:50-61）
try:
    yield _sp                                   # ← 业务代码在此执行
    _sp.status = "ok"
except Exception as e:                          # ← 异常也要记录
    _sp.status = "error"
    _sp.error = f"{type(e).__name__}: {e}"
    raise                                       # ← 记录完继续往外抛，不改变原语义
finally:
    _sp.latency_ms = int((time.perf_counter() - started) * 1000)
    _current_trace.reset(token_t)
    _current_span.reset(token_s)
    _persist(_sp)                               # ← 无论成败都要落库
```

观测层**吞掉异常是反模式**：只记录、不处理、继续抛。

**③ fire-and-forget 落库**（`_persist` L102-121）：

```python
loop = asyncio.get_running_loop()
loop.create_task(_write())        # L119 不 await，立即返回
```

落库在 `finally` 里触发（L61），主流程完全不等待。没有事件循环时（脚本场景）静默跳过（L120-121）。

`_safe()`（L124-130）用 `json.loads(json.dumps(v, default=str))` 把任意对象洗成可 JSON 化的字典，失败则退成 `{"repr": ...}`——**保证永远能入库**。

### 22.5 调用关系

```
埋点位置（全项目共 4 处 with span(...)）
  supervisor.py:32      span("agent.supervisor", "agent_node")
  node_factory.py:30    span("agent.{spec.name}", "agent_node")
  planner.py:127        span("agent.planner", "agent_node")
  （LLM / 工具 / 检索 的 span 由上层节点包裹，未单独埋点）

查询侧
  api/observability/router.py
    GET /api/observability/traces            → list_traces()   trace.py:152
    GET /api/observability/traces/{trace_id} → get_trace()     trace.py:135
```

### 22.6 最小可复现骨架

```python
# 最小可复现：全链路 Trace（≈35 行）
import asyncio, time, uuid
from contextlib import contextmanager
from contextvars import ContextVar

_current_trace: ContextVar[str | None] = ContextVar("trace_id", default=None)
_current_span: ContextVar[str | None] = ContextVar("span_id", default=None)


@contextmanager
def span(name, kind, input_data=None, user_id=None):
    """① contextvars 透传 → 嵌套自动成树；② 异常只记录不吞；③ 落库 fire-and-forget"""
    trace_id = _current_trace.get() or uuid.uuid4().hex   # 无父则新建根
    parent = _current_span.get()                          # 当前 span 自动成为父节点
    span_id = uuid.uuid4().hex
    started = time.perf_counter()
    t_tok, s_tok = _current_trace.set(trace_id), _current_span.set(span_id)
    sp = {"trace_id": trace_id, "span_id": span_id, "parent_span_id": parent,
          "kind": kind, "name": name, "input": input_data, "user_id": user_id,
          "status": "ok", "output": None, "error": None, "latency_ms": 0}
    try:
        yield sp                                          # ← sp.set_io(output=...) 写回
        sp["status"] = "ok"
    except Exception as e:
        sp["status"] = "error"
        sp["error"] = f"{type(e).__name__}: {e}"
        raise                                             # ② 记录完继续抛，不吞异常
    finally:
        sp["latency_ms"] = int((time.perf_counter() - started) * 1000)
        _current_trace.reset(t_tok)                       # 恢复上一层，保证兄弟 span 平级
        _current_span.reset(s_tok)
        _persist(sp)                                      # ③ 不 await


def _persist(sp):
    async def _write():
        async with get_session_factory()() as db:
            db.add(TraceSpan(**sp))
            await db.commit()
    try:
        asyncio.get_running_loop().create_task(_write())  # fire-and-forget
    except RuntimeError:
        pass                                              # 无事件循环（脚本场景）跳过


def _safe(v):                                             # 任意对象 → 可 JSON 化
    try:
        return json.loads(json.dumps(v, ensure_ascii=False, default=str))
    except Exception:
        return {"repr": repr(v)}
```

**复现要点**：① 用 `ContextVar` 而非全局变量（async 下会串）；② `finally` 里 `reset` 保证兄弟节点平级；
③ 异常记录后**必须 `raise`**；④ 落库不 `await`，且要处理"没有事件循环"的脚本场景。

### 22.7 验证与预期输出

```powershell
envs\lunjiang\python.exe scripts/smoke_trace.py     # Span 嵌套 + 回放自检
```

起服务后通过管理端接口查看（需 admin 角色 token）：

```powershell
curl -H "Authorization: Bearer <admin_token>" http://127.0.0.1:8000/api/observability/traces?limit=5
# → [{"trace_id": "...", "spans": 7, "total_latency_ms": 4310, "total_cost_usd": 0.0}, ...]

curl -H "Authorization: Bearer <admin_token>" http://127.0.0.1:8000/api/observability/traces/<trace_id>
# → [{span_id, parent, kind, name, status, latency_ms, ...}, ...]  按 parent 即可还原成树
```

**→ 主动练习（改一行看变化）**：在任一被 `span()` 包住的调用点改 span 名（或再嵌套一层），重跑 22.7——观察 trace 树还原结果与 `/api/observability` 返回的层级变化。

### 22.8 面试点与坑

| 点 | 说明 |
| --- | --- |
| 面试点：为什么用 `contextvars` 而不是全局变量 | 全局变量在并发的 async 任务间会互相污染；`ContextVar` 是每个任务独立的视图，且与 `asyncio.Task` 的传播语义天然契合。 |
| 面试点：为什么落库用 fire-and-forget | Trace 是旁路观测，不应该增加主流程延迟。代价是"服务突然退出时最后几个 span 可能丢失"——这是一笔明确的取舍。 |
| 坑：`create_task` 的返回值没保存强引用 | `trace.py:119` 的 `loop.create_task(_write())` 没有把 task 存起来，asyncio 只持有弱引用，**理论上存在被 GC 的风险**。生产环境应维护一个全局 `set` 持有 pending task 并在完成后 `discard`。这是本实现的已知边界，值得在面试时主动点出。 |
| 坑：只埋了 Agent 节点，没埋 LLM 调用 | 当前 `kind` 实际只有 `agent_node` 在用。`tokens_in/out`、`cost_usd` 字段已预留但基本没人写，所以 `/metrics` 里的成本统计接近 0。**别声称"我们有完整的 token 成本追踪"**。 |
| 坑：Trace 依赖数据库 | `trace_enabled` 默认 true（`trace.py:33`），PG 挂掉时每次落库都会 `logger.exception`（L115）。虽然不影响主流程，但日志会被淹。排查问题时可临时关掉。 |

***

## 第 23 课 人机介入（interrupt）

> 🔗 复习锚点：第 10.3 课讲过「interrupt + Command(resume) 的机制」，本课拆**触发、持久化、恢复**三段实现（含 ③ Checkpointer 装配）。

### 23.1 问题与契约

有些决策**不该让 AI 自己做主**——比如"就按这个选题开题"。人机介入的契约：

| 项 | 内容 |
| --- | --- |
| 触发条件 | 专项 Agent 的 `spec.needs_confirmation == True`（**当前只有 `topic_agent`**，见 `specs.py:20`） |
| 挂起时 | 图在 `interrupt()` 处冻结，状态存 Checkpointer，SSE 下发 `interrupt` 事件 |
| 恢复时 | 前端调 `POST /api/agent/resume` 带 `feedback`，图从挂起点继续跑 |
| 硬约束 | **挂起可以跨进程重启**（状态持久化），且同一 `thread_id` 只能有一个挂起点 |

### 23.2 文件清单

| 文件 | 行数 | 在本能力中的职责 |
| --- | --- | --- |
| `services/agent/specialists/node_factory.py` | 91 | **触发点**：`interrupt()` 调用（L66-70） |
| `services/agent/engine.py` | 173 | **恢复侧**：`Command(resume=...)`（L75）+ 提取挂起载荷（L166-173） |
| `services/checkpoint/tiered.py` | 73 | **状态持久化**：Redis → PG → 内存 三级降级 |
| `services/agent/conversation_service.py` | 125 | 续跑编排 + 决策归档（L97-122） |
| `api/agent/router.py` | 65 | `POST /api/agent/resume` 接口（L55-64） |

### 23.3 核心数据结构

**interrupt 载荷**（`node_factory.py:66-70`）：

```python
{
    "type": "confirm",              # 交互类型
    "agent": spec.name,             # 哪个 Agent 在问
    "question": "请确认选题方案，或提出调整意见",
    "proposal": output,             # AI 的初步方案（前端直接渲染给用户看）
}
```

**Checkpointer 三级降级**（`tiered.py:33-73`）：

| 级 | 存储 | 特点 | 降级触发 |
| --- | --- | --- | --- |
| 一级 | Redis | 低延迟热存储 | 默认优先 |
| 二级 | PostgreSQL | 持久化，重启不丢 | Redis 连接/setup 失败 |
| 三级 | 进程内存 `InMemorySaver` | 零依赖 | 前两级都失败（**仅开发模式**） |

### 23.4 代码走读

**① 触发（`node_factory.py:65-79`）**：

```python
if spec.needs_confirmation:
    feedback = interrupt({...})        # L66  ← 图在此挂起，函数"暂停"在这一行
    if feedback:                       # L72  resume 后从这一行继续，feedback 即用户反馈
        final = await provider.chat([
            {"role": "system", "content": spec.system},
            {"role": "user", "content": f"原方案:\n{output}\n\n用户反馈:\n{feedback}\n\n"
                                        "请根据反馈输出最终选题结论（保留被认可部分）。"}],
            max_tokens=1200)
        output = final
```

**理解 `interrupt()` 的心智模型**：它不是"抛异常"，而是**让函数在这一行暂停**；当用户带反馈恢复时，`interrupt()` 的返回值就是那个 `feedback`，函数从下一行继续。

**② 挂起检测与载荷下发（`engine.py:94-105`）**：

```python
snap = await graph.aget_state(config)
if snap.next:                          # 还有未执行的节点 = 图被挂起了
    payload = _interrupt_payload(snap)
    if payload is not None:
        await hub.emit("interrupt", payload)      # 推给前端
else:
    await hub.emit("final", {...})                # 正常结束
```

`_interrupt_payload()`（L166-173）遍历 `snap.tasks[].interrupts[].value` 取第一个非空值。

**③ 恢复（`engine.py:74-75`）**：

```python
if resume is not None:
    invoke_input: Any = Command(resume=resume)    # 注意：resume 模式下 user_input 被忽略
```

**④ Checkpointer 装配（`engine.py:44-45`）**：`saver, tier = await TieredCheckpointer.create()`，然后 `build_graph(checkpointer=saver)`。**没有 checkpointer 就没有 interrupt**——这是最容易漏的一步。

**③ 状态持久化装配（`tiered.py:30-73`）——interrupt 能"挂起再恢复"的真正底座**：`TieredCheckpointer.create()` 按优先级**探测**可用 Checkpointer，返回 `(saver, tier)`，`saver` 实现 LangGraph 统一的 `BaseCheckpointSaver` 接口，对图编译完全透明。

```python
# services/checkpoint/tiered.py:30-73（精简）
@staticmethod
async def create() -> tuple[object, str]:
    # 一级 Redis：低延迟热存储
    try:
        from langgraph.checkpoint.redis.aio import AsyncRedisSaver
        saver = AsyncRedisSaver(get_value("storage","redis","url")); await saver.setup()
        return saver, "redis"
    except Exception: ...                              # 失败→降级，不抛
    # 二级 PostgreSQL：Redis 不可用时持久化
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg_pool import AsyncConnectionPool
        pool = AsyncConnectionPool(conninfo=..., kwargs={"autocommit": True})  # setup() 需非事务
        await pool.open(wait=True, timeout=10)
        saver = AsyncPostgresSaver(pool); await saver.setup()
        return saver, "postgres"
    except Exception: ...
    # 三级 Memory：都不可用→进程内兜底（仅开发）
    return InMemorySaver(), "memory"
```

> 三个设计要点：① **函数内 `import` 不是坏味道**（`tiered.py:8-9` 注释明示）——`langgraph.checkpoint.{redis,postgres}` 是可选依赖，"装了哪级用哪级"的降级语义靠它实现；② **二级用 `autocommit=True`**——`setup()` 里的 `CREATE INDEX CONCURRENTLY` 不允许在事务块内；③ `with_suppress_close`（`tiered.py:21-27`）在二级失败时尽力关池，避免残留 pending worker。**这正是 10.3 说的"Redis→PG→内存三级降级"的代码实锤**。

### 23.5 调用关系

```
触发
  topic_agent 节点执行完 → spec.needs_confirmation=True → interrupt(payload)
      → 图挂起 → TieredCheckpointer 存状态（Redis/PG/内存）
      → engine.produce() 检测到 snap.next → hub.emit("interrupt") → SSE → 前端弹确认框

恢复
  前端 POST /api/agent/resume {session_id, feedback}
      → api/agent/router.py:55 → conversation_service.stream_resume()
      → engine.run(resume=feedback) → graph.astream(Command(resume=feedback))
      → 从 interrupt 那行继续 → 综合反馈产出 final_output
      → conversation_service._archive_decision()  写 long_term(kind=decision) + structured.topic
```

### 23.6 最小可复现骨架

```python
# 最小可复现：人机介入（≈30 行）
from langgraph.types import interrupt, Command

# ① 图必须带 checkpointer 编译，否则 interrupt 无处挂起
graph = builder.compile(checkpointer=await TieredCheckpointer.create())


async def node(state):
    output = await run_agent(state)
    # ② 需要确认的 Agent 才挂起（由 spec.needs_confirmation 控制）
    if spec.needs_confirmation:
        feedback = interrupt({                      # ← 图在此挂起；恢复时返回 feedback
            "type": "confirm", "agent": spec.name,
            "question": "请确认选题方案，或提出调整意见",
            "proposal": output,                     # 前端直接渲染给用户
        })
        if feedback:                                # ③ 带用户反馈再跑一次 LLM 综合
            output = await provider.chat([
                {"role": "system", "content": spec.system},
                {"role": "user", "content":
                    f"原方案:\n{output}\n\n用户反馈:\n{feedback}\n\n"
                    "请根据反馈输出最终选题结论（保留被认可部分）。"}],
                max_tokens=1200)
    return {"final_output": output, "next_agent": "supervisor"}


# ④ 区分"挂起"与"结束"：snap.next 非空即被挂起
snap = await graph.aget_state({"configurable": {"thread_id": session_id}})
if snap.next:
    payload = next(i.value for t in snap.tasks for i in t.interrupts if i.value)
    await hub.emit("interrupt", payload)
else:
    await hub.emit("final", {"output": snap.values.get("final_output", "")})

# ⑤ 恢复：用 Command(resume=...) 而不是重新构造输入
async for _ in graph.astream(Command(resume=feedback), config=config, stream_mode="updates"):
    pass
```

**复现要点**：① **没有 checkpointer 就没有 interrupt**（最常见的新手坑）；② `interrupt()` 的返回值即用户反馈；
③ 恢复用 `Command(resume=...)`，且此时**不要再传 `user_input`**；④ 靠 `snap.next` 区分挂起/结束；
⑤ `thread_id` 必须前后一致，否则找不到挂起点。

### 23.7 验证与预期输出

```powershell
envs\lunjiang\python.exe scripts/smoke_graph.py     # 路由 + 中断恢复自检（含 checkpointer 装配）
```

端到端（需先起 uvicorn）：

```powershell
# 1) 发起会触发确认的请求（选题分析），观察 SSE 中的 interrupt 事件
curl -N -X POST http://127.0.0.1:8000/api/agent/chat ^
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"sess-0001\",\"message\":\"我是计算机专业，对推荐系统感兴趣，帮我分析选题\",\"project_id\":1}"
# → ... data: {"type":"interrupt","payload":{"type":"confirm","agent":"topic_agent",
#             "question":"请确认选题方案，或提出调整意见","proposal":"..."}}

# 2) 带反馈续跑
curl -N -X POST http://127.0.0.1:8000/api/agent/resume ^
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"sess-0001\",\"feedback\":\"方案二不错，但请把数据集限定在公开数据集上\",\"project_id\":1}"
# → ... data: {"type":"final","payload":{"output":"<综合反馈后的最终选题结论>"}}
```

> 注意 `session_id` 长度需 8–64（`api/agent/router.py:26`），两次调用必须**完全一致**。

**→ 主动练习（改一行看变化）**：把 `specs.py` 里 `topic_agent` 的 `needs_confirmation` 改成 `False`，重发一次选题分析——观察 SSE 里不再出现 `interrupt` 事件、图一口气跑完，体会**确认点 = 配置**的开关化设计。

### 23.8 面试点与坑

| 点 | 说明 |
| --- | --- |
| 面试点：为什么不用"轮询"或"第二轮对话"实现 | 轮询要前端不断发请求、状态自己维护；第二轮对话会丢失中断时的全部上下文。LangGraph 的 interrupt + checkpointer 是**把执行栈本身持久化**，恢复时局部变量都还在，语义上等价于"函数从那一行继续"。 |
| 面试点：三级 checkpointer 的意义 | Redis 快但可能丢，PG 稳但慢，内存零依赖但不持久。按优先级探测、**装了哪级就用哪级**，让同一份代码在"生产多副本"和"本地 demo"下都能跑。 |
| 坑：只有 `topic_agent` 会触发 | `specs.py` 里只有 `TOPIC_AGENT` 设了 `needs_confirmation=True`（L20），其余 5 个都没开。所以测试时**必须发选题类请求**才看得到 interrupt。 |
| 坑：`thread_id` 必须一致 | `engine.py:72` 用 `{"configurable": {"thread_id": session_id}}`，前后不一致会新建一条线，永远恢复不了。 |
| 坑：三级降级到内存时重启即丢 | `tiered.py:72` 会打 WARNING：`Checkpointer 三级降级生效: 进程内存（仅开发模式）`。**生产环境看到这条日志要立刻排查 Redis/PG**。 |
| 坑：PostgreSQL 那一级要求 `autocommit=True` | `tiered.py:53-57`，因为 `setup()` 里的 `CREATE INDEX CONCURRENTLY` 不允许在事务块内执行。 |

***

> 🏁 **里程碑 3**：⑥可观测 + ⑦人机介入——一次对话已可**全链路追踪**，也能在需要用户确认时**挂起等人、带着反馈续跑**。

***

## 第 24 课 流式输出（streaming）

> 🔗 复习锚点：第 12.1 课讲过「SSE 为什么要一条事件总线」，本课讲 EventHub 的**队列、微缓冲与生命周期**怎么实现。

### 24.1 问题与契约

| 项 | 内容 |
| --- | --- |
| 输入 | Agent 图各节点产出的 token 增量与生命周期事件 |
| 输出 | 单一有序的 `StreamEvent` 异步流 → SSE 推给前端 |
| 核心难点 | LangGraph 的 **token 流（细粒度）**与**节点事件（粗粒度）**天然时序交错，直接推会乱序 |
| 解决方案 | 一个 `asyncio.Queue` 串行化所有事件，天然保序 |

### 24.2 文件清单

| 文件 | 行数 | 职责 |
| --- | --- | --- |
| `services/streaming/hub.py` | 103 | `EventHub` 事件总线 + `StreamEvent` + `bind_hub`/`current_hub` |

### 24.3 核心数据结构

**`StreamEvent`**（`hub.py:20-30`）：

| 字段 | 含义 |
| --- | --- |
| `type` | 事件类型（见下表） |
| `payload` | 载荷（dict / str） |
| `node` | 产生事件的节点名 |
| `seq` | 单调递增序号（前端可据此检测丢帧） |

**事件类型全表**：

| type | 何时发 | 前端怎么用它 |
| --- | --- | --- |
| `node_start` | 节点开始 | 时间线新增一项「正在…」 |
| `node_end` | 节点结束 | 时间线标记完成 |
| `intent` | supervisor 分类完成 | 显示"识别为：文献检索" |
| `route` | 路由决策完成 | 显示派发给哪个 Agent |
| `plan` | Planner 产出计划 | 渲染步骤列表 |
| `step_event` | Planner 每步完成 | 逐步打勾 |
| `token` | LLM 流式增量 | **追加文本（打字机）** |
| `interrupt` | 图挂起 | 弹出确认框 |
| `final` | 全部完成 | 收尾，写短期记忆 |
| `error` | 异常 | 显示错误 |
| `done` | 流关闭 | 结束渲染 |

### 24.4 代码走读

**入口：`EventHub` — `hub.py:33`**。

**① token 微缓冲（`hub.py:49-55`）**——本项目最精巧的一处：

```python
async def emit_token(self, chunk: str, node=None) -> None:
    self._buffer.append(chunk)
    joined = "".join(self._buffer)
    if len(self._buffer) >= 4 or len(joined) >= 32:   # 攒 4 个 chunk 或 32 字符
        self._buffer.clear()
        await self.emit("token", joined, node=node)
```

**为什么要缓冲？** LLM 一个 token 可能只有 1~2 个字符（尤其中文），逐 token 推会给队列塞进上千条消息、前端重渲染上千次。攒够 4 个或 32 字符再推，**观感上仍是打字机，但事件量降了一个数量级**。配套的 `flush_tokens()`（L57-60）保证剩余内容不会丢。

**② 生命周期结束（`hub.py:62-66`）**：`close()` 先 `flush_tokens()` 再入队一个 `done` 事件——**`done` 是消费端的终止信号**。

**③ NullHub 兜底（`hub.py:78-93`）**：

```python
def current_hub():
    return _hub_var.get() or _NULL_HUB       # 没绑定 hub 时返回静默丢弃的假 hub
```

这让节点在**脚本、评测、单测**里可以脱离 SSE 直接调用，不用到处写 `if hub:`。这是很值得学的"空对象模式"。

**④ 上下文绑定（`hub.py:96-103`）**：`bind_hub(hub)` 是 `@contextmanager`，用 `ContextVar` 绑定，同一 asyncio 任务内的所有节点都能通过 `current_hub()` 拿到。

### 24.5 调用关系

```
生产端（各节点）
  supervisor.py:35/43/62/74   node_start / intent / route / node_end
  node_factory.py:33/82       node_start / node_end
  planner.py:129/143/160/167  node_start / plan / step_event / node_end
  supervisor.py:94            hub.emit_token()（闲聊直接流式作答）
        │
        ▼  全部进同一个 asyncio.Queue（保序）
  消费端
  engine.py:114  async for ev in hub.stream(): yield ev
  api/agent/router.py:50  yield ev.to_sse()   → SSE
  frontend/src/api.js     fetch + getReader() 逐行解析
```

### 24.6 最小可复现骨架

```python
# 最小可复现：SSE 事件总线（≈35 行）
import asyncio, json
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass
class StreamEvent:
    type: str
    payload=None
    node: str | None = None
    seq: int = 0

    def to_sse(self) -> str:
        data = {"type": self.type, "seq": self.seq, "node": self.node, "payload": self.payload}
        return f"data: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


class EventHub:
    """一个会话一个 Hub：生产者写入，SSE 消费；队列天然保序"""
    def __init__(self):
        self._q = asyncio.Queue()
        self._seq = 0
        self._buf: list[str] = []
        self._closed = False

    async def emit(self, type, payload=None, node=None):
        if self._closed:
            return
        self._seq += 1
        await self._q.put(StreamEvent(type, payload, node, self._seq))

    async def emit_token(self, chunk, node=None):
        """微缓冲：攒 4 个 chunk 或 32 字符再推，事件量降一个数量级，观感仍是打字机"""
        self._buf.append(chunk)
        joined = "".join(self._buf)
        if len(self._buf) >= 4 or len(joined) >= 32:
            self._buf.clear()
            await self.emit("token", joined, node=node)

    async def flush_tokens(self, node=None):
        if self._buf:
            await self.emit("token", "".join(self._buf), node=node)
            self._buf.clear()

    async def close(self):
        await self.flush_tokens()                 # 先冲掉残留，再发终止信号
        self._closed = True
        self._seq += 1
        await self._q.put(StreamEvent("done", seq=self._seq))

    async def stream(self):
        while True:
            ev = await self._q.get()
            yield ev                              # done 也要 yield，让消费端看到终止
            if ev.type == "done":
                return


class _NullHub:                                   # 空对象模式：脚本/单测里静默丢弃
    async def emit(self, *a, **k): ...
    async def emit_token(self, *a, **k): ...
    async def flush_tokens(self, *a, **k): ...
    async def close(self): ...


_hub_var: ContextVar = ContextVar("hub", default=None)

def current_hub():
    return _hub_var.get() or _NullHub()

@contextmanager
def bind_hub(hub):
    tok = _hub_var.set(hub)
    try:
        yield hub
    finally:
        _hub_var.reset(tok)
```

**复现要点**：① 所有事件走**同一个队列**（保序的关键）；② token 必须微缓冲；
③ `close()` 要**先 flush 再发 done**；④ `_NullHub` 空对象让节点脱离 SSE 也能跑。

### 24.7 验证与预期输出

```powershell
# 起服务后观察原始 SSE 帧（注意 -N 禁用缓冲）
curl -N -X POST http://127.0.0.1:8000/api/agent/chat ^
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"sess-0002\",\"message\":\"你好\",\"project_id\":1}"
```

预期帧序列（`type` 依次为 `node_start` → `intent` → `token`×N → `node_end` → `final` → `done`）：

```
data: {"type":"node_start","seq":1,"node":"supervisor","payload":{"agent":"supervisor","title":"主控Agent"}}
data: {"type":"intent","seq":2,"node":"supervisor","payload":{"intent":"chitchat","label":"闲聊/其他","confidence":0.95,"layer":"rule"}}
data: {"type":"token","seq":3,"node":"supervisor","payload":"你好！我是论匠…"}
data: {"type":"node_end","seq":4,"node":"supervisor","payload":{"agent":"supervisor","output_preview":"…"}}
data: {"type":"final","seq":5,"node":null,"payload":{"output":"…","intent":"chitchat","visited_agents":[]}}
data: {"type":"done","seq":6,"node":null,"payload":null}
```

**→ 主动练习（改一行看变化）**：把 token 微缓冲的 flush 字符数阈值调大一倍，用 24.7 的 curl 观察 SSE——帧数明显变少、每帧更长，体会**微缓冲 = 帧粒度与性能的折中**。

### 24.8 面试点与坑

| 点 | 说明 |
| --- | --- |
| 面试点：为什么用队列而不是直接 `yield` | LangGraph 的节点是并发/嵌套执行的，直接透传会乱序（token 可能跑到 `node_end` 后面）。单一队列 + 单一消费者 = 天然 FIFO 保序。 |
| 面试点：为什么不用 EventSource | `EventSource` 只支持 GET，而 `/api/agent/chat` 需要 POST 携带较长的 message 与 project_id。改用 `fetch + ReadableStream.getReader()` 逐行解析（见 `frontend/src/api.js`）。 |
| 坑：SSE 帧必须以 `\n\n` 结尾 | `to_sse()`（hub.py:30）格式是 `data: {json}\n\n`。少一个换行，前端就解析不出这一帧。 |
| 坑：反向代理会缓冲 SSE | `api/agent/router.py:21-22` 专门设了 `Cache-Control: no-cache` 与 `X-Accel-Buffering: no`。**Nginx 下没有 `X-Accel-Buffering: no` 会导致打字机变成"最后一次性弹出"**。 |
| 坑：`emit_token` 后必须 `flush_tokens` | 每个节点结束前都有 `await hub.flush_tokens(...)`（`node_factory.py:81`、`supervisor.py:99`），否则最后不足 32 字符的尾巴会丢。`hub.close()` 里也有一次兜底 flush。 |

***

## 第 25 课 编排中枢（agent）

> 🔗 复习锚点：第 10 课讲过「主从图怎么运转」，本课是**总装课**——把 ①~⑧ 八段骨架接进 state/builder/supervisor/engine 的真实代码里。

> 这一课把前八课**全部串起来**，是"能独立复现后端"的最后一环。读懂它 = 读懂整个系统。

### 25.1 问题与契约

| 项 | 内容 |
| --- | --- |
| 输入 | `session_id`、`user_input`、`user_id`、`user_role`、`project_id`、`resume`（可选） |
| 输出 | 异步的 `StreamEvent` 流（见第 24 课） |
| 职责 | ① 装配四层记忆 → ② 跑 LangGraph 图 → ③ 事件转 SSE → ④ 会话收尾维护记忆 |
| 硬约束 | **图编译必须是全局单例**（每次编译要重建 checkpointer，代价极高） |

入口函数：**`AgentEngine.run()` — `services/agent/engine.py:52`**。

### 25.2 文件清单

| 文件 | 行数 | 职责 |
| --- | --- | --- |
| `state.py` | 35 | `AgentState`（全图共享黑板，17 个字段） |
| `builder.py` | 41 | 图结构定义与编译 |
| `supervisor.py` | 100 | 主控节点：意图分类 + 路由 + 收尾 |
| `engine.py` | 173 | **运行入口**：图单例 + 记忆装配 + 生产者/消费者 + interrupt 提取 |
| `conversation_service.py` | 125 | 应用层编排：记忆双写、后台维护、决策归档 |
| `planner.py` | 227 | 复合任务 Plan-Execute-Replan |
| `specialists/specs.py` | 64 | 6 个专项 Agent 的**纯数据规格** |
| `specialists/node_factory.py` | 91 | 专项节点工厂（工具循环 + interrupt） |
| `specialists/schemas.py` | 49 | 注册表 → OpenAI function-calling schema |

### 25.3 核心数据结构

**`AgentState`**（`state.py:7-35`）——全图共享的"黑板"，节点往里写、下个节点读。**理解这 17 个字段就理解了整个数据流**：

| 分组 | 字段 | 谁写 | 谁读 |
| --- | --- | --- | --- |
| 会话身份 | `project_id` `session_id` `user_id` `user_role` | `engine.run()` | 工具治理（RBAC/限流） |
| 对话 | `messages`（`add_messages` 归约器） | LangGraph 自动 | 未直接使用 |
| 对话 | `user_input` | `engine.run()` | supervisor / 各节点 |
| 意图 | `intent` `intent_layer` | supervisor | 前端展示、可观测 |
| 调度 | `next_agent` | supervisor / 各节点 | `builder.route()` |
| 调度 | `visited_agents` | 各节点 | supervisor（判 hops） |
| 调度 | `agent_results` | 各节点 | 可观测 |
| 记忆 | `memory_brief` `history_text` | `engine._assemble_memory()` | 各节点（注入提示词） |
| 人机 | `interrupt_reason` `human_feedback` | **—（声明后从未使用）** | — |
| 产出 | `final_output` | 各节点 | `engine` 的 `final` 事件 |
| 产出 | `stop_reason` | supervisor | 可观测 |

> ⚠️ **已知死字段**：`interrupt_reason` 与 `human_feedback`（`state.py:30-31`）全项目检索**无任何读写**，
> 人机介入实际走 `interrupt()` 的返回值而非 State 字段（见第 23 课）。复现时可以不要这两个字段。

**`SpecialistSpec`**（`specs.py:5-12`）——专项 Agent 的"配置即代码"：

| 字段 | 含义 |
| --- | --- |
| `name` | 节点名（如 `topic_agent`） |
| `intent` | 负责的意图 |
| `title` | 中文名（前端时间线显示） |
| `system` | 系统提示词 |
| `tools` | **允许使用的工具子集**（最小权限原则） |
| `needs_confirmation` | 产出后是否人机确认 |

6 个专项与工具子集（`specs.py:15-63`）：

| Agent | 意图 | 工具子集 | 需确认 |
| --- | --- | --- | --- |
| `topic_agent` | topic_analysis | `topic_analysis`, `search_literature` | ✅ |
| `literature_agent` | literature_search | `rewrite_query`, `search_literature` | — |
| `writing_agent` | writing | `search_literature`, `generate_section` | — |
| `format_agent` | format_check | `check_format` | — |
| `plagiarism_agent` | plagiarism_reduce | `check_plagiarism` | — |
| `ai_detect_agent` | ai_detect | `detect_ai_text` | — |

### 25.4 代码走读

**① 图结构（`builder.py:19-41`）**——星型 + 回环：

```python
builder.add_edge(START, "supervisor")                       # L27
builder.add_conditional_edges("supervisor", route,
                              ["supervisor", "planner", *SPECIALISTS, END])  # L35-36
for name in SPECIALISTS:
    builder.add_edge(name, "supervisor")                    # L37-38  回环：回来交差
builder.add_edge("planner", "supervisor")                   # L39
```

`route()`（L29-33）的写法值得注意：**读 `state["next_agent"]`，而不是在路由函数里做判断**。
判断逻辑放在节点里（可观测、可测试），路由函数只做"翻译"——这是 LangGraph 的推荐范式。

**② 图单例（`engine.py:35-48`）**——标准双重检查锁：

```python
if cls._graph is None:
    async with cls._lock:
        if cls._graph is None:
            register_all()                          # L42-43  工具注册兜底（脚本入口）
            saver, tier = await TieredCheckpointer.create()
            cls._graph = build_graph(checkpointer=saver)
```

**③ 生产者 / 消费者（`engine.py:88-120`）**——本项目最需要理解的一段并发结构：

```python
async def produce() -> None:
    with bind_hub(hub):                             # L89  绑定 hub 到当前任务上下文
        try:
            async for _ in graph.astream(invoke_input, config=config, stream_mode="updates"):
                pass                                # L93  节点内部已直接向 hub emit
            snap = await graph.aget_state(config)
            if snap.next:
                await hub.emit("interrupt", _interrupt_payload(snap))   # L99
            else:
                await hub.emit("final", {...})      # L101
        except Exception as e:
            await hub.emit("error", {...})          # L108
        finally:
            await hub.close()                       # L110  ← 无论如何都要关流

task = asyncio.create_task(produce())               # L112
try:
    async for ev in hub.stream():                   # L114  消费端
        yield ev
finally:
    if not task.done():
        task.cancel()                               # L118  客户端断开要取消生产端
```

三个关键点：① `stream_mode="updates"` 但**循环体是空的**——事件不走 astream 的返回值，而是节点内部直接 `hub.emit()`（因为事件比状态更新更丰富）；② `finally: hub.close()` 保证异常时也发 `done`；③ 消费端退出时 `task.cancel()`，**防止客户端断开后生产协程泄漏**。

**④ 记忆装配（`engine.py:123-163`）**：四层全部包在 `try/except` 里，**任一层失败只 warning 不中断**（L135、L160）。这是刻意的降级设计——记忆是增强项，不能拖垮主流程。

**⑤ 会话收尾（`conversation_service.py:65-95`）**：

```
用户消息前置写入短期记忆        L73
      ↓
透传 engine.run() 事件流        L78-83
      ↓
助手终稿写入短期记忆            L87-88
      ↓
后台：窗口压缩 + 偏好沉淀        L93-95  （_fire = 不阻塞 SSE 收尾）
```

**⑥ Planner（`planner.py:121-171`）**：Plan → Execute（evidence 累积）→ Replan（失败重试一次，带"请输出更简短的版本"）→ 汇总 Markdown。`_coerce_params()`（L65-79）把 `top_k` 等数值参数强制 `int`，修的就是 LLM 输出 `"5"` 这类问题。

**⑦ 入口路由（`api/agent/router.py`）——只做两件事**：参数校验 + SSE 序列化。

```python
class ChatIn(BaseModel):                            # L25-28  参数契约（pydantic 自动校验）
    session_id: str = Field(min_length=8, max_length=64)
    message: str = Field(min_length=1, max_length=8000)
    project_id: int | None = None

@router.post("/chat", dependencies=[Depends(get_current_user)])
async def chat(body: ChatIn, user: User = Depends(...)):
    async def gen():
        async for ev in conversation_service.stream_chat(...):
            yield ev.to_sse()                       # StreamEvent → "data: {...}\n\n" 帧
    return StreamingResponse(gen(), media_type="text/event-stream", headers=_SSE_HEADERS)
```

三个点值得停一下：

1. **为什么业务不放在路由里**：路由只做"把 pydantic 校验好的参数交给 `conversation_service`，把返回的事件流逐条序列化成 SSE"。记忆双写/压缩/偏好这些编排全在下沉的应用层（见 25.4⑤），路由保持"哑"，好测好换；
2. **`stream_chat()` 返回的是 async generator**，`gen()` 只是逐条打上 `ev.to_sse()` 帧（格式见第 24.6 课）——这就是"打字机"的最后一公里；
3. **`_SSE_HEADERS` 三件头缺一不可**（L21-22）：`Cache-Control: no-cache` 防代理缓存；`X-Accel-Buffering: no` 防 Nginx 缓冲（踩坑详解见 24.8）；`Connection: keep-alive` 防连接被复用中断。少一个，前端就可能"最后一次性弹出"或断流。

`/api/agent/resume` 与 `/chat` 同构（L55-62），只是换成 `stream_resume(feedback=...)`——校验的字段多了 `feedback`、少了 `message`，其余完全一致。

### 25.5 调用关系

```
POST /api/agent/chat   api/agent/router.py:43
   │  只做参数校验 + SSE 序列化
   ▼
conversation_service.stream_chat()      conversation_service.py:65
   ├── short_term.append(user)                                    ← ②记忆
   ├── AgentEngine.run()                                          ← 编排
   │     ├── _assemble_memory()  → ②③④ 四层                      ← ②记忆
   │     ├── graph.astream()  with bind_hub(hub)                   ← ⑧流式
   │     │     ├── supervisor_node
   │     │     │     ├── intent_classifier.classify()              ← ①意图分类
   │     │     │     ├── is_complex_task() → route 到 planner
   │     │     │     └── INTENT_TO_AGENT[...] → route 到 specialist
   │     │     ├── specialist node (node_factory)
   │     │     │     ├── provider.chat_tools(... executor)         ← LLM function calling
   │     │     │     │     └── executor → tool_registry.call()      ← ⑤治理
   │     │     │     │           └── tools_impl.search_literature() ← ④工具
   │     │     │     │                 └── rag_pipeline.search()    ← ③检索
   │     │     │     └── interrupt() if spec.needs_confirmation     ← ⑦人机介入
   │     │     └── planner_node → tool_registry.call() × N
   │     └── hub.emit(final / interrupt)                            ← ⑧流式
   ├── short_term.append(assistant)                                ← ②记忆
   └── _fire(_compress_window / _learn_preference)                 ← ②记忆

旁路：span() 全程埋点 → trace_spans 表                              ← ⑥可观测
     api/middleware/audit.py  请求级审计
```

### 25.6 最小可复现骨架

下面这段是**整个后端核心的总装**。前八课的骨架拼起来就是它：

```python
# 最小可复现：编排中枢总装（≈60 行）—— 把 ①~⑧ 全部串起来
class AgentEngine:
    _graph = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_graph(cls):
        """① 图单例：双重检查锁。每次编译都要重建 checkpointer，绝不能每次请求都编译"""
        if cls._graph is None:
            async with cls._lock:
                if cls._graph is None:
                    register_all()                                    # 工具注册（幂等）
                    saver, tier = await TieredCheckpointer.create()   # 三级降级
                    cls._graph = build_graph(checkpointer=saver)      # 无 saver 就没有 interrupt
        return cls._graph

    @classmethod
    async def run(cls, *, session_id, user_input="", user_id, user_role="student",
                  project_id=None, resume=None, hub=None):
        hub = hub or EventHub()
        graph = await cls.get_graph()
        config = {"configurable": {"thread_id": session_id}}          # ← resume 靠它找回挂起点

        if resume is not None:                                        # ⑦ 人机续跑
            invoke_input = Command(resume=resume)                     # 此时忽略 user_input
        else:
            history_text, memory_brief = await cls._assemble_memory(  # ② 四层记忆装配
                project_id=project_id, session_id=session_id,
                user_id=user_id, user_input=user_input)
            invoke_input = {"user_input": user_input, "user_id": user_id,
                            "user_role": user_role, "project_id": project_id,
                            "session_id": session_id,
                            "history_text": history_text, "memory_brief": memory_brief,
                            "visited_agents": [], "agent_results": {}}

        async def produce():                                          # ⑧ 生产者：写 hub
            with bind_hub(hub):                                       # ContextVar 绑定
                try:
                    async for _ in graph.astream(invoke_input, config=config,
                                                 stream_mode="updates"):
                        pass                                          # 事件由节点直接 emit
                    snap = await graph.aget_state(config)
                    if snap.next:                                     # 被 interrupt 挂起
                        await hub.emit("interrupt", _interrupt_payload(snap))
                    else:
                        await hub.emit("final", {
                            "output": (snap.values or {}).get("final_output", ""),
                            "intent": (snap.values or {}).get("intent", ""),
                            "visited_agents": (snap.values or {}).get("visited_agents", [])})
                except Exception as e:
                    await hub.emit("error", {"message": str(e)})
                finally:
                    await hub.close()                                 # 必须关：发 done 终止流

        task = asyncio.create_task(produce())
        try:
            async for ev in hub.stream():                             # ⑧ 消费者：读 hub
                yield ev
        finally:
            if not task.done():
                task.cancel()                                         # 客户端断开 → 防协程泄漏


def build_graph(checkpointer=None):
    """星型 + 回环：supervisor 派活，specialist 回来交差，supervisor 决定收尾"""
    b = StateGraph(AgentState)
    b.add_node("supervisor", supervisor_node)
    for name, spec in SPECIALISTS.items():
        b.add_node(name, make_specialist_node(spec))
    b.add_node("planner", planner_node)
    b.add_edge(START, "supervisor")
    b.add_conditional_edges("supervisor",                             # 路由只做"翻译"
                            lambda s: s.get("next_agent") or END,
                            ["supervisor", "planner", *SPECIALISTS, END])
    for name in SPECIALISTS:
        b.add_edge(name, "supervisor")                                # 回环
    b.add_edge("planner", "supervisor")
    return b.compile(checkpointer=checkpointer)


async def supervisor_node(state):
    """主控：首次进入做分类路由，之后做收尾判定（visited 非空即已执行过）"""
    hub, visited = current_hub(), list(state.get("visited_agents", []))
    if not visited:                                                   # ① 意图分类
        ir = await intent_classifier.classify(state.get("user_input", ""))
        await hub.emit("intent", {"intent": ir.intent, "layer": ir.layer})
        if ir.intent == "chitchat":
            return {"final_output": await _chitchat_reply(state, hub),
                    "next_agent": "__end__", "stop_reason": "done"}
        nxt = "planner" if is_complex_task(state["user_input"], ir.intent) \
              else INTENT_TO_AGENT[ir.intent]
        await hub.emit("route", {"next": nxt})
        return {"intent": ir.intent, "intent_layer": ir.layer, "next_agent": nxt}
    # 收尾：hops 达上限则强制结束，防无限回环
    stop = "max_hops" if len(visited) >= _max_hops() else "done"
    return {"next_agent": "__end__", "stop_reason": stop}
```

**复现要点**：① 图必须单例；② `thread_id` 是 resume 的唯一凭证；③ 生产/消费者用 `finally` 双向清理（一边 `close()`、一边 `cancel()`）；④ 路由函数只翻译 `next_agent`，判断放在节点内；⑤ `max_hops`（默认 3，**`supervisor.py:21`**）是防止 Agent 无限回环的保险丝。

### 25.7 验证与预期输出

```powershell
envs\lunjiang\python.exe scripts/smoke_graph.py     # 图编译 + 路由 + 中断恢复自检
envs\lunjiang\python.exe scripts/smoke_api.py --topic   # 端到端（需 uvicorn 已启动）
```

观察一次完整对话的 SSE 事件序列（选题类会触发 interrupt）：

```
node_start(supervisor) → intent → route(topic_agent) → node_end
  → node_start(topic_agent) → [工具调用] → node_end
  → interrupt{type:confirm, agent:topic_agent, proposal:...}     ← 挂起
  ---- 用户反馈后 ----
  → node_start(topic_agent) → node_end → node_start(supervisor) → node_end → final → done
```

**→ 主动练习（改一行看变化）**：把 supervisor 的 `max_hops` 收紧为 1，再发一个复合任务——观察 `stop_reason=max_hops` 提前收尾；再把 `planner.is_complex_task` 的判定阈值调低，让普通任务也进 Planner，对比两条路径的事件流差异。

### 25.8 面试点与坑

| 点 | 说明 |
| --- | --- |
| 面试点：为什么用"主从"而不是多个 Agent 互相调用 | 互相调用会形成网状依赖，N 个 Agent 有 N² 条边，加一个 Agent 要改所有 Agent。星型结构下 supervisor 是唯一调度点，加 Agent 只需在 `SPECIALISTS` 里加一条数据。 |
| 面试点：`max_hops` 为什么必要 | LLM 决策有随机性，可能出现 A→B→A→B 死循环。`max_hops=3`（`supervisor.py:21`，配置 `agent.max_hops`）是硬性保险丝，到达后强制 `stop_reason="max_hops"` 收尾。 |
| 面试点：生产/消费者为什么都要 `finally` | 消费端断开（用户关页面）不清理生产协程 → 协程泄漏 + LLM 继续烧钱；生产端异常不 `close()` → 前端永远等不到 `done`，loading 转圈不停。**双向清理是流式系统的必备纪律**。 |
| 坑：死字段 `interrupt_reason` / `human_feedback` | `state.py:30-31` 声明后全项目无读写。人机介入实际通过 `interrupt()` 返回值传递，不走 State。 |
| 坑：`messages` 字段形同虚设 | 虽然用 `add_messages` 声明了，但代码里从未读写 `state["messages"]`，历史上下文走的是 `history_text`。**不要说"我们用 LangGraph 的消息流管理上下文"**。 |
| 坑：不带 `project_id` 时记忆读不到 | 见 18.8：`conversation_service` 用 `project_id or 0` 写，而 `engine` 用原始 `None` 读，key 不一致。 |
| 坑：工具注册有两处 | `main.py:65`（lifespan）与 `engine.py:42`（图单例内兜底）。因为在脚本/评测入口不经过 FastAPI lifespan，所以必须有兜底。**依赖 `register_all()` 的幂等性**。 |

***

> 🏁 **里程碑 4**：⑧流式 + 编排中枢总装完成。**第 0 课地基 + 九段模块骨架已全部就位**——理论上你已能在空白工程里拼出一个可运行的多智能体后端。第三部分开始逐项验收。

***

# 第三部分 · 从零复现实操

> 前两部分讲"怎么理解"，这一部分讲"**怎么在自己机器上跑起来并证明它真的能用**"。
> 假设你拿到的是一台**只有 Python 和 Git 的裸机**，按 26 → 27 → 28 的顺序执行即可。

## 第 26 课 环境准备：从裸机到全绿

### 26.1 依赖全景：五层地基

任何一层缺失，症状都不同。**先记住这张表，出问题时能立刻定位是哪一层**：

| 层 | 组件 | 端口 | 缺失/未启动的后果 |
| --- | --- | --- | --- |
| 1 | PostgreSQL 16 + pgvector | 5433 | **后端直接启动失败**（lifespan 里建表） |
| 2 | Redis | 6379 | 限流/熔断/短期记忆/分布式锁 全部降级，功能"看似正常但无记忆" |
| 3 | Ollama + bge-m3 | 11434 | 向量化失败 → RAG 检索为空 |
| 4 | Python 3.11 虚拟环境 | — | 无法运行 |
| 5 | `.env` + `configs/settings.yaml` | — | 连错库 / 连错底座 |

> 层 1~3 是**外部系统服务**，必须先于应用启动。这是新手最高频的卡点。

### 26.2 分步操作

**Step 0 · 启动基础设施（顺序：PG → Redis → Ollama）**

```powershell
# 1) PostgreSQL（本项目用独立实例，端口 5433）
D:\Develop\DB\PostgreSQL16\Library\bin\pg_ctl -D D:\Develop\DB\PostgreSQL16\data start

# 2) Redis
redis-server                      # 或 net start Redis（已注册为服务时）

# 3) Ollama（新开一个窗口常驻）
ollama serve
ollama pull bge-m3                # 嵌入模型，1024 维
```

连通性自检（三个端口都应看到 `LISTENING`）：

```powershell
netstat -ano | findstr ":5433 :6379 :11434"
```

**Step 1 · 建 Python 环境**

```powershell
conda create -p envs\lunjiang python=3.11 -y
conda run -p envs\lunjiang pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**Step 2 · 配置**

```powershell
copy .env.example .env             # 修改 PG / Redis 连接信息与 AGNES_API_KEY
```

关键配置项（完整表见 16.7）：

| 配置键 | 默认 | 说明 |
| --- | --- | --- |
| `llm.default_provider` | `agnes` | 对话底座（云端 agnes-2.5-flash） |
| `llm.embedding_provider` | `ollama` | 嵌入底座（本地 bge-m3），**与对话解耦** |
| `storage.postgres.sync_dsn` | — | PG 连接串（注意端口 5433） |
| `storage.redis.url` | — | Redis 连接串 |

**Step 3 · 建库与扩展**（脚本自动完成，见 `check_env.py:63-80`）

`check_env.py` 会连到 `postgres` 系统库，若目标库不存在则 `CREATE DATABASE`，再 `CREATE EXTENSION IF NOT EXISTS vector`。**无需手工执行 SQL**。

**Step 4 · 自检**

```powershell
envs\lunjiang\python.exe scripts/check_env.py
```

预期输出（4 项全 PASS）：

```
== 论匠环境检查（LLM provider: agnes）==

[PASS] Ollama 对话模型 | qwen3:4b-ctx4096 -> 'OK'
[PASS] Ollama Embedding | bge-m3 向量维度=1024
[PASS] Redis | PING=True, SET/GET=ok
[PASS] PostgreSQL 连接 | 数据库 lunjiang 已存在
[PASS] pgvector 扩展 | vector 类型可用

结果: 5/5 通过
```

> ⚠️ **默认 provider 是 `agnes`（云端）时，"Ollama 对话模型" 项会 404**——因为 `check_env.py` 按 Ollama 的
> `/api/generate` 格式探测（L36）。这**属预期行为**，不是环境坏了。要全本地验证需先把
> `configs/settings.yaml` 的 `llm.default_provider` 临时改成 `ollama`。详见附录三 Q3。

### 26.3 环境失败的快速定位

| 症状 | 最可能的原因 | 去哪查 |
| --- | --- | --- |
| `ConnectionRefusedError: [WinError 1225]` | PG 或 Redis 没起 | 附录三 Q2 |
| `Ollama Embedding` FAIL | 没拉 `bge-m3`，或 `ollama serve` 没开 | 26.2 Step 0 |
| `pgvector 扩展` FAIL | 无 superuser 权限建扩展 | 手动 `CREATE EXTENSION vector` |
| 起服务后检索永远返回空 | 语料没入库 | 第 27 课 Step 3 |

***

## 第 27 课 运行启动与端到端自检

### 27.1 启动顺序（以及为什么）

```
① PostgreSQL ──┐
② Redis ───────┼── 必须先起：main.py lifespan 会立即建表（main.py:60-62）
③ Ollama ─────┘   连不上就 ConnectionRefusedError

④ 语料入库 ─────── 必须先做：否则 RAG 检索永远为空（不是报错，是"安静地查不到"）

⑤ uvicorn ──────── 后端，启动期建表 + 注册工具 + 后台预热
⑥ npm run dev ──── 前端，/api 代理到 8000
```

### 27.2 启动命令

```powershell
# 语料入库（首次或换 embedding 模型后必须做；--force 强制重建）
envs\lunjiang\python.exe scripts/ingest_corpus.py

# 后端（窗口 1）
envs\lunjiang\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000

# 前端（窗口 2，PowerShell 用 ; 分隔，不要用 &&）
cd frontend; npm install; npm run dev
```

浏览器打开 <http://localhost:5173>：注册 → 登录 → 新建项目 → 发起对话。

### 27.3 启动期到底做了什么（`main.py:57-72`）

理解 lifespan 这五步，能解释 80% 的"启动后为什么这样"：

| # | 动作 | 位置 | 说明 |
| --- | --- | --- | --- |
| 1 | `Base.metadata.create_all` 建表 | `main.py:60-62` | 开发期直接建表；**生产应改用 Alembic** |
| 2 | `register_all()` 注册 14 个治理工具 | `main.py:64-65` | 幂等，重复调用安全 |
| 3 | `create_task(_warmup_bm25())` | `main.py:68` | 后台重建 BM25 索引，不阻塞就绪 |
| 4 | `create_task(_warmup_reranker())` | `main.py:69` | 后台加载交叉编码器（CPU 首载 10~60s） |
| 5 | Windows 事件循环策略修正 | `main.py:28-30` | psycopg 需要 Selector 循环，Windows 默认 Proactor 不支持 |

> **第 3、4 步是"预热"而非"阻塞"**：所以服务显示就绪后，**第一次检索仍可能较慢**（索引/模型还没热）。
> 想确认是否预热完成，看日志里有没有 `预热完成：BM25 索引 N 篇文档` 与 `预热完成：交叉编码器已加载`。

### 27.4 端到端自检清单

按顺序跑，全部通过 = 环境 + 核心功能都正常：

| # | 命令 | 验证什么 | 通过标准 |
| --- | --- | --- | --- |
| 1 | `scripts/check_env.py` | 五层地基 | `结果: 5/5 通过`（agnes 下对话项 404 属预期） |
| 2 | `scripts/ingest_corpus.py` | 语料入库 | 日志显示入库块数（约 1376 块） |
| 3 | `scripts/smoke_rag.py` | ③ 检索 | 各查询返回非空 results |
| 4 | `scripts/smoke_memory.py` | ② 记忆 | 四层读写 + 压缩比 ≤0.30 |
| 5 | `scripts/smoke_governance.py` | ⑤ 治理 | 治理栈 9 项通过 |
| 6 | `scripts/smoke_trace.py` | ⑥ 可观测 | Span 嵌套与回放正常 |
| 7 | `scripts/smoke_graph.py` | ⑦ 人机介入 + 编排 | 图编译 + 路由 + 中断恢复 |
| 8 | `scripts/smoke_api.py --topic` | 端到端（需 uvicorn） | 注册→登录→建项目→对话全链路 |
| 9 | `evals/harness.py` | 质量指标 | 意图准确率 / Recall@5 / 压缩比 |
| 10 | `-m pytest tests/ -q` | 离线单测 | 59 用例通过，无外部依赖 |

### 27.5 停止与清理

```powershell
D:\Develop\DB\PostgreSQL16\Library\bin\pg_ctl -D D:\Develop\DB\PostgreSQL16\data stop
```

***

## 第 28 课 八大能力复现清单

### 28.1 每个能力的"最小证明"

判断一个能力是否真的跑通，**不看代码看输出**。这张表就是验收标准：

| 能力 | 最小验证方式 | 通过标准（你应该看到） |
| --- | --- | --- |
| ① 意图分类 | 第 17.7 课的三条命令 | 三行 `layer=rule`，且「参考文献格式对不对」判为 `format_check` |
| ② 记忆 | `smoke_memory.py` + 同一 session 连问两句 | 第二句的回答引用了第一句的内容；压缩比 ≤0.30 |
| ③ 检索 | `smoke_rag.py` + 第 19.7 课改写验证 | `results` 非空；`strategy` 字段按查询难度在 `skip`/`llm` 间切换 |
| ④ 工具 | 第 20.7 课注册数验证 | `已注册工具数: 14`，重复 `register_all()` 数量不变 |
| ⑤ 治理 | `smoke_governance.py` + 第 21.7 课熔断验证 | 连续失败 5 次后状态 `OPEN`，`before_call()` 抛 `CircuitOpenError` |
| ⑥ 可观测 | `smoke_trace.py` + `/api/observability/traces` | 返回带 `parent_span_id` 的 Span 列表，可按 parent 还原成树 |
| ⑦ 人机介入 | 第 23.7 课两条 curl | 第一条 SSE 出现 `type:"interrupt"`；带 feedback 续跑后出现 `type:"final"` |
| ⑧ 流式 | 第 24.7 课 curl -N | 帧序列 `node_start → intent → token×N → node_end → final → done` |

### 28.2 后端核心模块复现顺序（照着写代码用）

如果你要**从零把后端核心写出来**（毕设 / 作品集），按下面 13 步推进。每一步都标注了**骨架代码在第几课**——照抄即可跑通：

| 步 | 产出 | 骨架出处 | 完成标志 |
| --- | --- | --- | --- |
| 1 | 配置层 `get_settings()` / `get_value()` | **第 0 课** + 第 3 课 | 能从 YAML 按路径取值 |
| 2 | FastAPI 骨架 + `/health` + lifespan | 第 3 课 + 27.3 | 服务能起，启动期建表 |
| 3 | PG + Redis 连接 + ORM 模型 | **第 0 课** + 第 4 课 | `memory_items` / `projects` / `trace_spans` 建出来 |
| 4 | JWT + bcrypt 认证 | 第 5 课 | 注册/登录闭环 |
| 5 | `LLMProvider`（chat / chat_stream / embed / chat_tools） | 第 6 课 | 四个方法都能通 |
| 6 | ① 意图分类器 | **17.6** | 三类样本分别命中 rule/vector/llm |
| 7 | ③ RAG：入库 → 多路召回 → RRF → 精排 | **19.6** | Recall@5 ≥ 0.90 |
| 8 | ② 记忆四层 + 压缩 | **18.6** | 压缩比 ≤0.30，四层各能读写 |
| 9 | ④ 工具实现 + 注册 | **20.6** | 14 个工具注册成功且可直调 |
| 10 | ⑤ 治理栈六步流水线 | **21.6** | RBAC/限流/熔断/重试 各能单独验证 |
| 11 | ⑧ EventHub + SSE | **24.6** | 帧序列符合 24.7 的预期 |
| 12 | ⑥ Trace span | **22.6** | 嵌套 span 能还原成树 |
| 13 | 编排中枢：state + builder + supervisor + specialists + engine | **25.6** | 图编译 + 路由 + ⑦ interrupt 恢复（**23.6**） |

> 步骤 6~13 的**骨架代码是本复现路径的核心资产**。建议：先照抄跑通 → 再回头对照 N.4 的真实实现补齐
> 降级、日志、配置等工程细节 → 最后用 28.1 的清单逐项验收。

### 28.3 什么算"复现成功"

三条硬标准：

1. **28.1 的八项验收全部通过**（不是"代码写完了"，是"输出符合预期"）；
2. **能在空白机器上从 Step 0 重跑一遍**（26 课）；
3. **能回答"为什么"**：任意挑一个模块，说清它的输入/输出、上下游、以及至少一个设计取舍（N.8 的面试点）。

达到这三条，你就不是在"抄一个项目"，而是**真的掌握了这套架构**。

***

## 附录 关键类与调用链速查

### 一次对话的调用链（对应文件）

```
api/agent/router.py → conversation_service.stream_chat()/stream_resume()   # services/agent/conversation_service.py（编排：记忆双写/压缩/偏好/归档）
    → AgentEngine.run()
    → services/memory/（四层组装）
    → services/agent/engine.py：绑定 EventHub → 跑 LangGraph 图
        → supervisor_node（意图分类：services/classifier/intent.py；复杂任务 → planner）
        → specialists/xx 节点  │  planner_node（services/agent/planner.py）
            → services/governance/tool_registry.py: ToolRegistry.call()
                → rate_limiter / circuit_breaker / retry / dist_lock
                → tools_impl.search_literature()  │  academic_tools.*  │  tools_impl.generate_artifact()
                    → services/rag/pipeline.py: RagPipeline.search()
                        → query_rewrite → retriever(dense+sparse+相邻窗口, RRF) → reranker
                          （项目知识库路/保底/降噪，知识库入库见 services/rag/ingest/pipeline.py）
    → EventHub → SSE
services/observability/trace.py 全程 span 记录；api/middleware/audit.py 后台审计
```

### 类/函数速查表

| 你想找……       | 去哪里                                                                                |
| ----------- | ---------------------------------------------------------------------------------- |
| 全局配置        | `infrastructure/config.py` `get_settings()`                                        |
| LLM 调用      | `services/llm/provider.py` `LLMProvider`                                           |
| 向量化         | `LLMProvider.embed()`（bge-m3，1024 维；底座由 `llm.embedding_provider` 指定）               |
| 短期记忆        | `services/memory/short_term.py` `ShortTermMemory`                                  |
| 记忆压缩        | `services/memory/compressor.py` `compress_window_if_needed()`                      |
| RAG 入口      | `services/rag/pipeline.py` `RagPipeline.search()`                                  |
| 多路召回 + RRF  | `services/rag/retriever.py` `HybridRetriever.rrf_fuse()` / `sibling_search()`      |
| 知识库入库       | `services/rag/ingest/pipeline.py` `ingest_document()` / `parsers.parse_document()` |
| 意图分类        | `services/classifier/intent.py` `IntentClassifier.classify()`                      |
| 图构建         | `services/agent/builder.py` `build_graph()`                                        |
| 主控节点        | `services/agent/supervisor.py` `supervisor_node()`                                 |
| 对话编排        | `services/agent/conversation_service.py` `ConversationService.stream_chat()`（路由只做校验+SSE，编排下沉于此） |
| 专项 Agent 定义 | `services/agent/specialists/specs.py` `SpecialistSpec` / `SPECIALISTS`             |
| 规划器         | `services/agent/planner.py` `planner_node()` / `is_complex_task()`                 |
| 结构化产物       | `services/governance/artifacts.py` `generate_artifact()`                            |
| 工具治理入口      | `services/governance/tool_registry.py` `ToolRegistry.call()`                       |
| 工具实现        | `services/governance/tools_impl.py` `register_all()` + `academic_tools.py`         |
| 流式事件        | `services/streaming/hub.py` `EventHub`                                             |
| 检查点（中断恢复）   | `services/checkpoint/tiered.py` `TieredCheckpointer`                               |
| Trace       | `services/observability/trace.py` `span()`                                         |
| 语料入库        | `services/rag/ingest/corpus_loader.py` `ingest_corpus()`                           |
| 评测          | `evals/harness.py` / `evals/ab.py` / `evals/regression.py`                         |
| 项目 CRUD      | `api/projects/router.py`（列表/详情/改/删；`get_owned_project` 保证只能动自己的项目） |
| 项目根路径/数据目录 | `infrastructure/paths.py`（项目内路径基准点，上传目录等由此派生） |

### 环境检查 5 项对应关系

`scripts/check_env.py` 的 5 个检查项 = 5 个"地基"：

| 检查项              | 对应第几课  | 失败时看哪里                                           |
| ---------------- | ------ | ------------------------------------------------ |
| Ollama 对话模型      | 课 6    | Ollama 是否 `ollama serve`；`num_ctx` OOM（见**附录三 Q1**） |
| Ollama Embedding | 课 8    | 是否 `ollama pull bge-m3`                          |
| Redis            | 课 4/11 | 服务是否在 6379；只读内存                                  |
| PostgreSQL 连接    | 课 4    | 5433 实例启停命令（见 README）                            |
| pgvector 扩展      | 课 4    | 是否 `CREATE EXTENSION vector`（脚本自动建）              |

***

## 附录二 模块依赖矩阵

排查问题时用它定位"哪一层挂了会连累谁"；重构时用它评估改动的影响面。

| 模块 | Redis | PG | pgvector | LLM/嵌入 | 交叉编码器 | 内部依赖 | 被谁依赖 |
| --- | :-: | :-: | :-: | :-: | :-: | --- | --- |
| `classifier/intent.py` | | | | ✅ | | `llm.provider` | `agent/supervisor.py` |
| `memory/short_term.py` | ✅ | | | | | `redis_client`, `config` | `engine`, `conversation_service` |
| `memory/structured.py` | | ✅ | | | | `models.project` | `engine` |
| `memory/long_term.py` | | ✅ | ✅ | ✅ | | `models.memory`, `llm.provider` | `engine`, `compressor` |
| `memory/preference.py` | | ✅ | | ✅ | | `models.memory` | `engine` |
| `memory/compressor.py` | ✅ | ✅ | ✅ | ✅ | | `short_term`, `long_term` | `conversation_service` |
| `rag/retriever.py` | | ✅ | ✅ | ✅ | | `models.memory` | `rag/pipeline`, `tools_impl` |
| `rag/reranker.py` | | | | | ✅ | `config` | `rag/pipeline` |
| `rag/query_rewrite.py` | | | | ✅ | | `llm.provider`, jieba | `rag/pipeline` |
| `rag/pipeline.py` | | ✅ | ✅ | ✅ | ✅ | 上面三个 | `tools_impl` |
| `rag/ingest/*` | | ✅ | ✅ | ✅ | | `parsers`, `models.memory` | 入库脚本 |
| `governance/tool_registry.py` | ✅ | ✅ 审计 | | | | 下面六个 + `rbac` | `node_factory`, `planner` |
| `governance/rate_limiter.py` | ✅ | | | | | — | `tool_registry` |
| `governance/circuit_breaker.py` | ✅ | | | | | `config` | `tool_registry` |
| `governance/retry.py` | | | | | | `config` | `tool_registry` |
| `governance/dist_lock.py` | ✅ | | | | | `config` | `tool_registry` |
| `governance/skill.py` | ✅ | ✅ | | ✅ | | `models.skill` | `tool_registry` |
| `governance/tools_impl.py` | | ✅ | ✅ | ✅ | | `rag/pipeline`, `artifacts` | `tool_registry` |
| `observability/trace.py` | | ✅ | | | | `models.trace` | `supervisor`, `node_factory`, `planner` |
| `streaming/hub.py` | | | | | | — | 全部节点 + `engine` |
| `checkpoint/tiered.py` | ✅ | ✅ | | | | `config` | `engine` |
| `agent/state.py` | | | | | | — | 全图 |
| `agent/supervisor.py` | | | | ✅ | | `classifier`, `planner`, `trace`, `hub` | `builder` |
| `agent/specialists/*` | | ✅ | ✅ | ✅ | | `tool_registry`, `trace`, `hub` | `builder` |
| `agent/planner.py` | | ✅ | ✅ | ✅ | | `tool_registry`, `trace`, `hub` | `builder` |
| `agent/engine.py` | ✅ | ✅ | | | | 记忆四层, `builder`, `checkpoint`, `hub` | `conversation_service` |
| `agent/conversation_service.py` | ✅ | ✅ | | | | `engine`, 记忆四层 | `api/agent/router.py` |

**读法**：`engine.py` 是依赖面最广的模块（记忆四层 + 图 + checkpoint + hub），
所以它也是**最容易被"某一层静默降级"影响、却又看不出来**的地方——排查时优先看它的日志。

***

## 附录三 常见问题 FAQ

> ⚠️ **变更标注（2026-09-02）**：旧版附录中「`num_ctx` OOM（见 FAQ Q1）」指向了不存在的小节，本附录即为补全。

**Q1 · Ollama 返回 500（KV Cache OOM）怎么办？**

本地小显存/小内存机器跑 `qwen3:4b` 时，单请求 `num_ctx` 过大会撑爆 KV Cache。而 Ollama 的 `/v1`
兼容端点**不认请求级 `options`**，必须用 Modelfile 固化参数：

```powershell
ollama pull qwen3:4b
ollama create qwen3:4b-ctx4096 -f configs\ollama\Modelfile.qwen3-ctx4096
# 然后把 configs/settings.yaml 的 llm.default_provider 改为 ollama、chat_model 改为 qwen3:4b-ctx4096
```

当前默认对话底座是云端 `agnes`，只有本地回退场景才会遇到。详见 `docs/OPTIMIZATION_ROUND2.md`。

**Q2 · 后端启动报 `ConnectionRefusedError: [WinError 1225]`？**

`main.py` 的 lifespan 会**立即**连 PostgreSQL 建表（L60-62），PG/Redis 没起就直接失败。
按 26.2 Step 0 的顺序启动依赖后重启后端，并用 `netstat -ano | findstr ":5433 :6379 :11434"` 确认监听。

**Q3 · `check_env.py` 报 404，是环境坏了么？**

不是。该脚本按 **Ollama `/api/generate`** 格式探测（`check_env.py:36`），而默认 `default_provider`
是 OpenAI 兼容的云端 `agnes`，端点不同必然 404。两种处理方式：

1. 以 `netstat` 端口检查 + `scripts/` 其余冒烟脚本为准；
2. 需要全本地验证时，临时把 `settings.yaml` 的 `llm.default_provider` 改成 `ollama` 再跑。

**Q4 · `pg_ctl start` 提示 another server might be running 并卡住？**

异常退出残留了 `postmaster.pid`。确认 5433 无监听、无 postgres 进程后删除
`D:\Develop\DB\PostgreSQL16\data\postmaster.pid` 再启动。

**Q5 · 端口 5433 / 6379 被占用？**

释放端口，或同步修改 `.env` 与 `postgresql.conf` 保持一致。

**Q6 · 服务起来了但检索永远返回空？**

两个最常见原因：① 没跑 `scripts/ingest_corpus.py` 入库；② BM25/精排还在后台预热（见 27.3 第 3、4 步）。
看日志里有没有 `预热完成：BM25 索引 N 篇文档`。

**Q7 · 不带 `project_id` 发对话时，上下文记不住？**

已知的实现不一致：写入侧用 `project_id or 0`、读取侧用原始 `None`，Redis key 分别是
`chat:0:{sid}` 与 `chat:None:{sid}`。详见 18.8。**临时规避：始终传 `project_id`。**

**Q8 · 第一次检索特别慢（几十秒）？**

交叉编码器 `bge-reranker-base` 首次加载需 10~60s（CPU）。`main.py:69` 已在后台预热，
但若在预热完成前就发请求，会在首次精排时阻塞加载。等日志出现 `预热完成：交叉编码器已加载` 即可。

**Q9 · 知识库上传返回 `status=failed`？**

扫描版 PDF 无可提取文本，本期不支持 OCR。请上传含文本层的 PDF 或 DOCX/TXT/MD；
也可调 `rag.knowledge.min_text_chars`（默认 30）放宽判定。

**Q10 · 熔断一直处于 OPEN 恢复不了？**

`recovery_timeout` 默认 30s，到期进入 `HALF_OPEN`，需要**连续 2 次成功**才回 `CLOSED`
（`circuit_breaker.py:68-73`）。若下游仍不稳定会立刻回到 OPEN。调试时可直接删除
Redis 的 `breaker:{name}` 键重置。

***

## 附录四 设计决策回溯：被否决的方案与代价

> 设计思路的精华不在"选了什么"，而在"**否决了什么、接受了什么代价**"。本附录把全文散落的取舍收拢成一张横向对照，按决策链排列。面试被问"为什么不用 X"时，答案就在这里。

### 决策 1 · 编排：LangGraph 主从图，而非手写 if/else 循环

| 项 | 内容 |
| --- | --- |
| 要解决的问题 | 多智能体协作需要"共享状态 + 受控跳转 + 可持久化的中断"，手写循环很快演化成状态机泥潭 |
| 选了什么 | LangGraph 主从图：节点写 `AgentState`，`route()` 读状态决定跳转（第 10/25 课） |
| 被否决 | ① 手写 `while` + 函数分派：第 6.4 的 FC 循环能干单轮的活，但挂起/恢复、状态回滚要自己造；② CrewAI/AutoGen：黑盒编排，持久化与人机介入定制空间小 |
| 接受的代价 | 引入框架概念成本；`interrupt` 必须配 Checkpointer 才能用（第 23.6 骨架坑 ①）；调试要看图执行轨迹而非堆栈 |
| 何时该换 | 只有单一 Agent、无人工确认环节时——手写循环更轻（本项目第 6 课就是那个"轻版本"） |

### 决策 2 · 检索：RRF 融合 + 交叉编码器精排，而非纯向量召回

| 项 | 内容 |
| --- | --- |
| 要解决的问题 | 纯向量召回对"精确术语/编号"类查询弱，且"检索得分高"≠"对生成有用" |
| 选了什么 | 稠密 + BM25 + 相邻窗口多路召回 → RRF 融合（唯一跨路可比分）→ 交叉编码器精排 + 噪声惩罚（第 8/19 课） |
| 被否决 | ① 纯向量 top_k：BM25 命中直接丢失；② 简单加权融合：稠密分与 BM25 分**量纲不可比**，权重无意义——RRF 用排名而非分数回避了归一化难题 |
| 接受的代价 | 链路变长、延迟上升；交叉编码器首次加载 10~60s（附录三 Q8）；噪声三态阈值（×1.0/×0.995/×0.982）是经验值，需按语料调 |
| 何时该换 | 语料小且查询短时，纯向量足够；若换大模型长上下文（直接塞全文），整个检索层可简化 |

### 决策 3 · 记忆：四层分工，而非"一个聊天记录数组"

| 项 | 内容 |
| --- | --- |
| 要解决的问题 | 单数组上下文：窗口一满要么截断丢事实、要么超预算；"用户偏好"与"对话原文"生命周期完全不同 |
| 选了什么 | 短期（Redis 窗口）→ 结构化（PG JSON）→ 长期语义（pgvector）→ 偏好（固定 importance 排序），外加自动压缩（第 7/18 课） |
| 被否决 | ① 全量塞上下文：成本随轮次线性涨；② 只做摘要丢弃原文：细节不可追溯；③ 向量库存一切：偏好这类"精确取"用向量检索反而是绕路 |
| 接受的代价 | 四层 = 四套读写路径与故障面（`engine._assemble_memory` 每层 try/except 降级，25.4 ④）；压缩有信息损耗（压缩比 ≤0.30 为验收线） |
| 何时该换 | 单轮工具型助手不需要四层；本项目第 7.1 的"四层动机"即裁剪依据 |

### 决策 4 · 持久化：三级 Checkpointer（Redis→PG→内存），而非单一存储

| 项 | 内容 |
| --- | --- |
| 要解决的问题 | `interrupt` 挂起的图状态必须**跨请求存活**，但部署环境（本地开发/单机生产/多实例）存储能力不同 |
| 选了什么 | `TieredCheckpointer.create()` 启动时逐级探测，返回统一 `BaseCheckpointSaver` 接口（第 23.4 ③） |
| 被否决 | ① 只用 Redis：重启丢挂起状态；② 只用 PG：高频断点恢复延迟高；③ 自研持久化：LangGraph 的序列化协议（含中断上下文）自己实现极易踩坑 |
| 接受的代价 | 三级语义不等价（内存级重启即丢，仅开发模式）；可选依赖函数内导入被 lint 工具质疑（`tiered.py:8-9` 特意注释辩护） |
| 何时该换 | 明确单机开发场景可固定 InMemorySaver，砍掉探测逻辑 |

### 决策 5 · 存储：pgvector 进 PG，而非独立向量库（Milvus/Qdrant）

| 项 | 内容 |
| --- | --- |
| 要解决的问题 | 记忆/文档块既要**关系查询**（按 project/kind 过滤）又要**向量近邻**，两套存储要手工保证一致 |
| 选了什么 | `MemoryItem` 一张表同时承载：普通列过滤 + `Vector(get_embedding_dim())` 近邻（第 0.3 ④） |
| 被否决 | ① 独立向量库：多一次网络往返 + 双写一致性 + 运维成本，对单机规模是过度设计；② 全内存 FAISS：不持久化 |
| 接受的代价 | pgvector 在亿级向量、高 QPS 场景弱于专用库；**向量维度绑定建表**（`models/memory.py:22`），换 embedding 底座需重建表（第 0.3 坑） |
| 何时该换 | 向量量级上千万、或多租户高并发检索时，再引入专用向量库不迟 |

### 一条贯穿的决策原则

> **每一层都先做"能跑通的最简正确版"，把复杂度后置到"确实疼了"再引入**——检索先有单路再有多路、持久化先有 Memory 再有三级、存储先有 PG 再考虑专用向量库。阅读本项目时问"这里为什么不上 X"，答案通常是"当前规模不需要"；问"什么时候该上 X"，看每张表的"何时该换"行。

***

<p align="center">学完第一部分（设计推演）+ 第二部分（模块解剖）+ 第三部分（从零复现），</p>
<p align="center">你就有能力独立搭建（甚至改进）一个多智能体论文助手。</p>
<p align="center">与实现不一致的地方，以实际代码为准——发现问题欢迎补充完善本文档。</p>
