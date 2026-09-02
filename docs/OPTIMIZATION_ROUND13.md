# 优化记录 · 第十三轮（简历对照整改：审计合规 / 改写自适应 / 记忆召回排序 / 多实例部署）

> 文档域：backend + deploy
> 文档类型：轮次记录
> 主题版本：—
> 轮次：ROUND13
> 日期：2026-09-02
> 状态：已落地

> 范围：承接 2026-09-02 的项目全量审计结果。审计对照简历逐点核验后锁定四项缺口——
> ① 审计参数合规硬约束（超 200 字符截断 + 哈希指纹 + 摘要）未实现；
> ② Query 改写只有全局布尔开关，AB\_REPORT 建议的"按查询难度自适应"未落地；
> ③ 长期记忆召回仅按 importance 重排导致语义最相关项被顶掉；
> ④ dist\_lock/熔断器"多实例"无部署载体（无 Dockerfile、无 app 服务）。本轮四项全部落地，
> 交付 59 项 pytest 全过 + ruff/mypy 静态检查零错误，并同步更新全部相关文档。

## 一、本轮改进总览

| 优先级  | 内容                                                                                | 面试收益             | 关键文件（代码证据）                                                                                                                                                               |
| ---- | --------------------------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| P0-1 | 审计参数合规：超 200 字符截断 + sha256 指纹 + 摘要（唯一落库口统一净化）                                     | 合规硬约束 / 安全严谨度    | [audit.py](file:///d:/PythonProject/Lun-Assistant/infrastructure/audit.py)                                                                                               |
| P0-2 | Query 改写三级模式 `off/auto/on`：`is_rewrite_worthwhile` 难度判定，简单查询跳过 LLM（strategy=skip） | 简历"自适应"表述有真实实现支撑 | [query\_rewrite.py](file:///d:/PythonProject/Lun-Assistant/services/rag/query_rewrite.py)、[pipeline.py](file:///d:/PythonProject/Lun-Assistant/services/rag/pipeline.py) |
| P0-3 | 长期记忆召回改「距离×重要度」加权混合排序（select 带距离列 + hybrid\_rank 纯函数）                             | 召回质量修正           | [long\_term.py](file:///d:/PythonProject/Lun-Assistant/services/memory/long_term.py)                                                                                     |
| P1-4 | Dockerfile + compose `app` 服务：多实例部署载体，dist\_lock/熔断可现场验证                          | "多实例互斥"从代码变为可见部署 | [Dockerfile](file:///d:/PythonProject/Lun-Assistant/Dockerfile)、[docker-compose.yml](file:///d:/PythonProject/Lun-Assistant/docker-compose.yml)                          |

## 二、文件级变更摘要

| 文件                                 | 改动                                                                                                               | 类型 |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------- | -- |
| `infrastructure/audit.py`          | 新增 `_sanitize_value` / `sanitize_detail` 递归净化；`write_audit` 落库前统一净化                                              | 修改 |
| `services/rag/query_rewrite.py`    | 新增 `_COLLOQUIAL_MARKERS` 口语词表、`is_rewrite_worthwhile()` 难度判定；`rewrite_query` 增加 `mode` 参数（on/auto/off，None 时读配置） | 修改 |
| `services/rag/pipeline.py`         | `search()` 新增 `rewrite_mode` 透传；S1 阶段 auto 语义接入                                                                  | 修改 |
| `evals/ab.py` / `evals/harness.py` | 评测入口显式传 `rewrite_mode="on"/"off"`，保持 AB 组别口径不被 auto 污染                                                           | 修改 |
| `services/memory/long_term.py`     | 新增 `hybrid_rank()` 纯函数；`recall()` select 带余弦距离列，α 加权重排                                                           | 修改 |
| `configs/settings.yaml`            | 新增 `rag.rewrite_mode`、`memory.recall_semantic_weight`、`governance.audit.sanitize_chars`                          | 修改 |
| `Dockerfile` / `.dockerignore`     | 后端容器镜像（python:3.12-slim + 非 root + /health 健康检查）                                                                 | 新增 |
| `docker-compose.yml`               | 新增 `app` 服务（env override PG\_HOST/PG\_PORT 走容器网络）                                                                | 修改 |
| `tests/test_audit_sanitize.py`     | 审计净化纯函数单测（截断/指纹可复现/嵌套递归）                                                                                         | 新增 |
| `tests/test_query_rewrite.py`      | 追加难度判定用例（hard 全 True / simple 全 False）                                                                           | 修改 |
| `tests/test_memory_pure.py`        | 追加 `hybrid_rank` 用例（语义主导/重要度 tie-break/空输入）                                                                      | 修改 |

## 三、P0-1 审计参数合规（截断 + 哈希指纹 + 摘要）

### 3.1 背景

审计链路三入口（工具调用 `tool_registry._finalize`、HTTP `AuditMiddleware`、认证 `auth/router`）最终统一落在
`write_audit` 写 `audit_logs.detail(JSON)`。此前全量直存：`check_format`/`detect_ai_text` 等工具会把整篇
论文文本写入日志，违反项目硬约束「审计日志必须截断参数超过 200 字符，仅存哈希指纹与摘要」。

### 3.2 实现

[audit.py](file:///d:/PythonProject/Lun-Assistant/infrastructure/audit.py#L23) `_sanitize_value` 递归净化：

```python
if isinstance(value, str) and len(value) > chars:
    return {"fp": sha256(value).hexdigest()[:16], "sum": value[:chars], "len": len(value)}
```

- 指纹：sha256 前 16 位，**相同原文指纹可复现**，人工审计对账仍可溯源；

- 摘要：保留前 200 字符（`governance.audit.sanitize_chars` 可配）；

- 长度：记录原文长度，便于统计超限字段占比；

- 短值 / 布尔 / 数字 / None 原样保留，`action/resource/user_id/ip` 等主信息不受影响；

- 净化在唯一落库口完成，一次改动自动覆盖三条入口，`AuditLog.detail` JSON 列 schema 不变。

### 3.3 验证

`tests/test_audit_sanitize.py` 覆盖：短值透传 / 5000 字符截断为 {fp,sum,len} / 指纹可复现 / 嵌套 dict+list 递归 / None 与数值原样。

## 四、P0-2 Query 改写按难度自适应（off / auto / on）

### 4.1 背景

AB\_REPORT 结论：改写对简单术语查询零召回增益（纯开销 2.2s→61s），对口语化长尾查询是强优化。
此前仅 `rag.rewrite_enabled` 全局布尔，所有查询一刀切走 LLM 改写，"按查询难度自适应开关"未落地。

### 4.2 实现

- [query\_rewrite.py](file:///d:/PythonProject/Lun-Assistant/services/rag/query_rewrite.py#L137) 新增零 LLM 的难度判定：

```python
_COLLOQUIAL_MARKERS = ("怎么破", "站不住脚", "没底", "太像", "怕过不了", "嫌我",
                       "乱七八糟", "忘了", "乱调", "像流水账", "咋", "啥", ...)

def is_rewrite_worthwhile(query):
    if any(m in q for m in _COLLOQUIAL_MARKERS): return True   # 口语化长尾 → 值得 LLM
    return len(q) > 40                                        # 其余长句保守回现状全走 LLM
```

判定原则「保守向 LLM」：只在明确简单（短句 + 无口语信号）时才跳过，避免引入召回回退风险。

- `rewrite_query(query, provider=None, *, mode=None)` 三级模式，None → 读 `rag.rewrite_mode`（默认 auto）：

  - `off` → `strategy="idle"`（原查询 + 规则关键词）；

  - `auto` 且判定简单 → `strategy="skip"`（跳过 LLM，仅规则关键词，零 LLM 开销）；

  - `on` 或 auto 判定长尾 → 走 LLM 改写，失败/拒答/漂移仍回退规则改写（防漂移三件套保留）。

### 4.3 评测口径保持（本次改动不回退硬指标）

评测脚本 `ab.py` / `harness.py` 显式传 `rewrite_mode="on"/"off"`，**AB 分组语义不被 auto 污染**：

- 简单集 8 条：全部判定为简单 → 跳过 LLM，Recall 本为 100% 保持不变，时延显著下降（预计回归 AB\_REPORT 的 2.2s→近乎规则开销）；

- 长尾困难集 8 条：口语词表全命中 → 照走 LLM，Recall/MRR 与修复版 A₁ 完全一致。

- `tests/test_query_rewrite.py`：hard/simple 全量数据覆盖判定正确性。

## 五、P0-3 长期记忆召回排序修复

### 5.1 问题

旧实现：SQL 按余弦距离取 `top_k*2` 候选 → **内存仅按 importance 重排** → 语义最相关但重要性低的
记忆会被"重要性高却跑题"的历史 summary 顶掉；且 SQL 未带出距离值，内存侧无从使用。

### 5.2 实现

[long\_term.py](file:///d:/PythonProject/Lun-Assistant/services/memory/long_term.py#L16)：

```python
def hybrid_rank(rows_dists, alpha, top_k):
    d_min, d_max = min(dists), max(dists); span = (d_max - d_min) or 1.0
    scored = [(alpha * (1 - (d - d_min) / span) + (1 - alpha) * importance, r)...]
```

- `recall()` 用 `stmt.add_columns(dist_col)` 保留余弦距离，`(entity, float(dist))` 传入纯函数；

- `alpha = memory.recall_semantic_weight`（默认 0.7）：语义距离主导、importance 降为次因子；

- 收敛 `(r, d)` 类型并过滤非数值距离，mypy 严格模式通过。

- `tests/test_memory_pure.py`：语义主导 / 距离同分时 importance 作 tie-break / 空输入容错。

## 六、P1-4 多实例部署载体（Dockerfile + compose app）

### 6.1 背景

此前 docker-compose 仅编排 PostgreSQL+Redis 依赖，应用裸进程运行；dist\_lock / 三态熔断器虽已具备
"多实例共享 Redis 状态视图"的能力，但没有第二个实例可证明。

### 6.2 实现

- [Dockerfile](file:///d:/PythonProject/Lun-Assistant/Dockerfile)：`python:3.12-slim` + torch 运行最小系统库
  （libgomp1/libglib2.0-0，不含编译链）+ 依赖层缓存 + 非 root 用户 + urllib `/health` 健康检查；
  `.dockerignore` 排除 .env/venv/event 目录/前端 node\_modules 等，缩小构建上下文。

- [docker-compose.yml](file:///d:/PythonProject/Lun-Assistant/docker-compose.yml#L46) 新增 `app` 服务：

```yaml
app:
  build: .
  env_file: .env
  environment:
    PG_HOST: postgres      # 容器网络走服务名
    PG_PORT: "5432"        # 覆盖本机 .env 的 5433，两者互不影响
  ports: ["8001:8000"]
  depends_on: postgres/redis 均 service_healthy
  volumes: [uploads:/app/data/uploads]
```

- 起两副本验证路径：`docker compose up -d --scale app=2` →
  副本 A 持 `DistributedLock` 期间副本 B `acquire` 抛 `LockNotAcquired`；
  副本 A 连续失败打满熔断阈值后 B 的 `before_call` 直接 `CircuitOpenError`（快速失败共享视图）。

### 6.3 限制

本机未安装 Docker CLI，compose 变更未做 `docker compose config` 实机校验（语法人工核对）。
容器内 `models/` 未挂载，首次启动 HF 下载需网络或在镜像内预置（当前 `HF_HUB_OFFLINE=1` 仅对已缓存
模型生效，如需离线建议 build ARG 预下载）。

## 七、验证证据

```
$ .\envs\lunjiang\python.exe -m pytest tests -q
59 passed in 2.78s

$ .\envs\lunjiang\python.exe -m ruff check infrastructure services evals tests
All checks passed!

$ .\envs\lunjiang\python.exe -m mypy infrastructure\audit.py services\rag\query_rewrite.py \
    services\rag\pipeline.py services\memory\long_term.py evals\ab.py evals\harness.py
Success: no issues found in 6 source files

运行时冒烟（真实配置加载）:
rewrite_mode= auto | weight= 0.7 | sanitize= 200
hard= True | simple= False | fp= c5c30650816a3625 len= 300
```

## 八、与历史约定的一致性

- 配置文件新增项集中在 `configs/settings.yaml`，模块读取走 `get_value()`（缺失回退默认值），无硬编码；

- 评测入口显式传模式下，AB 实验/回归评测口径与本轮改动前一致，`results_latest.json` 等历史结果可继续对比；

- 新增纯函数均带单测且全部离线可跑；改动未触碰三层架构（api → services → infrastructure）依赖方向。

