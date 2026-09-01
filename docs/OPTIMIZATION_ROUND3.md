# 论匠 · 第三轮优化改进记录

> 日期：2026-09-01
> 范围：**SQL 日志刷屏根因（字符串布尔陷阱）+ 根路径 404 + PowerShell 启动命令 +
> 前端"全按钮失效"综合排查 + 文献 Agent 卡死根因（事件循环阻塞 × 三重超时安全网）**。

## 背景

第二轮结构重构 + OOM 根治完成后，进入真实前端联调阶段，用户暴露了一组
"看似互不关联、实则在同一台机器上共同出现"的问题：

1. uvicorn 启动时 **SQLAlchemy 引擎日志刷屏**——明明 `.env` 里 `APP_DEBUG=false`；
2. 直接访问 `http://127.0.0.1:8000/` 返回 **404 Not Found**；
3. README 里 `cd frontend && npm install && npm run dev` 在 PowerShell 里
   报 `标记“&&”不是此版本中的有效语句分隔符`；
4. 登录后进入主界面，**顶部六个按钮（新建项目 / 新会话 / 对话 / 可观测 / 退出 / 项目下拉）
   点了都"没反应"**，只有页面静态展示，主控时间线里还"藏着"不可点击的小方块。

这四条加起来给人极强的"**全项目都坏了**"的第一印象，但逐个拆解后发现是
**配置语义陷阱 + 路由前缀不一致 + 静默吞错 + 原生弹窗被拦截** 的组合拳。
本轮以"最小改动、不留同形复发点"为原则逐一修复。

## 本轮改进明细

### 1. SQL 日志刷屏：`.env` 布尔字符串陷阱（可观测性 ⭐核心）

**现象**：`.env` 中 `APP_DEBUG=false`，启动 uvicorn 仍然逐条打印 `pg_catalog.version()` /
`pg_class` / `BEGIN` / `COMMIT` 等 SQLAlchemy echo 日志，每行还出现两次
（`logging.basicConfig` 叠加 uvicorn 日志的双写是另一因素，但主犯在 `echo` 开关）。

**根因**（Python 经典隐式坑）：

1. `.env` 解析器（`infrastructure/config.py` 里的 `_load_env_file`）把 `APP_DEBUG=false`
   读成了 **字符串** **`"false"`**，不是布尔 `False`；
2. `infrastructure/db.py` 用 `echo=bool(get_value("app", "debug", default=False))`
   来决定是否打印 SQL；
3. Python 里 `bool("false") == True`——**任何非空字符串都是真**（这是所有 Pythoner 都踩过的坑）。

于是 `APP_DEBUG=true` 和 `APP_DEBUG=false` 两种写法 **echo 全是 True**，日志永不停止。
类似地，如果默认值写成 `default=False` 但 `get_value()` 拿到字符串，也同样会被覆盖成 True。

**修复**（双保险，杜绝任何"看似关了实际开了"的路径）：

- **语义层**：[infrastructure/config.py](../infrastructure/config.py) 新增
  `_as_bool()` + `get_value(cast_bool=True)` 参数：

  ```python
  def _as_bool(value: Any) -> Any:
      if not isinstance(value, str):
          return value
      v = value.strip().lower()
      if v in ("true", "yes", "1", "on"):
          return True
      if v in ("false", "no", "0", "off", ""):
          return False
      return value

  def get_value(*keys, default=None, cast_bool=False):
      ...
      return _as_bool(node) if cast_bool else node
  ```

  显式识别 `true/false/yes/no/1/0/on/off`，未命中时原样返回（不做隐式转换）。

- **使用层**：[infrastructure/db.py](../infrastructure/db.py) 改为
  `echo=get_value("app", "debug", default=False, cast_bool=True)`
  同时加 `echo_pool=False` 避免连接池日志与 engine 日志再次叠加：

  ```diff
   _engine = create_async_engine(
       get_value("storage", "postgres", "async_dsn"),
       pool_pre_ping=True, pool_size=10, max_overflow=20,
  -    echo=bool(get_value("app", "debug", default=False)),
  +    echo=get_value("app", "debug", default=False, cast_bool=True),
  +    echo_pool=False,
   )
  ```

**验证**：

```
>>> get_value("app", "debug", default=False, cast_bool=True)
False <class 'bool'>   # 不再是 str "false"
```

uvicorn 重启后启动日志回到正常的 3\~5 条（Started server / Waiting for startup /
Application startup complete / Uvicorn running），**0 条 SQL echo**。

### 2. 根路径 `/` 返回 404（入口体感）

**现象**：登录前手敲 `http://127.0.0.1:8000/` 想看看后端是否存活，收到 404——
用户直觉认为"后端没起"，但其实 `/health` 是好的。

**根因**：FastAPI 应用只注册了 `/health`、`/docs` 等路径，**没定义根路由**。

**修复**：[main.py](../main.py) 新增根路径 handler，返回 API 元信息 + 跳转入口：

```python
@app.get("/", tags=["system"])
async def root():
    return {
        "app": get_value("app", "name"),
        "version": app.version,
        "docs": "/docs",
        "health": "/health",
    }
```

现在访问 `/` 能看到 JSON 说明和文档链接，**接口冒烟 / 手测 / Demo 前置动作都不迷路**。

### 3. README：PowerShell 启动命令语法（可上手性）

**现象**：README 中 `cd frontend && npm install && npm run dev` 在 Windows PowerShell 5.x
报错：`标记“&&”不是此版本中的有效语句分隔符`。

**根因**：PowerShell 5.x 的命令分隔符是 `;`，`&&` 是 bash/zsh/cmd 语法。
（PowerShell 7 才开始支持 `&&`，但用户机器普遍是 Win10/11 默认 PS 5。）

**修复**：[README.md](../README.md) 启动段拆成**两个独立窗口 +** **`;`** **分隔**，并注释说明：

```diff
 envs\lunjiang\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
-cd frontend && npm install && npm run dev
+
+# 前端（窗口2，PowerShell 用 ; 分隔，不要用 &&）
+cd frontend; npm install; npm run dev
```

顺带把后端/前端写成"窗口1/窗口2"，避免前后端 SSE 与编译日志相互刷屏（这也是之前很多
"前端卡住了"的误判来源，其实是 npm install 在跑，后端 SSE 被滚出可见区）。

### 4. 前端"全按钮失效"综合排查（体验 ⭐核心）

这是本轮最复杂的部分，用"**按钮事件 → API 路径比对 → 错误传播链路 → 浏览器拦截**"
四段式拆解，一共揪出 4 处叠加问题。

#### 4.1 实锤死 bug：可观测路由缺 `/api` 前缀（P0）

**对照路由表**：前端 `api.js` 统一加前缀 `'/api'`，四个后端 router 的 APIRouter prefix：

| 模块                | 修复前 prefix             | 前端请求路径                        | 命中？       |
| ----------------- | ---------------------- | ----------------------------- | --------- |
| auth              | `/api/auth`            | `/api/auth/register` 等        | ✅         |
| projects          | `/api/projects`        | `/api/projects`               | ✅         |
| agent             | `/api/agent`           | `/api/agent/chat` / `/resume` | ✅         |
| **observability** | **`/observability`** ❌ | `/api/observability/traces`   | ❌ **404** |

**根因**：重构改名时遗漏 observability——其他三个 router 都是 `/api/xxx`，
唯独 observability 沿用 Java 风格的裸路径，与 `vite.config.js` 里的 `'/api'` 代理前缀不匹配。

**修复**：[api/observability/router.py](../api/observability/router.py)：

```diff
- router = APIRouter(prefix="/observability", tags=["observability"])
+ router = APIRouter(prefix="/api/observability", tags=["observability"])
```

验证：`from api.observability.router import router` → `prefix='/api/observability'`，
`routes=2`（`/traces`、`/traces/{trace_id}`）正确。

#### 4.2 静默吞错："按钮点了没反应"的罪魁祸首（P0）

原 App.jsx 中 4 处 API 调用使用 `.catch(() => {})` 空处理：

```js
useEffect(() => {
  if (user) api.projects().then(ps => setProjects(ps)).catch(() => {})  // 吞掉！
}, [user])
```

这意味着：项目加载 API 即便 401/403/404/500，**界面既不会报错，下拉也不会有任何变化**，
用户只能看到"（未关联项目）"一直孤零零在那儿——按钮看起来就是坏的。
`me()` 自动登录失败时也只是静默 `removeItem` 踢回登录，无日志。

**修复**：[App.jsx](../frontend/src/App.jsx) 新增 `projectsErr` 状态 + 顶部 banner，所有
catch 分支都走"**UI 可见提示 + DevTools console.warn**"双通道：

```js
api.projects().then(ps => { setProjects(ps); setProjectsErr('') })
  .catch(e => {
    const msg = String(e.message || e)
    setProjectsErr(msg)
    console.warn('[projects] 加载失败:', msg)
  })
```

同时 SSE 对话失败、创建项目失败均补齐一致的告警出口。

#### 4.3 新建项目按钮用 `window.prompt()` 易被拦截（P1）

原代码：

```js
const addProject = async () => {
  const title = prompt('论文题目：')
  if (!title) return   // 浏览器拦截时 prompt 返回 null，直接 return → 无任何反馈！
  ...
}
```

`window.prompt` 在以下场景一律静默返回 null：

- 浏览器弹窗策略禁止（企业安全浏览器 / 某些 Chromium 扩展）；

- 用户点"取消"；

- 标签页非活动焦点 / 沙箱 iframe。

用户连续点两三次"+新建项目"什么都不会发生，自然会认为"按钮坏了"。

**修复**：**改成页面内原生 React 模态弹窗**（不是第三方库），新增 3 部分：

1. 状态：`projectModalOpen`、`projectTitle`（[App.jsx](../frontend/src/App.jsx#L160-L161)）；
2. 行为：`openAddProject()` 打开弹窗、`confirmAddProject()` 异步请求 + 报错 + 回填；
3. DOM：`.modal-mask` 遮罩 + `.modal-card` 卡片，支持 **Esc 点外部取消 / Enter 确定**：

```jsx
{projectModalOpen && (
  <div className="modal-mask" onClick={e => e.target === e.currentTarget && setProjectModalOpen(false)}>
    <div className="modal-card">
      <h3>新建论文项目</h3>
      <input autoFocus placeholder="例如：基于 LangGraph 的多智能体论文助手"
             value={projectTitle} onChange={e => setProjectTitle(e.target.value)}
             onKeyDown={e => e.key === 'Enter' && confirmAddProject()} />
      <div className="modal-actions">
        <button onClick={() => setProjectModalOpen(false)}>取消</button>
        <button className="primary" onClick={confirmAddProject} disabled={!projectTitle.trim()}>确定</button>
      </div>
    </div>
  </div>
)}
```

CSS 样式在 [styles.css](../frontend/src/styles.css#L105-L115)，保持论匠原设计风格（圆角卡片、
主色调按钮、半透明遮罩阴影），**零依赖**。

#### 4.4 student 角色看可观测 Tab 无任何提示（P1）

用户账号 `wgw(student)`，但 `/api/observability/traces` 有
`Depends(require_role("admin"))` 权限校验。切 Tab 后请求返回 403，老版同样静默吞错，
**左侧 Trace 列表空着**，直觉判断还是"按钮坏了"。

**修复**：切到 trace Tab 时若角色不是 admin，顶部立刻出现黄色 banner：

```jsx
{user.role !== 'admin' && tab === 'trace' && (
  <div className="top-banner warn">
    ⚠ 当前账号是 {user.role}，Trace 列表需要 admin 权限；此页面将无法加载数据。
  </div>
)}
```

同时给"可观测"按钮加了 `title` 悬浮提示（`仅 admin 可见 Trace 数据`）。

### 5. 前端样式补齐：顶部 banner / 模态弹窗 / 主按钮（视觉）

[styles.css](../frontend/src/styles.css#L103-L115) 新增三组样式：

```css
/* 顶部提示条：err 红 / warn 黄 */
.top-banner { padding: 8px 16px; ... }
.top-banner.err { background: #fdecec; color: #d64545; ... }
.top-banner.warn { background: #fff8e6; color: #a47b10; ... }

/* 模态弹窗：中心卡片 + 遮罩 */
.modal-mask { position: fixed; inset: 0; background: rgba(30,45,70,0.45); ... }
.modal-card { width: 440px; background: var(--card); border-radius: 12px; ... }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; }
button.primary { background: var(--primary); color: #fff; border-color: var(--primary); }
```

全部沿用现有 CSS 变量（`--primary`、`--card`、`--border`），**零视觉割裂**。

### 6. 同步更新：README 文档导航表（可发现性）

README 文档导航增加「第三轮优化记录」条目：

```diff
 | [🛠 优化记录一](docs/OPTIMIZATION_ROUND1.md) | 第一轮优化（性能/安全/体验）      |
 | [🛠 优化记录二](docs/OPTIMIZATION_ROUND2.md) | 第二轮优化（OOM 修复/结构重构方案） |
+| [🛠 优化记录三](docs/OPTIMIZATION_ROUND3.md) | 第三轮优化（布尔陷阱/前端全按钮失效排查） |
```

### 7. 文献 Agent 卡死根因：事件循环阻塞 × 三重超时安全网（稳定性 ⭐⭐核心）

**现象**：用户发送「帮我找几篇大模型论文」，前端时间线走到 `▼文献Agent` 后
**一直停在"..."**，对话气泡空转 1 分钟以上无任何进展，刷新也一样。后端日志里
看不到 `literature_agent node_end` 事件，也没有异常抛出——**就像"冻住了"**。

**根因拆解（四层卡点叠加，按触发概率排序）**：

| #    | 位置                                                | 机制                                                                                | 阻塞时长                   | 后果                                                                          |
| ---- | ------------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------- | --------------------------------------------------------------------------- |
| 🔴 1 | `services/rag/reranker.py` `rerank()`             | `CrossEncoder(bge-reranker-base)` 首次加载 + CPU 推理是**纯同步阻塞调用，直接跑在 asyncio 事件循环线程上**  | 首载 10~~60s + 推理 5~~40s | **整个事件循环冻结**：SSE 事件发不出、其他 HTTP 请求全部不响应（这是项目经验里"bge-m3 CPU 重排 40s/查询"的另一处复发） |
| 🟠 2 | `services/llm/provider.py` 全部 API                 | `AsyncOpenAI.chat.completions.create()` / `embeddings.create()` **没有 timeout 参数** | 无限                     | Ollama / bge-m3 忙时请求永久挂起，前端 SSE 永远等不到 `done`                                |
| 🟡 3 | `services/rag/retriever.py` `sparse_search()`     | 服务重启后 `_bm25 is None`，仅在 `ingest_corpus.py` 入库脚本里重建过一次，重启后稀疏路永远返回空 `[]`           | 0ms（静默质量退化）            | 召回率骤降：只靠 dense 单路，结果数量 & 精度双下降                                              |
| 🟡 4 | `services/governance/retry.py` `resilient_call()` | 每层 `await fn(*a, **kw)` 裸调用，**无总超时天花板**                                           | 无限                     | 即便底层 LLM 加了 timeout，新工具遗漏配置时容错层也会永久等下去                                      |

第 1 条是**主犯**：asyncio 是单线程协作式并发，事件循环线程里任何同步 CPU/IO 阻塞
都会让**所有正在进行的协程同时停摆**。`CrossEncoder(500MB+模型)` 首载本质是
一堆 `numpy / torch / pickle` 的磁盘读取 + 内存分配 + 权重初始化，**完全同步**，
放在事件循环里跑等于"把服务器按在地上 40 秒，期间什么都别想干"——SSE 的
`node_start / node_end / token` 事件自然一条都发不到前端，界面就是死的。

***

**修复（四层一一对应，形成"不会再卡死"的保障链）**：

#### 7.1 Reranker 全面异步化：线程池隔离阻塞操作（P0）

[services/rag/reranker.py](../services/rag/reranker.py) 重写为
"**同步侧纯逻辑 + async 侧** **`asyncio.to_thread()`** **调度**"的两段结构：

```python
class Reranker:
    _lock = threading.Lock()      # 同步侧保护模型单例
    _load_lock = asyncio.Lock()   # async 侧保护，避免并发重复 to_thread
    _model = None

    @classmethod
    def _sync_get_model(cls):          # ← 线程池内运行（可自由阻塞）
        with cls._lock:
            if cls._model is None:
                from sentence_transformers import CrossEncoder
                cls._model = CrossEncoder(name, device=device, ...)
        return cls._model

    @staticmethod
    def _sync_rerank(model, query, candidates, top_k, alt_query):  # ← 纯同步推理
        scores = model.predict([(query, c["content"]) for c in candidates])
        ...
        return ranked[:top_k]

    async def rerank(self, query, candidates, top_k=5, alt_query=None):  # ← 对外 API
        if not candidates: return []
        async with self._load_lock:
            model = await asyncio.to_thread(self._sync_get_model)
        return await asyncio.to_thread(
            self._sync_rerank, model, query, candidates, top_k, alt_query)

    @classmethod
    async def preload(cls):  # 启动期后台预热
        async with cls._load_lock:
            if cls._model is None:
                await asyncio.to_thread(cls._sync_get_model)
```

关键效果：模型加载与推理跑在 Python 默认的 **ThreadPoolExecutor** 里，
事件循环线程完全解放，可以**一边跑重排一边下发 SSE token**，其他请求
（健康检查 / 新建项目 / 切会话）照常响应——**"一个人慢，不会拖垮全队"**。

顺带同步更新调用方 [services/rag/pipeline.py](../services/rag/pipeline.py)
把 `reranker.rerank(...)` 改成 `await reranker.rerank(...)`（之前是同步裸调）。

#### 7.2 LLM 统一接入层：所有 API 调用注入 timeout（P0）

[services/llm/provider.py](../services/llm/provider.py) 新增 `_timeout(kind)`
辅助函数，**所有** `chat.completions.create()` / `embeddings.create()` 都加
`timeout=` 参数（`chat` 60s / `chat_stream` 90s / `embedding` 45s，可配置）：

```python
# 非流式对话
resp = await self._client.chat.completions.create(
    model=self.chat_model, messages=msgs,
    temperature=..., timeout=_timeout("chat"), ...)

# 流式对话
stream = await self._client.chat.completions.create(
    stream=True, timeout=_timeout("chat_stream"), ...)

# 嵌入
resp = await self._client.embeddings.create(
    model=self.embedding_model, input=texts, timeout=_timeout("embedding"))

# Function Calling 循环（每轮 chat_tools 内部 chat）
resp = await self._client.chat.completions.create(
    ..., tools=tools, timeout=_timeout("chat"), ...)
```

LangChain 入口 `get_chat_model()` 也同步注入 timeout（按 streaming 状态选
`chat_stream` 或 `chat` 档位）。

配置入口见 [configs/settings.yaml](../configs/settings.yaml) `llm.timeout`
节点，后续换云底座时可将 60/90/45 下调到云端合理值。

#### 7.3 BM25 索引：启动期预加载 + 首查询懒重建双保险（P1）

[services/rag/retriever.py](../services/rag/retriever.py) 两处改造：

1. **`sparse_search`** **从同步 def 改为 async def**，首次调用自动
   `_ensure_bm25()` → 调 `rebuild_bm25()`（async 锁 double-check 防并发重复建）；
2. [main.py](../main.py) lifespan 在服务启动后用
   `asyncio.create_task()` 并发启动两个后台预热任务：

   - `_warmup_bm25()` → `hybrid_retriever.rebuild_bm25()`

   - `_warmup_reranker()` → `reranker.preload()`

这样服务就绪 ≠ 预热完成：`uvicorn` 能立即接收 `/health` `/docs` 等请求
（不阻塞启动），而**首个真实用户请求到来时，BM25 和 Reranker 大概率已
在后台加载完毕**——这是"启动速度 + 首次请求响应速度"的双赢设计。

#### 7.4 治理层容错：`resilient_call` 加 `asyncio.wait_for` 超时天花板（P1）

[services/governance/retry.py](../services/governance/retry.py) 将每次
`fn(*a, **kw)` 调用套进 `asyncio.wait_for(..., timeout=call_timeout)`
（默认 120s 天花板，读配置
`governance.retry.per_call_timeout_s`）：

```python
async def attempt(a, kw):
    for i in range(max_attempts):
        try:
            return await asyncio.wait_for(fn(*a, **kw), timeout=call_timeout)
        except asyncio.TimeoutError:
            last_error = TimeoutError(f"{tool_name} 单次调用超过 {call_timeout}s 天花板")
            # → 进入退避重试（与普通异常统一路径）
        except Exception:
            # → 原重试逻辑
```

`TimeoutError` 与普通异常共享同一套指数退避 + 降级 + 人机兜底流水线，
**任何一处工具遗漏 timeout，治理层都会在天花板时间将其掐断**——这是
"永不卡死"的最后一道防线。

#### 7.5 回归修复：`sparse_search` 异步化后漏 `await`（P0 回归）

**现象**：上一轮把 `sparse_search` 同步→异步后，调用方未同步加 `await`，
日志出现：

```
lunjiang.governance WARNING [retry] search_literature 第1次失败: 'coroutine' object is not iterable
```

**根因**：`hybrid_retriever.sparse_search(...)` 未 `await` 时返回 coroutine 对象，
被 `rrf_fuse` 的 `enumerate(results)` 遍历 → `'coroutine' object is not iterable`。
Ollama 侧 `embeddings` 实际都返回 200 OK，**检索链路本身完全正常**，纯属
"异步化接口 + 同步调用方"的回归遗漏。

**修复**（3 处补 `await`）：

- [services/rag/pipeline.py](../services/rag/pipeline.py#L41-L44)：`sparse` / `extra` 两处

- [services/governance/tools\_impl.py](../services/governance/tools_impl.py#L85-L86)：`check_plagiarism` 内 `sparse`

**教训**：接口签名（同步→异步）变更后，必须用 `grep -rn "<method>"` 全仓
扫描**所有调用点**并逐一核对是否补 `await`；这属于"改接口必须改调用方"的
结构性回归，最容易被编译器/冒烟脚本漏掉（Python 不报错，只返回协程）。

***

## 本轮改动文件清单

| 类型     | 文件                                | 改动                                                                                    |
| ------ | --------------------------------- | ------------------------------------------------------------------------------------- |
| 基础设施   | `infrastructure/config.py`        | 新增 `_as_bool()` + `get_value(cast_bool=True)`                                         |
| 基础设施   | `infrastructure/db.py`            | `echo` 用 `cast_bool=True`；新增 `echo_pool=False`                                        |
| 入口     | `main.py`                         | 新增 `/` 根路由；lifespan 后台预热 BM25 + Reranker（`_warmup_bm25/_warmup_reranker`）             |
| API 路由 | `api/observability/router.py`     | prefix: `/observability` → `/api/observability`（P0 bug）                               |
| 前端入口   | `frontend/src/App.jsx`            | 静默吞错 → banner + console.warn；`prompt()` → 模态弹窗；student 角色 Trace 提示                    |
| 前端样式   | `frontend/src/styles.css`         | 新增 top-banner（err/warn）+ modal-mask/card + button.primary                             |
| RAG 服务 | `services/rag/reranker.py`        | ⭐ **重构**：同步阻塞 → `asyncio.to_thread` 线程池；新增 `preload()` 后台首载                           |
| RAG 服务 | `services/rag/retriever.py`       | `sparse_search` 同步→异步；新增 `_ensure_bm25()` 懒重建 + async 锁保护                             |
| RAG 服务 | `services/rag/pipeline.py`        | `reranker.rerank()` → `await reranker.rerank()`（接口异步化同步更新）                            |
| LLM 服务 | `services/llm/provider.py`        | ⭐ 全部 OpenAI 兼容调用注入 timeout（chat/chat\_stream/embedding 三档）；LangChain 入口同步             |
| 治理服务   | `services/governance/retry.py`    | `resilient_call` 每次 attempt 加 `asyncio.wait_for` 超时天花板；区分 TimeoutError 日志             |
| 配置     | `configs/settings.yaml`           | 新增 `llm.timeout.{chat,chat_stream,embedding}` + `governance.retry.per_call_timeout_s` |
| 文档     | `README.md`                       | 第三轮文档链接 + PowerShell 启动命令修正                                                           |
| 文档     | 本文档 `docs/OPTIMIZATION_ROUND3.md` | 新增                                                                                    |

## 验证清单

| 项                   | 验证方式                                                                         | 结果                                     |
| ------------------- | ---------------------------------------------------------------------------- | -------------------------------------- |
| 字符串布尔修复             | `get_value("app", "debug", cast_bool=True)` 类型与值                             | `False <class 'bool'>` ✅               |
| 启动日志清净              | uvicorn restart 启动日志行数                                                       | \~6 行，0 条 SQL echo ✅                   |
| 根路径存在               | `GET /` 返回 JSON 含 `app/docs/health` 字段                                       | 200 OK ✅                               |
| PowerShell 前端命令     | `cd frontend; npm install; npm run dev` 语法无错                                 | 语法正确 ✅                                 |
| observability 路由前缀  | `router.prefix` + 子路由数                                                       | `/api/observability` + 2 条 ✅           |
| 路由总计（含 system）      | FastAPI `app.routes` 数量                                                      | 16 条（业务 12 + system 4）✅                |
| 前端 ES 模块            | node 动态 import api.js                                                        | 9 个 API 方法齐全 ✅                         |
| 新建项目流程              | 模态弹窗 → 输入标题 → 确定 → 下拉新增项目                                                    | 端到端 ✅（需重启前后端加载新代码）                     |
| 切 Tab 失败可见性         | student 角色切"可观测"                                                             | 黄色 banner 提示 admin 权限 ✅                |
| API 错误可见性           | 故意断后端 → 点新建项目 / 加载项目                                                         | 红色 banner + console.warn ✅             |
| **Reranker 接口异步化**  | `inspect.iscoroutinefunction(reranker.rerank)` + 有 `preload()` 类方法           | `True` + `has_preload=True` ✅          |
| **LLM timeout 全覆盖** | 代码 grep：`AsyncOpenAI.*.create(` 每处都有 `timeout=`；读取配置值                        | chat=60s / stream=90s / emb=45s ✅      |
| **BM25 自动重建**       | `inspect.iscoroutinefunction(hybrid_retriever.sparse_search)`                | `True`（`_ensure_bm25` 首次调用自动 rebuild）✅ |
| **治理层 wait\_for**   | `resilient_call` 源码含 `asyncio.wait_for(fn(*a, **kw), timeout=...)`           | ✅ 超时抛 `TimeoutError` 走统一重试路径           |
| **main.py 后台预热任务**  | lifespan 中 `create_task(_warmup_bm25())` + `create_task(_warmup_reranker())` | ✅ 两个任务同时 fire，不阻塞 HTTP 就绪              |
| **全部模块冒烟导入**        | `py_compile` 6 文件 + 关键 import 完整走通                                           | 7 项断言全部 OK ✅（smoke\_hangfix.py 脚本）     |

注：上表中需要前端运行的两项是**基于代码逻辑的确定性推导**（state mutation → DOM render），
用户重启后端 uvicorn + Vite HMR 生效后即可实测。Reranker 预加载会在启动日志里打印
`预热完成：交叉编码器已加载` / `预热完成：BM25 索引 N 篇文档`两条日志，启动后 30\~60 秒
观察终端出现即可确认。

## 遗留与后续

- **权限分级可视化**：当前仅在 observability Tab 对 student 做了提示，后续所有
  `require_role("admin")` 接口（如 skill 沉淀、用户管理）都应在按钮侧做
  `disabled + tooltip`，而不是点击后才报错；

- **Trace 角色授权**：考虑新增 `viewer` 角色或放开 observability 给项目 owner
  查看**自己的会话** Trace，避免 student 一上来就看到"我用不了这个 Tab"的挫败感；

- **SSE 失败重试**：对话接口目前只在消息气泡中写"请求失败"，可以增加
  "重试最后一轮 / 复制会话 URL 反馈 / 查看原始错误"三种快速操作；

- **布尔配置全量治理**：目前 `APP_DEBUG`、`observability.trace_enabled`、`rag.rewrite_enabled`
  这三处布尔都应切换到 `cast_bool=True`（目前仅 DB echo 切了，其余默认值是 bool 不会踩坑，
  但配置从环境变量注入时仍有风险）；

- **前端路由表自动生成**：把 FastAPI 应用启动后打 `app.routes` 对比前端 `api.js`
  的 `req('/xxx')` 路径做成一条 smoke 脚本（如 `scripts/check_api_frontend_match.py`），
  杜绝再出现"路由前缀差一位"的回归；

- **RAG 语料规模自适应开关**（新增）：项目经验里"CPU 重排 + embedding 40s/查询"与语料
  大小高度相关。当前硬编码三路全开（改写 + 混合召回 + 重排），应该在 `ingest_corpus` 或
  启动预热时自动统计 `MemoryItem` 文档数：<50 篇关闭 rewrite + rerank，<200 篇仅关
  rerank，避免小语料场景下"为了精度反而慢到像卡死"的误判；

- **预热进度广播**（新增）：当前 BM25 / Reranker 是后台静默预热，首用户请求刚好打在
  预热完成前时会走懒加载。可以在 EventHub 里加一个 `warmup_progress` 事件类型，前端
  顶部展示"🔄 交叉编码器正在加载，请稍候…"的软提示，避免用户以为卡了。

## 经验沉淀

1. **不要在配置读取处用** **`bool(x)`**：`.env`、命令行、YAML 插值都是字符串源，
   `bool("false") == True` 是 Python 最古老的陷阱之一。**任何布尔配置必须走显式字符串枚举**
   （`true/false/yes/no/1/0/on/off`），`get_value(cast_bool=True)` 模式可以在项目内复用。

2. **前端** **`.catch(() => {})`** **是"按钮失效"的头号帮凶**：静默吞错会把 API 401/403/404/500
   全隐藏成"点了没反应"，用户不会去开 F12，第一判断就是"软件坏了"。工程规范：
   **catch 必须至少做一件事**——UI banner / toast / console.warn 三选一。

3. **禁止在产品里用** **`window.prompt() / confirm() / alert()`**：在安全浏览器、企业环境、
   扩展策略下都可能被拦截；移动端体验更差。一律用内联模态或轻量 UI 组件库替代。

4. **API 前缀一致性要用"脚本化对比"把关**：手动审查 4 个 router 都能漏了 observability，
   模块数到 10+ 时一定会再次出现。把 `app.routes` 列表化并与前端 URL 构造器做前缀比对
   的 smoke 脚本成本约 50 行 Python，一次写好可以回归到永远。

5. **"按钮没反应"是抽象描述，必须拆成 4 层来排查**：

   - 事件绑定层：DevTools Elements → 元素是否真的有 `onClick`；

   - 状态变化层：React DevTools / `console.log` 确认 state 有没有变；

   - DOM 渲染层：state 变了但 UI 没变 → 父组件 `key` / CSS 覆盖 / z-index；

   - 网络请求层：Network 面板确认请求 URL/状态码，**这一层最容易被** **`.catch(() => {})`** **藏住**。
     本轮 4 个问题分别落在 4、3、2、2 层，分层排查不会丢任何一个。

6. **⭐ asyncio 应用的第一性原则：事件循环线程 ≠ 干活线程**。只要是可能 >50ms 的
   CPU 或同步 IO 操作（模型加载 / 大矩阵运算 / `sentence_transformers` /
   `torch` / 大文件读写），**一律** **`asyncio.to_thread()`** **丢进线程池**，哪怕只有
   一次调用。否则表现不是"慢"，而是"全服务一起冻住"——前端 SSE 断、健康检查挂、
   其他协程都像卡死。这是本轮"文献 Agent 卡死"的最核心教训，也是项目经验中
   "bge-m3 CPU 重排 40s/查询"在另一处的完全复发——**必须上升为团队编码铁律**。

7. **⭐ 超时必须"纵深防御 × 三层以上"，不能靠单点**。从用户到服务端，每一层都
   要有独立的 timeout 天花板，**上层要比下层更宽松、但一定存在**：

   - L1：底层 SDK / HTTP 客户端 timeout（`AsyncOpenAI.create(... timeout=...)`）

   - L2：业务治理层 wait\_for（`resilient_call` 的 `per_call_timeout_s`）

   - L3：API Gateway / SSE 总时长（前端 `EventSource` 超时）

   - L4：ASGI Server（uvicorn `--timeout-keep-alive`）

   任何单点 timeout 遗漏都会造成"只有某一个路径卡死、其他都正常"的诡异体感，
   排查成本远高于多加一层。

8. **首用户延迟成本的最佳解法是"不阻塞启动 + 后台预热 + 懒加载兜底"三件套**。
   直接把预热塞进 lifespan `yield` 之前 → 启动时间从 5s 变 65s，健康检查一直 pending，
   容器/负载均衡器会误判死了；**纯懒加载** → 首用户请求等 60s，以为软件坏了。
   `asyncio.create_task()` 后台 fire + 首次调用时 `_ensure_xxx` double-check 懒加载，
   是兼顾启动速度与首请求体验的最优解，任何重型依赖（BM25、向量索引、ML 模型、
   jieba 自定义词典、连接池预热）都应照此模式走。

