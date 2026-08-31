# 论匠 · 第一轮优化改进记录

> 日期：2026-08-31
> 范围：全维度审查后的 P0 批次（低风险、高收益项），共 5 项，全部落地并验证。

## 背景

对项目进行了代码结构、性能、可维护性、安全性、可扩展性、用户体验六个维度的全面审查，
形成 20+ 优化点清单并按投入产出比排序。本批次落地 P0（"简单难度 + 零/低风险 + 高可见收益"）5 项。

## 本轮改进明细

### 1. LLMProvider 客户端连接复用（性能）

**问题**：`LLMProvider()` 在专项 Agent 节点、6 类工具实现、意图分类器、Query 改写器中
被高频临时实例化，每次都新建 `AsyncOpenAI` 客户端（即新建 httpx 连接池），
每次工具调用都付出 TCP/TLS 握手开销。

**修复**：[core/llm/provider.py](../core/llm/provider.py) 增加模块级 `_client_cache`，
按 `(provider名, base_url, api_key)` 三元组复用客户端实例（AsyncOpenAI 线程安全）。

**收益**：工具密集型会话消除重复连接建立；多 provider 配置（ollama/deepseek/zhipu/qwen）互不干扰。

### 2. 审计中间件真异步化（性能）

**问题**：[app/middleware/audit.py](../app/middleware/audit.py) 注释声称 fire-and-forget，
实际 `await write_audit(...)` 同步阻塞每个 API 响应，每个请求平添一次 DB commit 延迟。

**修复**：审计落库改为 `asyncio.create_task` 真后台执行，异常仅记运行日志不丢响应。

**收益**：所有 API 请求响应时间减少一次同步写库开销（约 5-15ms/请求）。

### 3. 助手消息 Markdown 渲染（用户体验）

**问题**：LLM 输出大量 `###`/`**`/表格/列表语法，前端按纯文本渲染显示原始符号，演示效果差。

**修复**：
- [frontend/src/App.jsx](../frontend/src/App.jsx)：引入 `react-markdown` + `remark-gfm`，
  助手气泡走 Markdown 渲染（用户消息保持纯文本），外链默认新窗口打开；
- [frontend/src/styles.css](../frontend/src/styles.css)：补齐标题/列表/表格/代码块/
  引用块/分割线样式，代码块采用深色主题。

**验证**：`npm run build` 通过（310KB → gzip 97KB）。

### 4. 认证端点限流（安全）

**问题**：`/api/auth/login` 与 `/register` 无频率限制，可被无限尝试爆破口令。

**修复**：[app/auth/router.py](../app/auth/router.py) 接入治理层现成的 Redis 滑动窗口限流器
（ZSET + Lua 原子执行），按 `用户名+IP` 维度限制 5 次/分钟，超限返回 429。
设计为 fail-open：Redis 故障时放行请求，避免基础设施故障锁死全部用户。

**验证**：启动服务实测连续登录——前 5 次返回 401（密码错误），第 6 次起返回 429，
`/health` 不受影响。

### 5. 开发环境编码问题根治（可维护性）

**问题**：Windows 中文环境下 IDE 全局 `files.encoding` 配置为 `gbk`，导致：
- 新建 Python 文件为 GBK 编码，解释器报 `SyntaxError: Non-UTF-8 code`；
- diff 视图中 UTF-8 文件中文显示为乱码；
- 本轮开发中该问题重复出现 6+ 次，反复手工转码。

**修复**（双层）：
- IDE 全局设置 `files.encoding`: `gbk` → `utf8`（根因，保留 `autoGuessEncoding` 兼容旧 GBK 文件）；
- 项目根新增 [.editorconfig](../.editorconfig) 声明 `charset = utf-8` 兜底。

**附**：[.gitignore](../.gitignore) 修正前端目录名（`web/` → `frontend/`），
未跟踪文件从 2370 个降至 111 个（此前 node_modules 约 2200 个依赖文件被误纳入）。

## 验证清单

| 项 | 验证方式 | 结果 |
|---|---|---|
| 客户端复用 | `ast.parse` 语法 + 全部相关文件 UTF-8 编码检查 | 通过 |
| 审计异步化 | 服务启动 + `/health` + 登录流程 | 通过 |
| Markdown 渲染 | `npm run build` | 通过 |
| 认证限流 | 实测 7 次连续登录：`[401×5, 429×2]` | 通过 |
| 编码根治 | 修改后全部文件 UTF-8 校验 | 通过 |

## 后续优化路线（未落地，按优先级）

- **P1**：trace_spans/audit_logs 定期清理（表膨胀）、检索延迟优化（意图分层自适应改写开关，
  A/B 数据已支撑）、审计参数脱敏、tools.yaml 注册缓存
- **P2**：会话持久化（刷新恢复）、pytest 测试骨架、refresh token、结果导出
- **P3**（生产化前置，暂缓）：依赖方向重构、BM25 增量索引、EventHub 多实例扩展

## 追记：编码问题收尾修复（commit 802acab）

第 5 项编码根治落地后复查发现，部分在配置生效**之前**写盘的文件仍有遗留问题，分两类处理：

| 遗留问题 | 文件 | 处理 |
|---|---|---|
| GBK 编码但内容完好 | `api.js`、`index.html`、`requirements.txt` | 无损转码为 UTF-8 |
| 中文被替换为字面 `?`（数据丢失） | `App.jsx`（46 行）、`styles.css`（5 处注释） | 按原始版本重写恢复 |

全项目扫描确认无残留乱码，`npm run build` 通过。历史教训已固化：`.editorconfig`（项目级）
+ IDE 全局 `files.encoding=utf8` 双层防护，`autoGuessEncoding` 保留以兼容其他项目的旧 GBK 文件。
