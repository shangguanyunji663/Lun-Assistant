# 优化记录 · 第六轮（架构改进与工程化治理）

> 范围：工程化 / 模块化审查识别的 P0/P1 问题修复 + 架构改进 + 治理层测试骨架。本轮不新建业务功能，而是把此前审查发现的工程化短板系统性补齐，并在代码中逐项验证（附 file:line 证据）。
>
> 说明：本文件即「工程化 / 模块化审查」的落档形态——审查发现的每项问题，其修复即本轮优化内容，故不再另立独立的「审查报告」。

## 一、本轮改进总览

| 模块 | 内容 | 关键文件（代码证据） |
| --- | --- | --- |
| 治理层 | ToolRegistry 六步治理流水线（RBAC/限流/熔断/锁/容错/审计/观测） | [tool\_registry](file:///d:/PythonProject/Lun-Assistant/services/governance/tool_registry.py) |
| 可测性 | 同步 handler 线程池适配（修复 P0-1）+ 离线 pytest 测试骨架（9 用例） | [tool\_registry:88](file:///d:/PythonProject/Lun-Assistant/services/governance/tool_registry.py)、[test\_tool\_registry\_call](file:///d:/PythonProject/Lun-Assistant/tests/test_tool_registry_call.py) |
| 路径单一真源 | 收敛 `PROJECT_ROOT`（消除 12 处重复定义 + sys.path hack） | [paths](file:///d:/PythonProject/Lun-Assistant/infrastructure/paths.py) |
| 数据模型 | embedding 维度解耦（修复 P0-2）+ Project.status 前后端对齐（修复 P0-3） | [memory](file:///d:/PythonProject/Lun-Assistant/infrastructure/models/memory.py)、[project](file:///d:/PythonProject/Lun-Assistant/infrastructure/models/project.py)、[constants](file:///d:/PythonProject/Lun-Assistant/frontend/src/constants.js) |
| 注册幂等 | `register_all` 幂等 + tools.yaml 单次加载（lru_cache） | [tools\_impl:153](file:///d:/PythonProject/Lun-Assistant/services/governance/tools_impl.py) |
| API 契约/分层 | 主要路由补 `response_model`；agent 路由收敛为校验+SSE，编排下沉 | [projects/router](file:///d:/PythonProject/Lun-Assistant/api/projects/router.py)、[agent/router:8](file:///d:/PythonProject/Lun-Assistant/api/agent/router.py) |
| 清理 | tools.yaml 死配置移除；`retriever.py` 不规范 logger 清理 | [tools.yaml](file:///d:/PythonProject/Lun-Assistant/configs/tools.yaml)、[retriever:10](file:///d:/PythonProject/Lun-Assistant/services/rag/retriever.py) |
| 依赖解环 | **打破 agent↔governance 双向依赖**：`artifacts.py`（结构化产物生成）从 agent 层下沉至 governance 层，治理层不再反向依赖编排层 | [artifacts](file:///d:/PythonProject/Lun-Assistant/services/governance/artifacts.py)、[tools\_impl:4](file:///d:/PythonProject/Lun-Assistant/services/governance/tools_impl.py) |

## 二、治理层与可测性（修复 P0-1）

`ToolRegistry.call()` 统一编排 7 个外部边界（RBAC / 限流 / 熔断 / 分布式锁 / 三级容错 / 审计 / 行为观测）。

- `_invoke_handler`（`tool_registry.py:88-92`）将同步/异步 handler 适配抽出：同步 handler 经 `asyncio.to_thread` 执行，异步直接 `await`。这一步**修复了 P0-1** —— `format_reference` 是同步 `def`，此前被 `await` 调用会 `TypeError`，现由线程池适配，既有 `tests/test_tool_registry.py::test_sync_handler_executed_via_thread_pool` 覆盖。
- 治理流水线具备**离线 pytest 测试骨架**（`tests/test_tool_registry_call.py`，9 用例 + `reg` fixture，模块边界 mock 隔离 Redis/Postgres）：覆盖成功主路径、RBAC 拒绝、限流拒绝、熔断打开、三级容错耗尽→人机兜底、通用异常、同步 handler、分布式锁装配、行为观测上下文透传。与 `test_tool_registry.py` / `test_rbac.py` 共 **18 passed**。
- 测试化过程中发现**审计盲区**：RBAC/限流拒绝发生在 `_finalize()`（审计写库）之前，被拒调用不落审计日志。已用 `write_audit.assert_not_awaited()` 锁定现状，修复建议见第八节。

## 三、路径与配置单一真源

`infrastructure/paths.py:12` 收敛 `PROJECT_ROOT` 及 `CONFIG_DIR`/`DATA_DIR`/`EVALS_DIR` 等路径常量，文档注释明确"此前 PROJECT_ROOT 在 12 处重复定义，sys.path.insert 样板散落 12 处"。全部 `scripts/` 与 `evals/` 改为 `sys.path.insert` 单行引导 + `from infrastructure.paths import PROJECT_ROOT`，不再各自计算路径。**消除审查发现的路径重复定义问题。**

## 四、数据模型与枚举对齐（修复 P0-2 / P0-3）

- **P0-2 embedding 维度解耦**：`memory.py:21-22` 注释"维度跟随运行时 embedding_provider"，列定义为 `mapped_column(Vector(get_embedding_dim()))`；`get_embedding_dim()`（`config.py:80`）读取运行时 `embedding_provider` 对应底座的 `embedding_dim`。**切换底座（如 zhipu 2048）不再硬编码失败。**
- **P0-3 状态枚举前后端对齐**：后端 `project.py:9` `PROJECT_STATUSES = ("created","topic","literature","writing","review","finalize")`，`project.py:18` 默认 `"created"`；前端 `constants.js:1-6` `STATUS_LABEL` 与之后端 6 态一一对应，注释"单一真源在后端，由后端 Pydantic Literal 校验，前端仅做文案映射"。**前后端状态语义不再错配。**

## 五、注册与启动幂等

`tools_impl.py:153` `register_all()` 注"注册全部治理工具（幂等，可安全多次调用）"；`tool_registry.register()`（`tool_registry.py:64-76`）对已注册同 handler 直接跳过。`_tools_yaml_config()`（`tool_registry.py:38-43`）为 `@lru_cache(maxsize=1)`，**tools.yaml 仅加载一次**，消除审查指出的"每次 register 重开+解析 YAML（14 次磁盘 IO）"问题。`register_all()` 在 `main.py:65`（lifespan）与 `agent/engine.py:42-43`（`AgentEngine.get_graph()` 单例锁内兜底注册，覆盖脚本/评测等未走 FastAPI lifespan 的入口）均可安全多次调用。

## 六、API 契约与分层

- **response_model 补齐**：`api/projects/router.py` 全部 5 个端点均带 `response_model`（`ProjectCreatedOut` / `list[ProjectListItem]` / `ProjectDetailOut` / `ProjectPatchedOut` / `DeletedOut`，见 `:28,38,48,56,69`）；`auth` / `knowledge` / `observability` 路由同样使用。**审查"全路由无 response_model"的论断已过时。** 响应模型统一收敛到各路由的 `schemas.py`（`api/auth/schemas.py` / `api/projects/schemas.py` / `api/knowledge/schemas.py` / `api/observability/schemas.py`），不再散落在 router 文件内。
- **共享依赖**：项目归属校验收敛为 `api/deps.py::get_owned_project`，`projects` 与 `knowledge` 路由复用，消除两处重复的 `_get_owned` 实现。
- **知识库路由拆分**：项目知识库 4 端点（上传/列表/删除/库内检索）从 `api/projects/router.py` 拆出，独立为 `api/knowledge/router.py`（聚合根前缀 `/api/projects/{project_id}/knowledge`），`projects` 路由只保留项目 CRUD。
- **路由分层**：`api/agent/router.py:8` 注释明确"本路由只做参数校验与 SSE 序列化；对话编排（记忆双写/压缩/偏好/归档）"下沉到 agent 层。编排实现在 `services/agent/conversation_service.py`（`ConversationService.stream_chat/stream_resume`），原先散落在路由内的记忆维护逻辑（`_fire`/`_compress_window`/`_learn_preference`/`_archive_decision`）随之下沉。**审查指出的"路由承载业务逻辑"问题已修复。**

## 七、死配置 / 死代码清理

- `configs/tools.yaml` 中 grep `classify_intent` / `ingest_corpus` / `admin_reindex` **无匹配** —— 审查指出的 3 条未注册死配置已移除。
- `services/rag/retriever.py:10` 现为规范 `import logging`，审查指出的 `__import__("logging")` 动态取 logger 已清理。
- **Query 改写判重死逻辑修复**（`query_rewrite.py:_rule_rewrite`）：判重口径从"扩展串**首词**是否已出现"改为"**整段扩展**是否已出现"。旧实现中扩展串首词通常即触发词本身（如术语"大模型"的扩展首词即"大模型"），守卫恒真，同义词池整体失效。
- **LLM 接入收敛**：`services/llm/provider.py` 删除 `get_chat_model()`（langchain ChatOpenAI 适配层），全项目统一 `LLMProvider`（openai 官方异步 SDK），LangGraph 图内节点同样直连；`requirements.txt` 的 langchain 依赖仅保留 langgraph 系。
- **死参数清理**：`HybridRetriever.dense_search()` 移除已无调用方的 `project_id` 参数（项目文档统一走 `project_dense_search`）。
- **延迟 import 大范围收敛**：本轮将函数内延迟导入批量提升为模块级（`builder` / `engine` / `planner` / `node_factory` / `supervisor` / `academic_tools` / `tools_impl` / `retriever` / `query_rewrite` / `compressor` / `trace` / `tiered` / `dist_lock` / `skill` 等），审查指出的"延迟 import 泛滥"已清理大部分；残余（如引擎启动期的模块级依赖环规避）见 8.3。

## 八、审查发现总表与遗留项

### 8.1 P0 缺陷修复对照

| # | 问题 | 修复落点（代码证据） | 状态 |
| --- | --- | --- | --- |
| P0-1 | `format_reference` 同步 `def` 被 `await` 调用 → TypeError | `_invoke_handler` 线程池适配（`tool_registry.py:88-92`）+ 测试覆盖 | ✅ |
| P0-2 | embedding 维度硬编码 1024，切换底座入库失败 | `Vector(get_embedding_dim())`（`memory.py:21-22`，`config.py:80`） | ✅ |
| P0-3 | 前后端 `Project.status` 枚举错配 | 后端 `project.py:9,18` + 前端 `constants.js:3-6` 对齐 6 态 | ✅ |

### 8.2 架构性问题复核

| 问题 | 结论 | 证据 |
| --- | --- | --- |
| 延迟 import 泛滥（审查称 82 处） | 🟡 大部分已收敛：函数内导入批量提升为模块级（见第七节），残余仅限规避模块级依赖环的个别处 | 见 8.3-2 |
| 路由承载业务逻辑 | ✅ 已修复：编排下沉 agent 层 | `api/agent/router.py:8` 注释 |
| `register_all()` 无幂等/无缓存 | ✅ 已修复：幂等 + YAML `lru_cache` 单次加载 | `tools_impl.py:153`、`tool_registry.py:38-43` |
| 路径/导入 hack 重复（PROJECT_ROOT 12 处） | ✅ 已修复：`paths.py` 单一真源 | `infrastructure/paths.py:12` |
| 缺 API 契约（全路由无 response_model） | ✅ 已修复：主要路由均补 `response_model` | `api/projects/router.py:28,38,48,56,69` 等 |
| 事件协议未兑现（死代码） | ⬜ 仍待办（设计决策） | 前端 `tool` 事件白名单/渲染分支 |
| 死配置（tools.yaml 3 条） | ✅ 已移除 | grep 无匹配 |
| 死代码（_STYLE_TMPL 等 / 缺 `__init__` / `_archive`） | 🟡 部分清理 | — |
| 不规范取 logger（`__import__("logging")`） | ✅ 已修复 | `retriever.py:10` 现为 `import logging` |

### 8.3 遗留与建议（未在本轮强行改动，待拍板）

1. **审计盲区**：`call()` 的 RBAC/限流拒绝不落审计日志。建议在 `call()` 入口将鉴权/限流拦截与执行结果统一纳入 `_finalize()` 审计通道；改动后相关测试断言可改为校验 `detail["ok"] is False`。
2. **延迟 import 残余**（审查称 82 处）：本轮已清理大部分（见第七节），残余仅在规避模块级依赖环的个别位置；如需彻底清零，可用 `TYPE_CHECKING` + 延迟导入双轨。
3. **前端事件协议死代码**（`App.jsx` 中 `tool` 事件白名单/渲染分支）：后端未 emit 对应事件，属已知待办。
4. **工程化补齐**：仓库仍缺 pyproject / CI / Alembic 迁移（审查事实基线）；建议后续引入，使测试骨架接入 CI、模型变更走迁移。

## 九、验证与结论

- 治理层离线测试：`pytest tests/test_tool_registry.py tests/test_tool_registry_call.py tests/test_rbac.py` → **18 passed**（无 Redis/Postgres 依赖）。
- 上述架构改进与 P0 修复均已在代码中存在并经 grep/Read 验证（file:line 见各节）。
- 第六轮将「工程化 / 模块化审查」发现的问题统一收口为架构改进与工程化治理，审查即本轮优化范围，不再另立独立的审查报告文档。

## 十、架构：打破 agent↔governance 双向依赖（artifacts 下沉）

> 审查补充：第六轮落档后进一步审查发现治理层存在对编排层的反向依赖，形成双向环，本轮收口处理。

**问题**：
- `services/governance/tools_impl.py:4` 导入 `services/agent/artifacts.py` 并将 `generate_artifact` 注册为治理工具；
- 而 agent 层（`planner.py`、`specialists/node_factory.py`）依赖 `services.governance.tool_registry` —— 依赖方向出现 `agent → governance → agent` 环。

**改动**：
1. `services/agent/artifacts.py` → `services/governance/artifacts.py`（结构化产物生成本质是"工具实现"，与 `tools_impl.py` / `academic_tools.py` 归置同一层）；
2. `tools_impl.py:4` import 路径更新为 `services.governance.artifacts`；
3. `evals/regression.py:200,204`（S6 产物场景）引用同步更新。

**效果（依赖方向恢复单向）**：

```
优化前：                         优化后：
agent/ ──────→ governance       agent/ ──────→ governance
  planner / node_factory          planner / node_factory
      ↑                                │ tool_registry.call()
      └── tools_impl ──→ agent/artifacts │
          （governance 反向依赖 agent）   ▼
                                   governance/ 自包含
                                   （tools_impl + artifacts + academic_tools）
```

**验证状态**：按指示本次改动未运行测试；建议后续执行 `pytest tests/` 与 `evals/regression.py`（S5/S6/S7 场景）回归确认。
