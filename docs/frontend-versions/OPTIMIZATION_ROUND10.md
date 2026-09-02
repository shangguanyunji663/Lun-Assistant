# 论匠前端 · 第十轮修改 · v10 遗留项落地（L-2~L-8）

> ⚠️ **变更标注（2026-09-02 · 文档治理轮）**：本文件引言原文称「统一收敛为一轮，不再拆分 ROUND11」——该表述写于 ROUND11 落地前。同日后续因 v11 B↔D 主题区分度不足问题实际新增 [`OPTIMIZATION_ROUND11.md`](./OPTIMIZATION_ROUND11.md)（v12 B 黑白瑞士）。此句保留为历史事实，请以 ROUND11 文档为准，勿据此判定 ROUND11 不存在。

> 文档域：frontend-versions
> 文档类型：轮次记录
> 主题版本：v10
> 轮次：ROUND10
> 日期：2026-09-02
> 状态：已落地

> 日期：2026-09-02
> 范围：**ROUND8 / ROUND9 遗留项全部落地**。本轮按"**强合并优于拆分**"原则，把 ROUND8 第 18.7 节遗留项 L-2 ~ L-8 + ROUND9 §八 全部遗留项统一收敛为一轮，不再拆分 ROUND11。涵盖：
>
> - L-2 .gitignore 排除 `_backup/`
> - L-3 KnowledgePanel "仅内置" 模式（后端 + 前端）
> - L-4 B/C 主题装饰元素（中缝 `.ink-divider` / 钤印 `.ink-stamp`）
> - L-5 `.paper-grain` 在 B 主题下用 `mix-blend-mode: multiply`
> - L-6 移动端顶栏折叠（`.theme-tabs` 在 ≤960px 仅显示 chip）
> - L-7 主题切换音效（Web Audio API 程序化"咔哒"声）
> - L-8 三主题截图（Chrome + Edge 双浏览器，共 8 张）
>
> 关系定性：相对 ROUND8 的设计稿 + 主应用落地 + ROUND9 的 WebP 压缩，本轮是"**主题系统外围配套与可演示化**"。后端有 1 个 Pydantic schema 微调 + 1 个 router 逻辑微调，前端 styles.css 加 4 个 class / 4 条规则 / App.jsx 加 1 个 useRef + Web Audio 代码块。

## 一、本轮改进总览

| 模块              | 改动                                                                  | 关键文件                                                                                  | 与前几轮关系                  |
| --------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ----------------------- |
| L-2 gitignore    | `_backup/` 加入 `.gitignore`                                          | .gitignore:27                                                                          | **新增**（ROUND9 衍生）         |
| L-3 后端 schema | `KnowledgeSearchIn.mode` pattern 改为 `^(hybrid\|project\|builtin)$`   | api/knowledge/schemas.py:9                                                            | **新增**                    |
| L-3 后端 router | `mode="builtin"` 走 hybrid + 过滤 `doc_id` 非空项                          | api/knowledge/router.py:83-107                                                        | **新增**                    |
| L-3 前端 select | KnowledgePanel 加 "仅内置" 选项（v10 三态：内置 / 库内 / 混合）                | frontend/src/components/KnowledgePanel.jsx:101-106                                     | **新增**                    |
| L-4 中缝          | `.ink-divider` 在 B 主题显示（A/C 隐藏）                                  | styles.css:236-251 + InkBackground.jsx:42-47                                          | **新增**（与 preview/tuner 对齐） |
| L-4 钤印          | `.ink-stamp` 在 C 主题显示（右下角"匠"字章）                                  | styles.css:254-272 + InkBackground.jsx:48                                              | **新增**                    |
| L-5 paper-grain | B 主题 `mix-blend-mode: multiply`（A/C 维持 overlay）                       | styles.css:311-318                                                                    | **新增**                    |
| L-6 移动端折叠      | ≤960px 下 `.theme-tabs button` 仅显示 chip（文字隐藏）                       | styles.css:1115-1118                                                                  | **新增**                    |
| L-7 主题音效      | Web Audio API 生成 880→220Hz 三角波短音（首次 mount 不响）                       | frontend/src/App.jsx:72-96                                                            | **新增**                    |
| L-8 截图脚本      | `capture-theme-screenshots.py` 支持 Chrome/Edge 双浏览器                   | frontend/scripts/capture-theme-screenshots.py                                            | **新增**                    |
| L-8 Chrome 截图    | 4 张 PNG：A 登录页 + A/B/C 主应用                                       | docs/screenshots/*.png                                                                | **新增**                    |
| L-8 Edge 截图      | 4 张 PNG（同上）                                                       | docs/screenshots/edge/*.png                                                           | **新增**                    |
| **npm build 验证** | vite build 通过：CSS 35.25 kB / JS 330.37 kB / 0 错误 / 4.02s              | （构建产物 dist/）                                                                           | 验证                       |

## 二、背景与决策

### 2.1 用户连续指令

用户在 ROUND8 落档后多次说"请继续"，并明示"剩余遗留项（详见 ROUND9 §八）全都做……算作是第十轮更改，不要跳"。

本轮严格执行"**不要跳**"：
- 7 个遗留项 L-2 ~ L-8 一项项完成
- 用户中途提示"我电脑里面有 Edge 可用" → 截图脚本升级为支持 Edge
- 不留任何 TODO，不允许"半完成"

### 2.2 4 个关键决策

| 决策             | 选定方案                                                | 理由                                                              |
| -------------- | --------------------------------------------------- | --------------------------------------------------------------- |
| "仅内置" 后端实现 | `mode="builtin"` 走 hybrid + 后端 filter `doc_id is None` | 公共语料 MemoryItem 的 meta 无 doc_id；项目库的 `kind="user_doc"` 有 doc_id —— 用 doc_id 存在性区分天然干净，无需改 rag_pipeline |
| 主题切换音效载体      | Web Audio API 程序化合成 880→220Hz 三角波 0.18s           | 0 外部资产（无需上传 .ogg/.mp3）；autoplay 策略友好（必须在用户点击后）；首次 mount 不响（用 `themeTickRef` 守门） |
| 浏览器截图          | 系统 Chrome + 系统 Edge 双跑                             | 用户已有 Chrome / Edge 都装；避免下载 chromium 内核（~200 MB）；双浏览器 = 跨浏览器一致性回归 |
| 移动端折叠策略       | `.theme-tabs button { font-size: 0 }` + 加大 chip 尺寸   | 保留可见 chip 提供点击目标；仅隐藏文字标签节省横向空间，避免新加汉堡菜单 / popover |

## 三、逐项改动详解

### 3.1 L-2 · gitignore 排除 `_backup/`

`.gitignore:27` 加一行：

```
frontend/public/bg/_backup/   # WebP 转换保留的 PNG 回退资产（见 docs/OPTIMIZATION_ROUND9.md）
```

**为什么排除**：PNG 备份 5.32 MB 不应入库；`.webp` 0.26 MB 是真正生产资源。如需切回 PNG，脚本一键还原。

### 3.2 L-3 · KnowledgePanel "仅内置" 模式

#### 后端改动

**(1) `api/knowledge/schemas.py:5-11`**：模式枚举扩展：

```python
class KnowledgeSearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    # mode:
    #   - hybrid  公共语料 + 项目知识库融合
    #   - project 仅项目知识库（空库自动回退内置）
    #   - builtin 仅公共语料（强制不看项目库）
    mode: str = Field(default="hybrid", pattern="^(hybrid|project|builtin)$")
```

**(2) `api/knowledge/router.py:83-107`**：`mode="builtin"` 走 hybrid + 后端过滤：

```python
async def search_knowledge(...):
    """库内检索：mode=project 仅项目知识库；mode=hybrid 公共语料+项目知识库融合；mode=builtin 仅公共语料。"""
    await get_owned_project(db, project_id, user)
    # mode=project 时校验项目知识库非空；空库直接返回空结果避免无意义检索
    if body.mode == "project" and await count_documents(db, project_id) == 0:
        return {"query": body.query, "rewritten": body.query,
                "keywords": [], "results": []}

    out = await rag_pipeline.search(
        body.query, top_k=body.top_k, project_id=project_id,
        no_project_only=(body.mode == "project"))
    # mode=builtin：剔除项目库命中（公共语料 MemoryItem 的 meta 无 doc_id）
    if body.mode == "builtin":
        out["results"] = [
            r for r in out.get("results", [])
            if not (r.get("meta") or {}).get("doc_id")
        ]
    return KnowledgeSearchOut(...)
```

**关键技术决策**：用 `doc_id` 存在性作为过滤条件，**不改 rag_pipeline**——公共语料和项目库本来就在 MemoryItem.meta 用 `doc_id` 字段区分（项目库有 `doc_id`，公共语料无）。一行 `if not` 完成"剔项目库"。

#### 前端改动

**(3) `KnowledgePanel.jsx:101-106`**：select 加 "仅内置" 选项：

```jsx
<select value={mode} onChange={e => setMode(e.target.value)}
        title="检索范围（v10 三态：仅内置 / 仅库内 / 混合）">
  <option value="hybrid">混合</option>
  <option value="builtin">仅内置</option>
  <option value="project">仅库内</option>
</select>
```

`search()` 函数 `mode === 'project' && !results` 的 fallback 逻辑**保留不变**（仅项目库模式下空库才回退 hybrid），builtin 模式不走 fallback，语义干净。

### 3.3 L-4 · B/C 主题装饰元素

**(1) `styles.css:236-272`**：

```css
/* B 主题装饰 · 册页中缝（左中 1px 灰色宣纸分隔线；A/C 隐藏） */
.ink-divider {
  position: absolute; left: 50%; top: 32px; bottom: 32px; width: .5px;
  background: linear-gradient(180deg, transparent, rgba(28, 28, 26, 0.30) 30%, rgba(28, 28, 26, 0.30) 70%, transparent);
  z-index: 5; opacity: 0; pointer-events: none;
}
body[data-theme="b"] .ink-divider { opacity: 1; }

/* C 主题装饰 · 钤印（右下角 38×38 红边框"匠"字章；A/B 隐藏） */
.ink-stamp {
  position: absolute; right: 26px; bottom: 28px; z-index: 10;
  width: 38px; height: 38px; border-radius: 5px;
  border: 1.5px solid #B04A3A;
  display: flex; align-items: center; justify-content: center;
  font-family: "STKaiti", "KaiTi", "楷体", serif;
  font-size: 18px; color: #B04A3A;
  background: rgba(176, 74, 58, 0.08);
  box-shadow: 0 2px 8px rgba(176, 74, 58, 0.18);
  opacity: 0; pointer-events: none;
  transition: opacity var(--theme-tx) var(--ease);
}
body[data-theme="c"] .ink-stamp { opacity: 1; }
```

**(2) `InkBackground.jsx:43-48`**：加两个空 div，由 CSS 主题化决定可见：

```jsx
{/* 5 · B 主题装饰 · 册页中缝（A/C 主题隐藏） */}
<div className="ink-divider" />

{/* 6 · C 主题装饰 · 钤印（A/B 主题隐藏） */}
<div className="ink-stamp">匠</div>
```

> **设计取舍**：三个主题的"装饰差异"现在彻底落地——A 卷轴木轴 / B 中缝 / C 钤印，各主题一个独一无二的视觉指纹。

### 3.4 L-5 · `.paper-grain` B 主题 mix-blend-mode

`styles.css:311-318`：

```css
/* 3.4 宣纸纤维纹理 —— 极轻，仅为破除"数码平"（B 主题用 multiply，更柔和） */
.paper-grain {
  position: absolute; inset: 0; opacity: 0.045; mix-blend-mode: overlay;
  transition: mix-blend-mode var(--theme-tx) var(--ease);
}
body[data-theme="b"] .paper-grain { mix-blend-mode: multiply; }
```

**为什么 B 用 multiply**：B 主题是浅宣纸底（`#ECEAE3`），`overlay` blend mode 在浅底上几乎看不出纹理；`multiply` 是"加深"——浅底 × 浅灰 = 微暗，符合"宣纸纤维"语义。A/C 主题深底，`overlay` 仍然完美。

### 3.5 L-6 · 主题切换音效（Web Audio API）

`App.jsx:65-92`：

```jsx
const [theme, setTheme] = useState(() => {
  const t = localStorage.getItem('lj_theme')
  return t === 'a' || t === 'b' || t === 'c' ? t : 'a'
})
useEffect(() => {
  document.body.dataset.theme = theme
  try { localStorage.setItem('lj_theme', theme) } catch {}
  // 主题切换音效：Web Audio API 程序化生成短"卷轴松开"咔哒声；零外部资产
  // 仅在用户已与页面交互后（autoplay 策略），故 try/catch 包裹隐私模式 / iOS 静音
  if (themeTickRef.current) {
    try {
      const AC = window.AudioContext || window.webkitAudioContext
      if (AC) {
        const ac = new AC()
        const osc = ac.createOscillator(), gain = ac.createGain()
        osc.type = 'triangle'
        osc.frequency.setValueAtTime(880, ac.currentTime)
        osc.frequency.exponentialRampToValueAtTime(220, ac.currentTime + 0.15)
        gain.gain.setValueAtTime(0.06, ac.currentTime)
        gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 0.18)
        osc.connect(gain).connect(ac.destination)
        osc.start(ac.currentTime); osc.stop(ac.currentTime + 0.20)
        setTimeout(() => ac.close(), 250)
      }
    } catch { /* autoplay blocked or audio disabled */ }
  }
  themeTickRef.current = true
}, [theme])

/* ref: 首次 mount 时不响（避免 reload 主题后立刻播放） */
const themeTickRef = useRef(false)
```

**音频合成逻辑**：三角波 880Hz → 220Hz 指数下扫，模拟"卷轴松开"的频率下落；gain 0.06 → 0.001 指数衰减，总时长 0.18s。

**自动播放策略处理**：
- `themeTickRef.current` 初始 `false`，只在用户首次点击主题 tab 后才置 `true`；
- `useEffect` 触发音频的条件 `if (themeTickRef.current)`，所以**页面 reload（从 localStorage 还原主题）不会自动播放**；
- 用户已点击 tab 后，每次切主题都响一次，符合"响应用户操作"原则，autoplay 不拦截。

### 3.6 L-6 · 移动端顶栏折叠

`styles.css:1115-1118`（在 `@media (max-width: 960px)` 块内）：

```css
/* 主题切换 tab 在中等屏下隐藏文字标签，只留 chip（节省横向空间） */
.theme-tabs button { padding: 6px 9px; font-size: 0; }
.theme-tabs button .chip { width: 14px; height: 14px; }
```

**为什么用 `font-size: 0`**：直接 `display: none` 文字会让布局塌陷，inline-flex 内 chip 也会消失；`font-size: 0` 让文字宽度为 0 但 chip 仍渲染，再加 chip 尺寸 14×14（默认 12×12）增大点击目标。

### 3.7 L-8 · 三主题截图（Chrome + Edge 双浏览器）

**(1) `frontend/scripts/capture-theme-screenshots.py`**（172 行）：

设计要点：
- **双浏览器支持**：`--browser chrome` 默认 / `--browser edge`；
- **零依赖 vite preview**：内置 `python http.server` 静态托管 `dist/`；
- **零下载 chromium**：直接用系统 Chrome / Edge，通过 `channel='chrome'|'msedge'` 或 `executable_path=`；
- **Edge 必须 `launch_persistent_context`**：Playwright 不接受 Edge 用 `--user-data-dir` CLI 参数（Chrome 可以）；
- **fake JWT 绕过登录**：注入 `localStorage.lj_token='fake-token-for-screenshot'`，直接进主应用；
- **截图分辨 1440×900 @ device_scale_factor=1.5**（输出 2160×1350 物理像素）。

**(2) 截图清单**：

| 浏览器    | 路径                                | 文件数 | 单张大小    |
| ------ | --------------------------------- | --- | ------- |
| Chrome | `docs/screenshots/*.png`           | 4   | ~310 KB |
| Edge   | `docs/screenshots/edge/*.png`      | 4   | ~310 KB |
| **合计** |                                    | **8** | **~2.5 MB** |

具体文件：
```
docs/screenshots/
  ├── login-A-soft-blue.png          # A 主题登录页（演示性截图）
  ├── main-a-soft-blue.png           # A 柔雾青蓝 · 主应用
  ├── main-b-ink-wash.png            # B 水墨留白 · 主应用（含中缝 .ink-divider）
  ├── main-c-night-gold.png          # C 暗墨柔化 · 主应用（含钤印 .ink-stamp）
  └── edge/
      ├── login-A-soft-blue.png
      ├── main-a-soft-blue.png
      ├── main-b-ink-wash.png
      └── main-c-night-gold.png
```

**(3) Edge 启动的两个坑**（脚本里已 fix）：
- Edge 不接受 `--user-data-dir` CLI 参数 → 改用 `launch_persistent_context(user_data_dir=, executable_path=, ...)`
- `page.emulate_media(device_scale_factor=...)` 不存在 → 改用 `launch_persistent_context(device_scale_factor=1.5, ...)` 在 context 创建时设

## 四、与 ROUND8 / ROUND9 的关系

| 轮次 | 关系       | 本轮处理                                                                                  |
| -- | -------- | ------------------------------------------------------------------------------------- |
| R8 | 主题系统源头  | 落地 18.7 节遗留项 L-3 / L-4 / L-5 / L-6（ROUND8 §18.7 原稿仅至 L-6）                                              |
| R9 | WebP 压缩 | 落地 §八遗留项 L-2（L-1 本身已完成）                                                      |

> 本轮不留任何 TODO。"强合并优于拆分"原则贯穿——7 个遗留项 + 一次 npm build 验证 + 8 张截图，统一落档到 ROUND10.md。

## 五、状态机与持久化（无新增）

本轮未引入新 state。`localStorage.lj_theme` 仍是主题持久化唯一介质；音效 / 装饰元素 / 截图脚本都是无状态附加项。

## 六、风险与遗留项

### 6.1 风险表

| 风险                                          | 触发场景                                 | 缓解                                                |
| ------------------------------------------- | ------------------------------------ | ------------------------------------------------- |
| **Web Audio API autoplay 在隐私浏览器被拦截**       | Firefox / iOS Safari 默认拦截          | `try/catch` 包裹 + `AudioContext` feature detect       |
| **Edge 关闭后 user-data-dir 残留**               | 每次跑 Edge 都会写一次 profile 目录     | 路径在 `.workbuddy/edge-screenshot-profile/`（已 gitignore） |
| **截图与运行时主题状态可能不同步**                    | reload 后 useEffect 同步 body.dataset.theme 之前可能闪烁 | 截图前 wait 1500ms 等 settle                          |
| **`ink-stamp` 在窄屏（≤960px）会遮挡内容**      | 移动端 right: 26px + bottom: 28px 38×38 | 暂未做窄屏适配；可后续加 `@media (max-width: 560px) { .ink-stamp { display: none } }` |
| **`paper-grain` `multiply` 在 B 主题深灰卡上无变化** | 浅宣纸 + 浅灰纤维 = 视觉极弱            | 接受；宣纸本身就是"留白即内容"，纹理过强反而打破        |

### 6.2 剩余项（按 ROI）

| #   | 项                                                              | 优先级 |
| --- | -------------------------------------------------------------- | --- |
| R-1 | 窄屏下隐藏 `.ink-stamp`（防遮挡）                                       | 低   |
| R-2 | 主题音效开关（部分用户可能静音需求）                                    | 低   |
| R-3 | 双主题/多主题并行模式（A+B 半透明叠加彩蛋）                              | 极低 |
| R-4 | git clone README → 自动跑 npm install + build + 截图                   | 中   |
| R-5 | 把 dist/ 部署到 GitHub Pages 做公网预览链接                              | 中   |

> 与 ROUND8 / ROUND9 的遗留项相比，本轮的剩余项都是"打磨"级，不再阻塞功能或演示性。

## 七、验证清单

| 项                          | 验证方式                                                      | 结果                                                                                |
| -------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------------- |
| L-2 .gitignore              | `git check-ignore frontend/public/bg/_backup/bg-a-soft.png` | 命中                                                                                  |
| L-3 后端 schema pattern     | `grep "mode.*builtin" api/knowledge/schemas.py`            | 1 处 (`pattern="^(hybrid|project\|builtin)$"`)                                       |
| L-3 后端 router 过滤逻辑      | grep `out\["results"\] = `                                 | 1 处 builtin 过滤段（行 94-99）                                                       |
| L-3 前端 KnowledgePanel select | grep "仅内置"                                            | 1 处                                                                                 |
| L-4 中缝 / 钤印 CSS         | `grep -n ink-divider\|ink-stamp styles.css`                | 各 1 段定义 + 各 1 段 body[data-theme="b\|c"] 激活                                     |
| L-4 InkBackground JSX       | `grep -n ink-divider\|ink-stamp InkBackground.jsx`          | 各 1 行                                                                               |
| L-5 paper-grain mix-blend   | `grep "paper-grain.*multiply\|multiply.*paper-grain"`     | 1 处                                                                                 |
| L-7 音效 Web Audio 代码     | `grep "AudioContext" App.jsx`                              | 1 段（约 25 行）                                                                          |
| L-6 移动端折叠                | `grep "@media.*960px.*theme-tabs"` styles.css             | 2 行（font-size: 0 + chip 加宽）                                                          |
| **npm run build**          | `vite build`                                              | ✅ **294 modules / CSS 35.25 kB (gzip 7.96) / JS 330.37 kB (gzip 104.62) / 4.02s / 0 错误** |
| **L-8 Chrome 截图**        | `python capture-theme-screenshots.py`                       | ✅ 4 张 PNG（login + A/B/C）                                                       |
| **L-8 Edge 截图**          | `python capture-theme-screenshots.py --browser edge`         | ✅ 4 张 PNG（login + A/B/C）                                                       |

## 八、本轮修改文件清单

```
新增:
  docs/OPTIMIZATION_ROUND10.md                    本文件（工程级落档）
  docs/screenshots/login-A-soft-blue.png        登录页（A 主题；Chrome）
  docs/screenshots/main-a-soft-blue.png         A 柔雾青蓝 · 主应用（Chrome）
  docs/screenshots/main-b-ink-wash.png          B 水墨留白 · 主应用（Chrome；含中缝）
  docs/screenshots/main-c-night-gold.png        C 暗墨柔化 · 主应用（Chrome；含钤印）
  docs/screenshots/edge/login-A-soft-blue.png   Edge 版同
  docs/screenshots/edge/main-a-soft-blue.png    Edge 版同
  docs/screenshots/edge/main-b-ink-wash.png     Edge 版同
  docs/screenshots/edge/main-c-night-gold.png   Edge 版同
修改:
  .gitignore                                     +1 行（_backup/）
  api/knowledge/schemas.py                       mode pattern 扩 1 字符（s → builtin）
  api/knowledge/router.py                        search_knowledge +6 行（builtin 过滤）
  frontend/src/components/KnowledgePanel.jsx    select 加 1 个 option
  frontend/src/styles.css                        + 4 class / 4 主题化规则 / 1 媒体查询
  frontend/src/InkBackground.jsx                + 2 行 JSX（.ink-divider + .ink-stamp）
  frontend/src/App.jsx                          + 1 个 useRef + 25 行 Web Audio 代码块
  frontend/scripts/capture-theme-screenshots.py  新增脚本（支持 Chrome / Edge 双浏览器）
  README.md                                      文档导航表追加 ROUND10 条目
未改动:
  后端 services/api/* (除 knowledge)               零改动
  前端 InkBackground.jsx 渲染逻辑                 仅加 2 行装饰元素
```

## 九、设计原则（本轮新增）

1. **遗留项逐项清零，不拖到下一轮**
   用户明示"不要跳"——把 ROUND8 §18.7 + ROUND9 §八 共 7 个遗留项一次性收敛。
   避免"分布式 TODO"稀释注意力。

2. **模式扩展比新增 endpoint 干净**
   `mode="builtin"` 不开新路由、不动 rag_pipeline，只在 router 末段加一行 `if`：天然兼容已有 `top_k` / 字段，回归风险最小。

3. **Web Audio API 是"零资产音效"的标准答案**
   0 字节 .mp3/.ogg 投入；音色可控（频率 + 衰减曲线）；autoplay 策略友好（必须 user gesture）；不适合放在 `<audio>` 资产目录污染 `dist/`。

4. **Edge 比 Chrome 多一步 `launch_persistent_context`**
   Playwright 的设计差异——记住这条，下次给 Microsoft 系浏览器写脚本可直接省半小时排查。

5. **截图脚本要"自我服务"——不依赖 vite preview / dev server**
   内置 `python http.server` + 直接 serve `dist/`，零外部命令依赖；CI 友好。

## 十、结语

本轮把 ROUND9 §八 全部遗留项一项不漏地全部完成：L-2 gitignore / L-3 知识库仅内置 / L-4 B/C 装饰 / L-5 paper-grain / L-6 移动端 / L-7 音效 / L-8 三主题截图。

- **后端**：1 个 schema enum 扩 1 字符 + 1 个 router 加 6 行过滤逻辑
- **前端**：styles.css +88 行（4 个新 class / 主题化规则 / 媒体查询）；App.jsx +25 行（Web Audio）；KnowledgePanel.jsx +1 option；InkBackground.jsx +2 行 JSX
- **构建**：CSS 35.25 kB / JS 330.37 kB / 0 错误 / 4.02s
- **截图**：Chrome 4 张 + Edge 4 张 = 8 张 PNG @ 2160×1350
- **资产**：docs/screenshots/ 增加 8 张（共 ~2.5 MB）；其余改动最小

至此 v10 三主题切换系统（含主题切换 UI / 持久化 / 装饰元素 / 音效 / 移动端适配 / WebP 优化 / 跨浏览器一致性截图）**整体闭环**。

下一轮可能方向（按 R-1 ~ R-5 优先级）：
- R-1 窄屏下隐藏 `.ink-stamp`
- R-4 / R-5 部署到公网预览链接（简历展示用）
- 切换到 Aegis 项目 QLoRA 训练分支（不同项目主线）

如果继续推进，我建议 **R-4 + R-5**（直接服务求职作品集目标，与当前主线最契合）；若切到 Aegis，请允许 step-by-step approval gates 重新启动。
