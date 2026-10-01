# 论匠前端 · v18 六套设计语言（推翻重来） — 变更文档

> 文档域：frontend-versions
> 文档类型：版本变更
> 主题版本：v18
> 轮次：—
> 日期：2026-10-01
> 状态：已落地

> 一句话背景：v11–v17 的「主题」本质是**同一套结构换配色与材质**（最多 11 套），
> 结构与排版始终只有一种。本版把视觉层整个推翻重写：**六套完整设计语言**
> （铅字印刷 / 夜航仪表 / 学术海报 / 木牍竖排 / 孔版双色 / 索引档案），
> 配色、字体、排版、材质、动效性格全部不同，可在工作台内即时切换；
> 落地页每套皮肤一个独立 HTML。旧的「6 主题 + 柔化开关」体系整体删除。

---

## 一、总览（结论先行）

| 维度 | 上一版（v17） | 本版（v18） | 改动 |
|---|---|---|---|
| 视觉范式 | 1 套结构 × 6 主题 × 柔化开关 | **6 套独立设计语言** | 是 |
| 作用域载体 | `<html data-theme data-soft>` | `<html data-skin="a…f">` | 是 |
| 持久化键 | `lj_theme` / `lj_soft` | `lj_skin` | 是 |
| 主题注册 | `hooks/useTheme.js`（6 项 + 柔化） | `skins/registry.js`（6 项，单一真源） | 是 |
| 选择器 | `components/ThemePicker.jsx` | `components/SkinPicker.jsx` | 是 |
| 工作台样式 | `styles.css` 单文件 1712 行 | `styles/base.css` + `styles/panels.css` + `skins/*.css`（6 份） | 是 |
| 落地页 | `index.html` 单页双结构（CSS 换肤） | `index.html` + `landing-b…f.html`（6 个独立页） | 是 |
| 落地页共享行为 | `landing.js` 552 行内联 | `src/landing/shared.{js,css}`（六页共用） | 是 |
| 动效层 | 压在 `styles.css` 末尾约 420 行 | 抽为独立 `src/fx.css` | 是 |
| 圆角 / 材质 | 由柔化开关在两态间切换 | 各皮肤自带一种材质语言（0–2px，无柔化开关） | 是 |
| 后端 / 业务逻辑 | — | — | 否 |

变更结论：

1. **结构**：工作台仍是三栏 React SPA，业务逻辑（hooks / api / 面板组件）一行未改内核；
   但 DOM 的类名契约整体重写为 `.wb-*` 语义类，使六套皮肤能各自重排与重绘。
   皮肤 D 用 CSS Grid 把「会话卷册」从左侧竖列改为**顶部横向书签栏**——
   这是纯 CSS 的结构变化，未改 JSX。
2. **样式系统**：从「一份 CSS + 变量覆盖」改为「共享底座 + 每皮肤一份完整样式」。
   次级面板（知识库 / 项目档案 / 可观测 / 登录页）由 `styles/panels.css`
   统一实现一次，只吃皮肤令牌变量，因此六套皮肤自动获得匹配观感。
3. **token 维度**：令牌契约从 `--color-* / --radius-* / --shadow-*` 收敛为
   「明暗层次 / 文字 / 描边 / 强调 / 字体 / 动效 / 圆角 / 阴影 / 间距 / 字号」,
   契约文本见 [`../../frontend/src/skins/CONTRACT.md`](../../frontend/src/skins/CONTRACT.md)。
4. **响应式**：每套皮肤独立给出 `≤1380 / ≤1080 / ≤820` 三档；
   木牍皮肤在 `≤1080` 把竖排标题退回横排，避免移动端溢出。

---

## 二、文件级变更摘要

### 2.1 新增

| 文件 | 改动 | 类型 |
|---|---|---|
| `frontend/src/skins/registry.js` | 6 套皮肤的单一真源（id / 名称 / 色点 / 落地页 / theme-color） | 新增 |
| `frontend/src/skins/CONTRACT.md` | 皮肤契约：令牌表 + 类名表 + 书写规范 + 自检清单 | 新增 |
| `frontend/src/skins/a-letterpress.css` | 皮肤 A · 铅字印刷（契约参照实现） | 新增 |
| `frontend/src/skins/b-console.css` | 皮肤 B · 夜航仪表 | 新增 |
| `frontend/src/skins/c-poster.css` | 皮肤 C · 学术海报 | 新增 |
| `frontend/src/skins/d-bamboo.css` | 皮肤 D · 木牍竖排（含书签栏结构变化） | 新增 |
| `frontend/src/skins/e-riso.css` | 皮肤 E · 孔版双色 | 新增 |
| `frontend/src/skins/f-archive.css` | 皮肤 F · 索引档案 | 新增 |
| `frontend/src/styles/base.css` | 共享底座：重置 / 焦点 / 滚动条 / 弹窗骨架 / markdown 结构 / 令牌契约说明 | 新增 |
| `frontend/src/styles/panels.css` | 共享组件层：知识库 / 档案 / 可观测 / 登录页（只吃令牌） | 新增 |
| `frontend/src/fx.css` | 动效层（自 `styles.css` 末尾抽出并改用新类名） | 新增 |
| `frontend/src/hooks/useSkin.js` | 皮肤状态 + `<html data-skin>` + `lj_skin` + 跨页联动 | 新增 |
| `frontend/src/components/SkinPicker.jsx` | 皮肤选择器（6 宫格 + 揭幕式换肤 + 跳落地页） | 新增 |
| `frontend/src/landing/shared.js` | 落地页共享行为（切换器 / 入场 / 数字滚动 / 打字机 / 彩蛋三门 / 落笔处） | 新增 |
| `frontend/src/landing/shared.css` | 落地页共享样式（切换器 / 砚纸 / 彩蛋层 / reveal），取色走 `--lb-*` | 新增 |
| `frontend/src/demo.js` | **仅 DEV** 的开发预览数据（`?demo=1`），用于无后端时逐套核对皮肤 | 新增 |
| `frontend/landing-b.html` … `landing-f.html` | 皮肤 B–F 的落地页（各 523–670 行） | 新增 |
| `frontend/public/fig/*.jpg` | 落地页配图 3 张（铅字书桌 / 老式打字机 / 手稿批注），本地资产 | 新增 |

### 2.2 修改

| 文件 | 改动 | 类型 |
|---|---|---|
| `frontend/index.html` | 重写为皮肤 A 落地页（报头 / Hero / 跑马灯 / 读数 / 六环节 / 架构 / 协同 / 开始 / 页脚）+ 站根皮肤记忆跳转 | 修改 |
| `frontend/app.html` | 首帧前写入 `data-skin`；字体改为三档字族（宋 / 黑 / 等宽）共用一个 CDN 请求 | 修改 |
| `frontend/src/main.jsx` | 样式入口改为 base → panels → fx → 6 skins；说明加载顺序 | 修改 |
| `frontend/src/App.jsx` | 全部改为 `.wb-*` 语义标记；接 `useSkin`；新增会话拖拽重排、采纳盖章 | 修改 |
| `frontend/src/components/AuthPage.jsx` | 接 `SkinPicker`（原 `ThemePicker`）；类名改 `.auth-*` | 修改 |
| `frontend/src/components/Timeline.jsx` | 改为数据驱动的标签表，输出 `.wb-tl-*` 语义结构 | 修改 |
| `frontend/src/components/KnowledgePanel.jsx` | 橡皮章显示改为皮肤令牌驱动；新增 `demo` 分支 | 修改 |
| `frontend/src/components/ProjectArchive.jsx` | 新增 `demo` 分支 | 修改 |
| `frontend/src/components/TracePanel.jsx` | 新增 `demo` 分支 | 修改 |
| `frontend/src/hooks/useSessions.js` | 新增 `reorderSessions`（拖拽重排）与 `seed`（演示数据） | 修改 |
| `frontend/src/hooks/useProjects.js` / `useChat.js` | 新增 `demo` 分支（不发请求，走本地假数据） | 修改 |
| `frontend/src/fx.js` | `themeFlash` → `skinFlash`；新增 `stampAt`（采纳盖章） | 修改 |
| `frontend/vite.config.js` | 多入口扩到 7 个（站根 + 工作台 + 5 张皮肤落地页） | 修改 |

### 2.3 删除

| 文件 | 原因 | 类型 |
|---|---|---|
| `frontend/src/tokens.css` | 主题令牌层，被 `skins/*.css` 的皮肤令牌取代 | 删除 |
| `frontend/src/themes/{ops,blueprint,lab,press,soft}.css` | 6 主题的招牌装饰（约 1864 行） | 删除 |
| `frontend/src/styles.css` | 单份工作台样式（1712 行），动效层已抽为 `fx.css` | 删除 |
| `frontend/src/hooks/useTheme.js` | 主题注册 + 柔化开关 | 删除 |
| `frontend/src/components/ThemePicker.jsx` | 主题选择器 | 删除 |
| `frontend/src/landing.css` / `landing-themes.css` | 旧落地页样式（共 1625 行） | 删除 |
| `frontend/src/landing.js` | 旧落地页交互（552 行），彩蛋逻辑已移植进 `landing/shared.js` | 删除 |
| `frontend/src/InkBackground.jsx` | 山水背景分层（v17 已随主题体系失去引用） | 删除 |
| `frontend/public/console/tuner.html` | 调参台：只服务已删除的主题变量（75KB） | 删除 |
| `frontend/public/bg/bg-{a-soft,c-nightgold,d-jinbi}.webp` | 旧主题背景图（535KB） | 删除 |
| `frontend/design-samples/motion-lab.html` | v17 动效评审台，依赖已删除的 `tokens.css` | 删除 |
| `frontend/scripts/shot-themes.mjs` | 主题回归脚本，目标 `tuner.html` 已删除 | 删除 |
| `frontend/scripts/compress-bg-to-webp.py` | 背景图转换脚本，源图已删除 | 删除 |

---

## 三、全局工程变更

### 3.1 皮肤令牌契约

每套皮肤在 `html[data-skin="X"]` 下定义同一组变量；`base.css` / `panels.css` / `fx.css`
只消费这些变量，不认识任何具体皮肤。完整表见 `src/skins/CONTRACT.md` §二。

皮肤可用两个可选令牌改变共享组件的形态：

- `--stamp-display` / `--stamp-text-display`：知识库「已入库」是用椭圆朱章还是文字。
  A / D / F 用章，B / C / E 用文字。
- `--scan-display: none`：关闭 `fx.css` 的扫描线。A / C / D / E / F 关闭，B 保留
  （仪器台需要这条扫描线）。

### 3.2 皮肤切换链路

```
SkinPicker 点击
  → skinFlash(点击处, onCover)            fx.js：全屏圆形遮罩扩散
  → onCover 里 setSkin(id)                useSkin.js
  → <html data-skin=id>                   触发 6 份皮肤 CSS 之一生效
  → localStorage.lj_skin                  storage 事件使落地页 / 多标签同步
```

落地页侧不同：六种版式的 DOM 差异过大，**无法**靠 CSS 换肤，故每套皮肤一个 HTML；
`landing/shared.js` 选中目标后先铺一层主题色遮罩再跳转，避免白屏硬切。

### 3.3 首帧防闪

`app.html` 与各落地页都在 `<head>` 内联一小段脚本，在首帧前把 `data-skin` 写到
`<html>` 上（读 `localStorage.lj_skin`，非法值回退 `a`）。脚本被禁用时保持模板里的
默认皮肤，功能不受影响。

### 3.4 演示模式（仅 DEV）

工作台依赖 FastAPI + PostgreSQL + Redis + Ollama 才能登录并产生数据，
「换一套皮肤就要重起一遍全套服务」的代价过高。故 `src/demo.js` 提供纯前端 mock：

- 启动：`npm run dev` → `http://localhost:5173/app.html?demo=1`
- `isDemo()` 在 `import.meta.env.DEV === false` 时恒为 `false`，生产构建不进入该分支
- 数据本体用 `import.meta.env.DEV ? <字面量> : <空值>` 包裹，Vite 构建时折叠为常量，
  死代码连带 mock 数据一起被移除——已实测产物中不含演示会话 / 项目数据
  （bundle 334KB → 330.7KB）；仅面板组件里几条「演示模式：未接入后端…」的提示文案
  保留在不可达分支中，属可接受的常量开销
- demo 分支只做「不发请求、用本地数据」的短路，不改变任何真实链路

### 3.5 可玩性交互

| 交互 | 位置 | 实现 |
|---|---|---|
| 按钮磁吸 | 全部主按钮（`data-magnet`） | `fx.js` 写 `--mgx/--mgy`，上限 8px |
| 3D 倾斜 + 高光扫过 | 会话项 / 中断确认条 / 落地页图版（`data-tilt`） | `fx.js` 写 `--rx/--ry/--mx/--my` |
| 点击粒子 | 皮肤项 / 提示块 / 落地页 CTA（`data-burst`） | `fx.js` 在落点迸发一圈粒子 |
| 会话拖拽重排 | 工作台左栏（皮肤 D 为顶部书签栏） | `App.jsx` VolumeList：**轴向自适应**（见 §3.6）+ Pointer 事件，仅前端状态 |
| 采纳盖章 | 中断确认条里「采纳」类选项 | `fx.js` `stampAt()` 在落点砸一枚图章 |
| 落笔留墨 | 落地页右下「落笔处」 | `landing/shared.js`：外接框 + 笔数 + 笔迹长度三重判定 |
| 换肤揭幕 | 皮肤选择器 | `fx.js` `skinFlash()` |
| 全屏跳转遮罩 | 落地页切换皮肤 | `landing/shared.js` `transitionTo()` |

以上全部尊重 `prefers-reduced-motion`，命中时降级为静态或直接跳过。

### 3.6 会话拖拽的轴向自适应

会话卷册在 A/B/C/E/F 是左侧竖列（沿 Y 拖），而在 D「木牍竖排」被 CSS Grid
挪到了顶部横向书签栏（必须沿 X 拖）。`VolumeList` 不依赖皮肤类名或媒体查询，
而是**按前两项的实际排布方向判断轴向**：

```
horizontal = |rect[1].left - rect[0].left| > |rect[1].top - rect[0].top|
```

轴向决定三件事：起始坐标取 `clientX`/`clientY`、位移写成 `translateX`/`translateY`、
位次步长取相邻项的横向/纵向间距。横排时还会在指针贴近容器左右 48px 内自动滚动列表，
否则书签栏总宽超过容器，远处的位次拖不到。

另有两处必须同时满足的细节：

1. **拖拽中摘掉 `data-tilt`**：`fx.css` 的 `[data-tilt].tilt-on` 以 `!important`
   声明 transform，会压掉内联的位移，跟随手感就没了。
2. **拖拽中 `transition: none`**：皮肤可能给 `.wb-vol` 加了 transform 过渡
   （木牍的选中位移、孔版的贴纸归正），不关掉会让位移滞后指针一到两百毫秒。

### 3.7 彩蛋机关（移植）

v17 的三门手势与「落笔处」判定逻辑**原样移植**到 `src/landing/shared.js`，
六张落地页共用：

| 门 | 触发 | 目标页 |
|---|---|---|
| 手速门 | 皮肤按钮 5 秒内连点 ≥6 下 | `easter/dispatch.html` |
| 精读门 | 划选正文 ≥10 字并保持约 0.9s | `easter/hunt.html` |
| 书写门 | 在「落笔处」写成一个字 | `easter/brush.html` |

判定阈值、宽容模式、自动清纸（20s）、冷却（1.5s / 收层后 1.2s）、
解锁记录 `localStorage.lj_easter` 均与 v17 一致。
`public/easter/` 三枚彩蛋页本身未改动。

---

## 四、与相邻版本 / 轮次的关系

| 关联项 | 关系说明 |
|---|---|
| v15（十一主题） | 完全取代。v15 的 A–K 主题命名与 `design-samples/proposal-*` 保留为**设计档案**，不再参与构建 |
| v16（6 主题 + 柔化开关） | 整体删除。柔化开关这一机制被废弃——六套皮肤各自就是一种确定的材质语言，不再需要「锐 / 柔」两态 |
| v17（动效层） | **逻辑保留**：`fx.js` 全部导出沿用（`themeFlash` 更名 `skinFlash`，新增 `stampAt`）；样式抽为 `fx.css`；打字机平滑层在 `useChat.js` 中保持原样 |
| R18（落地页彩蛋） | 逻辑移植进落地页共享模块，三枚彩蛋页不变 |
| 设计稿 | 本版设计稿为六套工作台 + 六套落地页的静态 HTML，落稿前经逐套浏览器实测；设计**契约**沉淀在 `src/skins/CONTRACT.md` |

---

## 五、视觉验证清单（开发者自查）

- [x] `npm run lint` 通过（0 error）
- [x] `npm run build` 通过，7 个入口全部产出
- [x] 六套皮肤在工作台内逐套实测：三栏栅格、栏宽、顶栏高度、消息、中断条、时间线均按各自设计生效
- [x] 六套皮肤无横向溢出（`scrollWidth - innerWidth <= 0`）
- [x] 皮肤切换写入 `<html data-skin>` 与 `localStorage.lj_skin`，刷新后保持
- [x] 站根皮肤记忆跳转生效（`lj_skin=b` 时访问 `/` 会跳到 `landing-b.html`）
- [x] 六张落地页均挂上共享物：皮肤切换器 / 落笔处 / 彩蛋层 / 入场揭示 / 数字滚动 / 打字机
- [x] 皮肤 D 的「会话栏移到顶部书签栏」在两行 Grid 下成立，且 `≤1080` 正确回落
- [x] 选中态与首选项按钮在六套皮肤下均有足够对比度（逐套测 computed color/background）
- [x] `prefers-reduced-motion` 下无持续动画（`fx.css` 与 `base.css` 双重兜底）
- [x] 落地页配图全部走本地资产 `./fig/*.jpg`，首帧即可见，不再依赖外部出图接口
      （配图原本走远程文生图，实测该接口会把两张不同 prompt 解析成同一张方图，故改为本地生成）
- [x] 会话拖拽在竖列皮肤（A/B/C/E/F）走 `translateY`、在木牍的横排书签栏走 `translateX`，
      实测拖拽中的项 `hasAttribute('data-tilt') === false`，且 computed transform 与内联位移一致
      （即位移真的画出来了，未被 fx 的倾斜规则压掉）

---

## 六、同步与状态保留

- 持久化键：
  - `localStorage.lj_skin` —— 当前皮肤（`a`…`f`），落地页与工作台共用
  - `localStorage.lj_easter` —— 彩蛋解锁记录（沿用 v17 键名，升级不丢进度）
  - `localStorage.lj_token` / `lj_sessions_v1` —— 未改动
- **已废弃的键**：`lj_theme` / `lj_soft` 不再读写；用户升级后旧值留在 localStorage 里
  但不影响行为，皮肤会回退到默认 `a`
- 跨页签联动：`storage` 事件监听 `lj_skin`，任一页切换后其余页签实时跟随

---

## 七、已知边界 / 未覆盖项

1. **六份皮肤 CSS 全量打包**（`app.css` gzip 19.85KB）：为避免切换时异步拉取造成白帧，
   六份一起进入产物，而非按需动态加载。总量可控，属有意取舍。
2. **孔版皮肤的时间线「运行中」态**：JSX 无显式运行态类名，
   E 用 `:last-child` 邻接选择器近似点亮，语义不如显式类名精确。
3. **`design-samples/proposal-*` 与 `sample-*`**：v15 的设计档案，保留作历史参照，
   不参与构建；其中样张主题已不存在于代码中。
4. 暗色皮肤（B）下浏览器原生控件的配色只通过 `color-scheme` 提示，
   个别平台的 `<select>` 下拉列表仍可能沿用系统主题。
5. **落地页配图是 AI 生成的写实照片**：与真实摄影相比，细节（尤其是手部与键盘）
   放大后仍能看出生成痕迹；若要用于正式对外发布，建议替换为真实摄影素材。
   替换只需覆盖 `frontend/public/fig/` 下的同名文件，无需改代码。

---

## 八、追溯 / 关联文档

- 版本索引：[`README.md`](./README.md)
- 皮肤契约：[`../../frontend/src/skins/CONTRACT.md`](../../frontend/src/skins/CONTRACT.md)
- 动效工具箱：[`../../frontend/src/fx.js`](../../frontend/src/fx.js)
- 目录结构：[`../PROJECT_STRUCTURE.md`](../PROJECT_STRUCTURE.md)
- 格式规范：[`../FORMAT_STANDARD.md`](../FORMAT_STANDARD.md)

---

*变更版本：v18 · 六套设计语言（推翻重来）· 令牌契约化 · 后端零改动*