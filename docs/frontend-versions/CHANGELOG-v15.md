# 论匠前端 · v15 现代艺术四主题 — 变更文档

> 文档域：frontend-versions
> 文档类型：版本变更
> 主题版本：v15
> 轮次：ROUND17
> 日期：2026-09-30
> 状态：已落地

> 一句话背景：用户需求「推翻固有模板思路、保留旧 7 版复古主题共存，为主页与工作台新增现代艺术方向」。四方向样图（frontend/design-samples/）经用户确认后全量落地：工作台新增 H/I/J/K 四主题（A-G 零改动共存，切换器达 11 主题）；落地页新增编辑部双结构（light/dark 显示经典六段，h/i/j/k 显示编辑部版式）。

---

## 一、总览（结论先行）

| 维度 | 上一版（v14） | 本版（v15） | 改动 |
|---|---|---|---|
| 工作台主题 | A–G 七版 | A–K **十一版**（+H/I/J/K） | 是 |
| 落地页主题 | 亮/暗 双主题 | **六主题**（亮/暗 + 编辑部四版） | 是 |
| 落地页结构 | 单结构（六段） | **双结构共存**（#ln-site / #ed-site） | 是 |
| 旧 7 版视觉 | — | **零改动**（追加式接入） | 否 |
| 字体资产 | 系统栈 | + Noto Serif SC 700/900 / Archivo Black / IBM Plex Mono（CDN + 系统栈回退） | 是 |
| 图片资产 | — | 零新增（纹理全 CSS 内联） | 否 |

四主题设计语言：

| 主题 | id | 底色 | 强调 | 标题字体 | 个性签名 |
|---|---|---|---|---|---|
| H 墨格编辑部 | `h` | 纸白 `#FAF8F3` | 朱红 `#C8341F` 单轴 | Noto Serif SC 900 | 期刊目次行、实墨线分隔、墨黑 CTA、近直角 |
| I 新构成主义 | `i` | 米白 `#F4F1EA` | 克莱因蓝 `#2B4BC7`（+镉红/芥末） | 黑体 Heavy | 全直角、硬阴影位移 hover、网格纸纹理 |
| J 夜航诗意 | `j` | 近黑 `#0B0C10` | 荧光青 `#4FE3C1`（+琥珀橙 `#FF7A45`） | IBM Plex Mono（拉丁）/系统黑体（中文） | 星点层、信号灯选中线、青→橙 CTA 切换 |
| K 拓印套色 | `k` | 纸白 `#FBF6EC` | 荧光粉 `#FF48B0`（×靛蓝 `#2B3AAB`） | Noto Serif SC 900 | 双色网点纸、套色错位阴影、套印标题 |

---

## 二、文件级变更摘要

| 文件 | 改动 | 行号范围 | 类型 |
|---|---|---|---|
| `frontend/app.html` | 字体 CDN link（preconnect + css2） | 9–12 | 新增 |
| `frontend/src/hooks/useTheme.js` | THEMES 注册 h/i/j/k；VALID_THEMES 扩容 | 5–21 | 修改 |
| `frontend/src/styles.css` | §21 v15 四主题令牌 + 个性覆盖 | 1649–2036 | 新增 |
| `frontend/index.html` | head 字体 link；#ln-site 包裹；#ed-site 编辑部结构 | 全文件（350 行） | 修改 |
| `frontend/src/landing.css` | §13 ed-site 双结构 + 四主题变体 + --ln-* 映射 | 765–1056 | 新增 |
| `frontend/src/landing.js` | 六主题循环切换 + 双结构 display 切换 | 7–31 | 修改 |
| `frontend/public/console/tuner.html` | H/I/J/K 接入（THEMES/BG_MAP/tab/CSS 覆盖/文案） | 全文件 | 修改 |

---

## 三、全局工程变更

### 3.1 工作台四主题（styles.css §21，1649 起）

接入方式与 v13 E/F/G 完全一致（body[data-theme] 令牌覆盖 + 个性覆盖选择器），要点：
1. **纹理零图片**：`.ink-bg::after` 承载 i 网格纸 / j 星点 / k 双色网点；H 纯纸。
2. **装饰层全静**：ink-photo/veil/blob/divider/stamp/wood-roll 均 display:none，木轴语言由边框承担。
3. **CTA 定制**：H 墨黑底纸白字（hover 转朱红）；I 镉红 + hover 硬阴影位移；J 荧光青黑字（hover 琥珀 + 光晕）；K 荧光粉深字（对比 4.66:1）+ 靛蓝套色阴影。
4. **字体覆盖**：H/K 覆盖 `--font-kai` 为 Noto Serif SC 栈（brand/空态标题/弹窗标题 900 字重）；J 覆盖为 IBM Plex Mono（中文回落系统黑体，落档标注）。
5. **面板实色化**：chat-col/side-col/trace-panel/sessions/auth-card 全部 `backdrop-filter: none`（E/F/G 模式延续）。

### 3.2 落地页双结构共存（landing.css §13，765 起）

- `#ln-site`：现有六段结构原样包裹，light/dark 下显示，样式零改动。
- `#ed-site`：编辑部版式（期刊 masthead / 三行揭示 hero / marquee / 目次 / 指标带 / 工作台 mock / 版权页），内容与六段同源（文案/评测数字直接复用）；h/i/j/k 下显示，四主题经 `--ed-*` 变量 + 个性覆盖驱动。
- 双结构由 landing.js 按 `body[data-theme]` 切 display；display none→block 使 CSS 入场动画（ed-rise 逐行揭示）在每次切换时自动重播。
- `--ln-*` 令牌在 h/i/j/k 下补齐映射（否则经典组件 .ln-btn/.ln-win 无色）。

### 3.3 主题切换机制（landing.js）

- 合法值扩为 `['light','dark','h','i','j','k']`；按钮循环切换，label 显示下一档名（暗色→墨格→构成→夜航→套色→亮色）。
- `lj_landing_theme` 键不变；旧存值（light/dark）无缝兼容。
- 数字滚动（.ln-num[data-count]）与 reveal（IntersectionObserver）机制对 ed-site 自动生效，零新增 JS。

### 3.4 tuner 追平（tuner.html）

- THEMES 表 + BG_MAP + tab 扩至 A–K；h/i/j/k 无背景图（img=bg，合成恒纯色，op 滑杆不生效且不写 `lj_ink_op`——v14 守卫延续）。
- 预览覆盖：stage 底色/字体（H/K 衬线、J mono）、面板直角/硬阴影、气泡、tab 选中态。

### 3.5 字体策略

- CDN：`fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Archivo+Black&family=IBM+Plex+Mono:wght@400;500`（app.html 与 index.html 双入口）；unicode-range 分片按需加载。
- **离线/CDN 不可达回退**：H/K 标题 → 宋体栈（"Source Han Serif SC"/Songti SC/SimSun）；I/J → 系统黑体/Consolas；功能与对比度不受影响，仅气质降档。
- 子集化 woff2 本地化列为后续可选项（见 §七）。

---

## 四、与相邻版本 / 轮次的关系

| 关联项 | 关系说明 |
|---|---|
| v13/v14 追加式约定 | 延续「body[data-theme] 覆盖 + 文末追加段」，A–G 既有规则零修改 |
| v14（ROUND16） | tuner 的 `lj_ink_op` 写入守卫延续到 h/i/j/k |
| ROUND15 | 落地页 C1~C3 工作台编辑器化（章节树+稿纸/AI 块写入/选中改写）仍待排期，本版未动工作台信息架构 |
| design-samples | `frontend/design-samples/` 四样图为落地依据（样图→生产还原），保留作设计档案 |

---

## 五、视觉验证清单（已全部执行通过）

- [x] `vite build`：301 modules，8.47s；landing css 26.45KB（gzip 6.35KB）
- [x] `eslint useTheme.js / landing.js`：0 error；landing.js `new Function` 语法校验通过
- [x] 工作台 h/i/j/k 截图（1440px）+ j 移动端（390px）：`.workbuddy/diag-shots/v15-app-*.png`
- [x] 落地页 6 主题全页截图 + h 移动端：`v15-landing-{light,dark,h,i,j,k}.png`
- [x] 全程 0 页面 JS 错误（pageerror 监听）
- [x] tuner A–K 十一主题切换（v14 测算守卫生效）

---

## 六、同步与状态保留

- 工作台：`localStorage.lj_theme`（a–k 十一值）；`lj_ink_op` 在 h/i/j/k 下不被 tuner 写入。
- 落地页：`lj_landing_theme`（light/dark/h/i/j/k 六值）；与工作台主题键依旧相互独立（设计如此）。
- 主题切换音效（useTheme Web Audio）对 h/i/j/k 同样触发。

---

## 七、已知边界 / 未覆盖项

1. **J 中文标题非 mono**：IBM Plex Mono 不含中文，中文标题回落系统黑体栈——双语混排的「仪表感」由拉丁/数字承担，属预期行为。
2. **CDN 字体依赖**：离线环境四主题标题降级系统栈（见 §3.5）；本地 woff2 子集化（pyftsubset，单字体目标 100~300KB）列为后续可选优化。
3. **ed-site 内容为静态同源副本**：与 ln-site 的文案/评测数字需人工同步（当前一致；后续若频繁改动可考虑构建期注入，暂无必要）。
4. **K 荧光粉 CTA 对比 4.66:1**（AA 达标）；H 朱红 hover 态 4.9:1、J 青 CTA 黑字 9:1、I 红 CTA 白字 4.0:1（大字号按钮文本，AA 大字达标）。
5. 移动端 ≤1024px 会话卷册/右栏不可达既有决策不变；ed-site ≤860px 隐藏导航与几何装饰。

---

## 八、追溯 / 关联文档

- 轮次记录：[`OPTIMIZATION_ROUND17.md`](./OPTIMIZATION_ROUND17.md)
- 设计样图：`frontend/design-samples/sample-{a-editorial,b-konstrukt,c-nightflight,d-riso}.html`
- 版本索引：[`README.md`](./README.md)
- 格式规范：[`../FORMAT_STANDARD.md`](../FORMAT_STANDARD.md)

---

*变更版本：v15 · 现代艺术四主题 · 与经典七版共存 · design tokens 统一管理*
