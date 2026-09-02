# 优化记录 · 第十二轮（工程化治理：静态检查 / 依赖锁定 / 前端 Hooks / 可移植性）

> 文档域：backend
> 文档类型：轮次记录
> 主题版本：—
> 轮次：ROUND12
> 日期：2026-09-02
> 状态：已落地

> 范围：承接求职展示优先级路线图的 P0/P1/P2 工程化项——静态检查接入 CI、依赖锁定、Alembic 迁移骨架、前端 ESLint + hooks 拆分、常量收敛、docker-compose 与指标端点、仓库治理。本轮以"工程严谨度 / 仓库第一印象 / 全栈可信度 / 演示与可移植"四类面试收益为目标，逐项落地并附验证证据。

## 一、本轮改进总览

| 优先级  | 内容                                                    | 面试收益      | 关键文件（代码证据）                                                                                                                                                                                                                                 |
| ---- | ----------------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| P0-1 | ruff + mypy + pytest 接入 CI（后端 test-backend job）       | 工程严谨度立判   | [pyproject.toml](file:///d:/PythonProject/Lun-Assistant/pyproject.toml)、[ruff.toml](file:///d:/PythonProject/Lun-Assistant/ruff.toml)、[deploy.yml](file:///d:/PythonProject/Lun-Assistant/.github/workflows/deploy.yml)                    |
| P0-2 | Alembic 迁移骨架（env.py 聚合全部模型，替换 create\_all 的前置）        | "企业级"最硬缺口 | [alembic/env.py](file:///d:/PythonProject/Lun-Assistant/alembic/env.py)、[alembic.ini](file:///d:/PythonProject/Lun-Assistant/alembic.ini)                                                                                                  |
| P0-3 | 依赖锁定（requirements.txt `==` 固定）+ 仓库清理（stub/临时文件/设计稿归档） | 仓库第一印象    | [requirements.txt](file:///d:/PythonProject/Lun-Assistant/requirements.txt)                                                                                                                                                                |
| P1-4 | 前端 ESLint + App.jsx hooks 拆分（454 行 → 4 个自定义 hook）     | 全栈可信度     | [App.jsx](file:///d:/PythonProject/Lun-Assistant/frontend/src/App.jsx)、[hooks/](file:///d:/PythonProject/Lun-Assistant/frontend/src/hooks/useChat.js)、[eslint.config.js](file:///d:/PythonProject/Lun-Assistant/frontend/eslint.config.js) |
| P1-5 | 常量/魔法数收敛（`_SSE_HEADERS` 去重、`[:600]` 命名化）              | 代码整洁      | [conversation\_service.py](file:///d:/PythonProject/Lun-Assistant/services/agent/conversation_service.py)                                                                                                                                  |
| P2-6 | docker-compose（pgvector+redis）+ 运行指标端点                | 演示与可移植    | [docker-compose.yml](file:///d:/PythonProject/Lun-Assistant/docker-compose.yml)、[observability/router.py](file:///d:/PythonProject/Lun-Assistant/api/observability/router.py)                                                              |

## 二、文件级变更摘要

| 文件                                           | 改动                                                             | 类型      |
| -------------------------------------------- | -------------------------------------------------------------- | ------- |
| `pyproject.toml` / `ruff.toml`               | mypy / ruff 规则配置（渐进式类型检查）                                      | 新增      |
| `.github/workflows/deploy.yml`               | 新增 `test-backend` job（ruff+pytest）；前端 job 增 `npm run lint`     | 修改      |
| `requirements.txt`                           | `>=` → `==` 版本锁定；补 alembic/mypy/ruff                           | 修改      |
| `services/llm/provider.py` 等 14 文件           | 修复 mypy 32 处报错（openai 类型 / redis await / json\_mode 载荷 / 变量注解） | 修改      |
| `infrastructure/config.py`                   | `.env` 缺失时回退 `.env.example`（CI 可跑测试）                           | 修改      |
| `alembic/` + `alembic.ini`                   | Alembic 异步迁移环境（聚合 `Base.metadata`）                             | 新增      |
| `docker-compose.yml`                         | PostgreSQL(pgvector) + Redis 一键编排                              | 新增      |
| `api/observability/router.py`                | 新增 `GET /api/observability/metrics`（进程 + 表计数，DB 容错）            | 修改      |
| `services/agent/conversation_service.py`     | 删死代码 `_SSE_HEADERS`；`output[:600]` → `_DECISION_ARCHIVE_CHARS` | 修改      |
| `frontend/src/App.jsx`                       | 454 行状态逻辑拆分为 4 个自定义 hook                                       | 修改      |
| `frontend/src/hooks/*.js`                    | `useTheme` / `useSessions` / `useProjects` / `useChat`         | 新增      |
| `frontend/eslint.config.js` / `package.json` | ESLint 9 flat config + `lint` script                           | 新增 / 修改 |
| 迁移残留 stub / 临时文件 / 设计稿                       | 见第九节（commit `9fe5aad`）                                         | 删除 / 归档 |

## 三、P0-1 静态检查与 CI 落地（后端）

### 3.1 工具链配置

- `pyproject.toml:5-22`（`[tool.mypy]`）：`namespace_packages + explicit_package_bases + mypy_path="."` 解决 `api.agent` 与 `services.agent` 同名包导致的 `Duplicate module`；`files` 限定 `main/api/services/infrastructure`，`check_untyped_defs=False` 保持渐进式采用；`[[tool.mypy.overrides]]` 对 `redis.*` 关闭 `misc/arg-type/union-attr`（其 stub 返回 `Awaitable[X] | X` 双兼容类型）。

- `ruff.toml:6-15`（`[lint]`）：只启用"真实错误 + 导入规范"类规则（`E4/E7/E9/F/I/F541/RUF022/RUF100`），设计性用法显式豁免（`B008` FastAPI 惯用、`BLE001` 入口容错等）；`scripts/`、`evals/` 允许宽松容错。

### 3.2 CI 接入

`deploy.yml:77-97` 新增 `test-backend` job（运行于云端 Ubuntu，与本机 Windows 无关）：`setup-python 3.11` → `pip install -r requirements.txt` → `ruff check .` → `pytest tests/ -q`。配置层回退（`config.py:_load_env_file`）保证无 `.env` 也能加载占位值跑测试，**CI 无需伪造** **`.env`**。

### 3.3 mypy 修复清单（32 → 0）

按类型归类的修复落点：

| 类型                 | 修复方式                                                                                                           | 关键位置                                                                                                                                                                                                                                                         |
| ------------------ | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| openai SDK 类型      | `messages/tools` 参数 `cast(Any)`；流式响应 `cast(Any)`；tool\_calls 用 `getattr(tc,"function",None)` 兼容 CustomToolCall | [provider.py:113](file:///d:/PythonProject/Lun-Assistant/services/llm/provider.py)、[provider.py:164](file:///d:/PythonProject/Lun-Assistant/services/llm/provider.py)、[provider.py:175-178](file:///d:/PythonProject/Lun-Assistant/services/llm/provider.py) |
| redis async 返回联合类型 | `await` 调用处补 `# type: ignore[misc]`（沿用既有约定）                                                                    | `short_term.py` / `rate_limiter.py` / `dist_lock.py` / `circuit_breaker.py` / `skill.py`                                                                                                                                                                     |
| json\_mode 载荷      | `chat()` 签名返回 `str`，JSON 分支用 `isinstance(data, dict)` 判空后取键                                                    | [intent.py:122](file:///d:/PythonProject/Lun-Assistant/services/classifier/intent.py)、`tools_impl.py:140`                                                                                                                                                    |
| pymupdf 迭代         | `for page in doc` → `for i in range(doc.page_count)`（stub 无 `__iter__`）                                        | [parsers.py:76](file:///d:/PythonProject/Lun-Assistant/services/rag/ingest/parsers.py)                                                                                                                                                                       |
| 变量注解               | `out: dict[str, Any]`、`evidence/report` 显式注解、`saver/pool: Any`                                                 | [planner.py:68](file:///d:/PythonProject/Lun-Assistant/services/agent/planner.py)、[tiered.py:35](file:///d:/PythonProject/Lun-Assistant/services/checkpoint/tiered.py)                                                                                       |
| API 契约             | `TraceListOut(items=[TraceListItem(**row) ...])` 服务层 dict → 契约模型适配                                             | [observability/router.py:35](file:///d:/PythonProject/Lun-Assistant/api/observability/router.py)                                                                                                                                                             |
| 其他                 | `retry.py` `fn_name` 断言 str；`tool_registry` `asyncio.to_thread(cast(...))`                                     | [retry.py:46](file:///d:/PythonProject/Lun-Assistant/services/governance/retry.py)、[tool\_registry.py:91](file:///d:/PythonProject/Lun-Assistant/services/governance/tool_registry.py)                                                                       |

## 四、P0-3 依赖锁定

`requirements.txt` 全部依赖从 `>=` 收敛为 `==`（以 `pip freeze` 实测版本为准，如 `fastapi==0.141.1`、`langchain==1.3.18`、`sentence-transformers==6.0.1`），并补充数据库迁移 `alembic==1.19.1` 与开发工具 `mypy==2.3.1` / `ruff==0.16.5`。文件头注明升级流程：逐个 bump 并重跑 pytest / ruff / mypy / 冒烟。CI 安装命令简化为 `pip install -r requirements.txt`（不再单独 `ruff`）。

> 💡 **为什么锁定**：`>=` 让 CI / 协作者按最新版本解析，上游破坏性升级（如 langchain 0.x→1.x）会造成"本机能跑、CI 挂、装不上"的不可复现问题；锁定后回归可二分、供应链可审计，是工程严谨度的硬指标。

## 五、P0-2 Alembic 迁移骨架（暂停推进）

已建立迁移环境，替换 `create_all` 的前置完成：

- `alembic/env.py`：**异步引擎**执行迁移（与运行时 asyncpg 一致）；DSN 复用 `infrastructure.config.get_value("storage","postgres","async_dsn")`，不写死在 `alembic.ini`；`target_metadata = Base.metadata`（`infrastructure.models` 聚合全部 8 张表），后续 `alembic revision --autogenerate` 可一次生成完整初始迁移；pgvector `Vector` 类型内置 compare 支持。

- `alembic.ini` + `alembic/versions/`（骨架）。

> ⚠️ **暂停标注（2026-09-02）**：本机 PostgreSQL 服务端口/认证与本仓库 `.env`（5433）不一致，初始迁移未能 autogenerate 生成。按指示暂缓推进，`main.py` lifespan 仍保留 `create_all` 兜底保证可启动；待数据库环境就绪后补 `alembic revision --autogenerate` + `alembic upgrade head`，再移除 `create_all`。

## 六、P1-4 前端 ESLint + hooks 拆分

### 6.1 App.jsx 拆分

`App.jsx` 由 454 行收敛为纯组合层（状态逻辑全部下沉）：

| Hook          | 职责（文件）                                                                                 |
| ------------- | -------------------------------------------------------------------------------------- |
| `useTheme`    | 四主题 + 山水浓度：localStorage 持久化（裸字符串，与 `console/tuner.html` 互通）+ storage 跨 tab 联动 + 主题切换音效 |
| `useSessions` | 多会话卷册：localStorage 持久化（上限 30）、保底会话、`patchSession` 增量更新                                 |
| `useProjects` | 项目列表加载 + create/patch/delete CRUD + 弹窗态 + 档案刷新键                                        |
| `useChat`     | 对话发送 + SSE 流式编排（token 增量 / 时间线事件 / interrupt 续跑）                                       |

`App.jsx:21-45` 直接组合四个 hook；会话增删/切换的 streaming 锁定与 interrupt 清理保持在组合层。拆分后行为不变（build 通过验证）。

### 6.2 ESLint

- `eslint.config.js`：ESLint 9 flat config，引入 `eslint-plugin-react` / `react-hooks` / `react-refresh`；浏览器 globals（`vite.config.js` 走 Node globals，`scripts/` 截图工具排除）；关闭 React 18 下不适用的 `set-state-in-effect` 与 `react-in-jsx-scope`（新 JSX transform）、`prop-types`。

- `package.json:10` 新增 `lint` script（`eslint .`）；CI `deploy.yml:44-46` 在 build 前执行 `npm run lint`。

## 七、P1-5 常量 / 魔法数收敛

- **`_SSE_HEADERS`** **去重**：`conversation_service.py` 中的定义实为未引用死代码（唯一使用方是 `api/agent/router.py:21`），已删除，SSE 头收敛为路由层单一真源。

- **`output[:600]`** **命名化**：`conversation_service.py:24-25` 上提为 `_DECISION_ARCHIVE_CHARS = 600`，`_archive_decision` 归档决策记忆时引用（`:53`）。

- **`0.982`** 已在前序轮次收敛为 `services/rag/pipeline.py:27` 的 `_SPARSE_ONLY_PENALTY`，本轮复核无散落。

## 八、P2-6 docker-compose + 指标端点

### 8.1 docker-compose.yml

PostgreSQL(pgvector) + Redis 一键编排：镜像 `pgvector/pgvector:pg16` 与 `redis:7-alpine`，端口映射与本仓库 `.env` 一致（PG **5433** / Redis **6379**），数据卷持久化 + healthcheck。`docker compose up -d` 即可拉起全部依赖，便于演示环境复现。

### 8.2 运行指标端点

`api/observability/router.py:94-105` 新增 `GET /api/observability/metrics`（admin）：

- 进程级：运行时长 `uptime_s`（monotonic）、内存 `process_rss_mb`（psutil）；

- 业务级：`users / projects / trace_spans / audit_logs / knowledge_documents` 五表行数；

- **DB 容错**：数据库不可用时计数返回 `None`，进程指标仍可用（`_table_count` try/except 包裹），适合演示与探活。

## 九、仓库治理（迁移残留 / 临时文件 / 设计稿归档）

已在 commit `9fe5aad` 落地：

- 删除无实际内容的**迁移残留 stub**（`docs/OPTIMIZATION_ROUND7-11`、`design-concepts/CHANGELOG-*`、`frontend/CHANGELOG-v11.md` 等指针文件）；

- 删除前端调试残留 `frontend/_verify-upload/`、`vite.config.js.timestamp-*.mjs`；

- 设计稿资源从根目录 `design-concepts/` **归档至** **`docs/design-concepts/`**（git 识别为 rename）；

- 同步修正 `README` / `PROJECT_STRUCTURE` / `FORMAT_STANDARD` / `frontend-versions` 引用；`.gitignore` 补 Vite 临时文件规则。

## 十、验证与结论

| 门禁      | 命令                           | 结果                                              |
| ------- | ---------------------------- | ----------------------------------------------- |
| ruff    | `python -m ruff check .`     | All checks passed                               |
| mypy    | `python -m mypy`             | Success: no issues found in 81 source files     |
| pytest  | `python -m pytest tests/ -q` | 48 passed                                       |
| 前端构建    | `npm run build`              | ✓ built（298 modules）                            |
| 前端 lint | `npm run lint`               | 0 errors（2 条既有组件 `exhaustive-deps` warning，未阻塞） |

提交记录：`d07a5b6`（chore(ci)：静态检查+CI+类型修复）、`9fe5aad`（chore(clean)：仓库治理）。

## 十一、已知边界 / 未覆盖项

1. **Alembic 初始迁移未生成**：本机 PG 端口/认证与 `.env` 不一致，待环境就绪后生成初始迁移并验证 `upgrade head`，随后移除 `main.py` 的 `create_all`。
2. **前端既有组件 warning**：`KnowledgePanel` / `ProjectArchive` 的 `useEffect` 依赖 `load`（`exhaustive-deps`）为既有代码模式，本轮未改动（避免扩大无关改动）。
3. **依赖锁定基准**：`==` 固定为 2026-09 本机验证版本，升级需按文件头流程逐个验证。

## 十二、追溯 / 关联文档

- 本轮为求职展示优先级路线图（P0/P1/P2）的工程化落档；与此前"结构审查 → 重构 → ROUND6 工程治理"一脉相承。

- 关联文档：[ROUND6（工程化治理）](OPTIMIZATION_ROUND6.md)、[统一格式规范](FORMAT_STANDARD.md)、[项目结构说明](PROJECT_STRUCTURE.md)、[部署指南](DEPLOY.md)。

