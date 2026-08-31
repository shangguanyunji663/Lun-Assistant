# 论匠 · 第二轮优化改进记录

> 日期：2026-08-31 \~ 2026-09-01
> 范围：本地可上手性验证 + Ollama KV Cache OOM 根治（含 /v1 兼容层坑）+ 文档体系重建 +
> **方案 B 三层结构重构完整落地**（P0-1 \~ P1-5，功能零变化）。

## 背景

第一轮（性能/安全/体验五件套）落地后按 README 从零验证上手，暴露两类问题：
**① 本地 16GB 机器跑通 qwen3:4b（OOM）** 比预想复杂——Ollama 的 `/v1` 兼容端点不认请求级 `options`；
**② README 定位失当**（越写越像学习文档）。随后用户拍板执行此前审查提出的**方案 B（三层结构）**，
本轮已完成代码迁移并全套回归。

## 本轮改进明细

### 1. Ollama 500：KV Cache OOM 根治（稳定性 ⭐核心）

**现象**：`check_env.py` 及对话接口返回 500：
`failed to allocate buffer of size 35433480192`（≈33GB）。

**根因（分两层）**：

1. qwen3:4b 模型权重仅 2.5GB，但 **KV Cache ≈ 2×层数×KV头数×头维度×上下文长度×2字节**，
   Ollama 默认超大上下文 → 16GB 机器预分配失败；
2. **Ollama** **`/api/generate`** **认请求级** **`options.num_ctx`，但** **`/v1/chat/completions`** **不认**——
   LLMProvider（基于 OpenAI SDK）走 `/v1`，此前注入的 `extra_body.options` 被忽略，
   模型仍按默认上下文加载 → 对话接口持续 OOM（实测复现 `[V1+OPTIONS] FAIL`）。

**修复**（双保险）：

- **主方案**：Modelfile 打镜像副本，`PARAMETER num_ctx 4096` 固化到模型本身
  （[configs/ollama/Modelfile.qwen3-ctx4096](../configs/ollama/Modelfile.qwen3-ctx4096)）：

  ```powershell
  ollama create qwen3:4b-ctx4096 -f configs\ollama\Modelfile.qwen3-ctx4096
  ```

  blob 与 `qwen3:4b` 共享，磁盘增量极小；`configs/settings.yaml` 的 `chat_model` 指向新标签。
  任何端点（`/v1` 或 `/api`）调用该模型均默认 4096 上下文，**彻底消除 OOM 路径**。

- **辅方案**：保留 [check\_env.py](../scripts/check_env.py) 与
  [services/llm/provider.py](../services/llm/provider.py) 中 `options.num_ctx=4096`（对 `/api/generate` 等原生端点有效）。

**验证**：

- `/v1/chat/completions` 直呼 `qwen3:4b-ctx4096` → 正常返回（此前同请求 500）；

- `check_env.py` 5/5、`smoke_api` 端到端对话正常。

### 2. qwen3 思考型模型空回复修复（正确性）

**现象**：OOM 修复后 `check_env.py` 对话项仍 FAIL——`num_predict=16` 预算被思考链吃光，
`done_reason=length`，`response` 为空。

**修复**：显式 `think: False` + `num_predict` 16→64（见 `check_env.py` / provider `_extra`）。

### 3. 补齐 bge-m3 embedding 模型（环境完备性）

`ollama pull bge-m3`（约 1.2GB，1024 维），Embedding 检查通过。

### 4. 按 README 全链路验证（可上手性）

`check_env 5/5` → 语料入库 16 篇 → uvicorn `/health` → 注册/登录/建项目 全通。

### 5. 文档体系重建：README 回归入口页定位（可维护性）

- [README.md](../README.md) 精简为入口页（120 行内）：快速开始 / 核心特性 / 目录简览 / API 速览 / FAQ；

- 新增 [docs/LEARNING\_GUIDE.md](../docs/LEARNING_GUIDE.md)：15 课教学式学习文档（从零重建思维）；

- 新增本文档；`docs/OPTIMIZATION_ROUND1.md` 路径随重构同步修正；

- 术语统一：README/学习指南/优化记录与重构后真实目录一一对应。

### 6. 方案 B：三层结构重构落地（结构 ⭐核心，功能零变化）

**目标结构**（依赖只允许从上到下）：

```
api/（接口：auth/projects/agent/observability/middleware）
  → services/（业务：agent/rag/memory/governance/classifier/streaming/checkpoint/llm/observability）
    → infrastructure/（地基：config/db/redis_client/audit/rbac/models）
      → configs/ data/ evals/ scripts/（静态资源）
```

**执行清单**（本回合完成 P0-1 \~ P0-3 + P1-4 + P1-5）：

| 阶段   | 动作                                                                                                             | 结果 | <br />        | <br />                              | <br /> | <br />        | <br /> |
| ---- | -------------------------------------------------------------------------------------------------------------- | -- | :------------ | :---------------------------------- | :----- | :------------ | :----- |
| P0-1 | \`app/config                                                                                                   | db | redis\_client | audit\_service→infrastructure/audit | rbac   | models\` 全部下沉 | 完成     |
| P0-2 | `app/main.py→main.py` 顶层；`app/auth·agent·middleware→api/`，`app/gateway→api/projects`（命名纠偏）                     | 完成 | <br />        | <br />                              | <br /> | <br />        | <br /> |
| P0-3 | `core/* -> services/agent·llm·classifier·streaming·checkpoint`；`rag/memory/governance/observability→services/` | 完成 | <br />        | <br />                              | <br /> | <br />        | <br /> |
| P1-4 | `services/agent/specialists/` 拆分：`specs.py` + `schemas.py` + `node_factory.py` + `__init__.py` 聚合导出（对外符号不变）    | 完成 | <br />        | <br />                              | <br /> | <br />        | <br /> |
| P1-5 | 删 `scripts/__init__.py`；`check_mem/test_think/to_utf8.ps1` → `scripts/_archive/`                               | 完成 | <br />        | <br />                              | <br /> | <br />        | <br /> |

**遭遇的坑（经验值 +1）**：

- 早期源码存在 **`\r\r\n`** **坏死换行**（GBK 转码残留），导致文本级读写校验往返不一致、
  并干扰编辑器展示——最终用**字节级**重写（`write_bytes` + `read_bytes` 校验）一次性根治并全员统一 LF；

- 目录层级变化后，`Path(__file__)` 相对计算的项目根偏移：
  `tool_registry.py` 与 `corpus_loader.py` 的 `PROJECT_ROOT` 分别 +1 层修正。

**验证（全部通过）**：

- `compileall` 全绿；`import main` 全链路 OK；

- LangGraph 图编译成功：`supervisor` + 6 个 specialist 节点齐全；

- `check_env.py` **5/5**；`smoke_rag`（改写回退/向量检索/精排）通过；`smoke_governance`（RBAC/限流/降级/Skill 沉淀）通过；

- `smoke_api` 端到端：注册→登录→SSE 对话（intent=rule 层 chitchat → 完整回复 → `[final]`/`[done]`）通过；

- API 手工链路：`/health` + register + login(164B token) + 建项目 全 2xx。

## 验证清单

| 项          | 验证方式                                                                                  | 结果   |
| ---------- | ------------------------------------------------------------------------------------- | ---- |
| /v1 OOM 根治 | 直呼 `/v1/chat/completions`(qwen3:4b-ctx4096)                                           | 通过   |
| 空回复修复      | `check_env.py` 对话项                                                                    | PASS |
| 环境整套       | `check_env 5/5` · 语料入库 · `/health` · 注册-登录-建项目                                        | 全通过  |
| 结构迁移       | 63 文件移动 · 196 处 import 改写 · 0 残留旧导入 · 字节级读回校验                                         | 通过   |
| 换行根治       | 全 .py 统一 LF（消除 `\r\r\n`）                                                              | 通过   |
| 图编译        | `build_graph()` 节点：supervisor + topic/literature/writing/format/plagiarism/ai\_detect | 通过   |
| 冒烟回归       | smoke\_rag / smoke\_governance / smoke\_api                                           | 全通过  |
| 文档同步       | README / LEARNING\_GUIDE(122 处路径) / ROUND1 / 本文档                                      | 同步完成 |

## 遗留与后续

- **P2-6 仓储层**（`infrastructure/repositories/`）：抽离 retriever / trace / skill / memory 中内联 SQL，
  换存储或加缓存不再散改 20+ 处——**风险等级与目录搬迁不同，建议单独批次**；

- **部署生产化**：gunicorn/systemd/Nginx 配置示例已在 ROUND2 前的长版 README 中起草，可沉淀为
  `docs/DEPLOYMENT.md`（gunicorn 命令注意 `main:app` 新入口）；

- **CI 化**：`scripts/check_imports.py`（自动发现依赖倒置）+ smoke 全量回归挂钩 git pre-push；

- README 研发提示：启动命令现为 `uvicorn main:app`（不再是 `app.main:app`）。

## 经验沉淀

1. **Ollama 兼容层的两个"隐形坑"**：① `/v1` 端点不认请求级 `options`（num\_ctx 必须固化到
   Modelfile 镜像副本）；② 思考型模型要显式 `think=False` + 足够的 `num_predict`。
   报 `failed to allocate buffer` 时先按 KV Cache 预算排查，而不是怀疑模型文件。
2. **批量改写必须字节级**：遭遇 `\r\r\n` 之后，文件内容治理一律 `read_bytes → replace → write_bytes → read_bytes 校验`，
   不要依赖文本模式（universal newlines）往返，否则得到"看似改写了但读回不一致"的假象。
3. **目录迁移后的路径级 bug 自查**：凡 `Path(__file__)` 计算项目根/配置目录的模块，搬家后必须复查层级；
   重构脚本可以机械替换 import，但这一类比"少父级/多父级"需要按实际目录树人工核对。
4. **文档与代码强一致**：结构重构是文档同步的"波次扩散源"，README、学习指南、历史优化记录
   都应同轮更新，避免出现"文档讲新结构、代码演示旧路径"的分裂。

