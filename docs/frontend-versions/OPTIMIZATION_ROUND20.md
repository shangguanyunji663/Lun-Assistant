# 论匠前端 · ROUND20 — 横切设计审计修复 + 时间线跳转

> 文档域：frontend-versions
> 文档类型：轮次记录
> 主题版本：v18
> 轮次：ROUND20
> 日期：2026-10-03
> 状态：已落地

> 一句话背景：v18 六套皮肤落地后，用 redesign-skill 做了一次**跨皮肤的全量设计审计**，发现遗留问题不在任何单一皮肤，而在**共享底座与入口层**——字体加载依赖 Google Fonts（内网/被墙环境掉 900 字重）、按钮无按下反馈、favicon/og 缺失、数据排版细节（等宽数字/孤字/行宽）未处理、boot 态是裸文本。本轮按 P1~P6 优先级全部落地；外加一个经 grill-me 盘问定案的功能：**执行时间线点击跳转到对应消息**。**编号依据**：前端版本线止于 ROUND19，本轮顺延为 ROUND20；主题版本仍为 v18（令牌契约未动，皮肤仅 e-riso 一处 dvh 兜底）。
>
> ⚠️ **变更标注（2026-10-03 · 八套皮肤轮）**：本轮落档时 vite 入口为 **7 个**；随后 [`ROUND20-ADDENDUM.md`](./ROUND20-ADDENDUM.md) 把两页新语言（编队总谱 / 论文底片）正式落地为独立页面，入口扩为 **9 个**、落地页扩为 **8 张**。当前入口数以 [`frontend/vite.config.js`](../../frontend/vite.config.js) 为准。

---

## 一、本轮改进总览

### 1.1 背景：审计发现（redesign-skill 流程）

对 `frontend/` 全量源码（base/panels/layout/fx + 八套皮肤 + 7 个入口 HTML + 全部组件）跑审计清单，按修复优先级排出的六类问题：

| 级别 | 问题 | 实测证据 | 性质 |
|---|---|---|---|
| P1 | 字体加载依赖 `fonts.googleapis.com` | 两个入口 HTML 外链 9 个字重；内网/被墙下 900 字重标题掉成系统粗体 | 可用性风险 |
| P2 | 按下反馈全项目 **0 处** `:active` | `.btn` 只有 hover；21 处 `:focus` 覆写核对后确认全部是表单 border-color，无焦点环破坏 | 微交互 |
| P3 | favicon / og meta 缺失 | index.html、app.html 均无 icon 链接，无 og:* | 品牌资产 |
| P4 | 数据排版细节缺失 | `tabular-nums` 0 处（时间戳每帧跳位）、`text-wrap` 0 处（孤字）、气泡行宽仅 C 皮肤有 66ch 限制 | 可读性 |
| P5 | 加载态落差 | boot 态裸文本「加载中…」（App.jsx:258）、ProjectArchive「读取中…」纯文本——与精心设计的空态形成断档 | 状态完整性 |
| P6 | 体系卫生 | z-index 5~130 九档散落无规约；3 处 `100vh` 未配 dvh；1 处内联 `style={{flex:1}}` | 可维护性 |

外加一条功能诉求（grill-me 五问定案，见 §五）：时间线事件点击跳转到对应消息。

### 1.2 涉及的前端模块或文件

| 文件 | 改动 | 类型 |
|---|---|---|
| `frontend/src/fonts/fonts.css` | 自托管字体入口（9 字重 @fontsource 引入） | **新增** |
| `frontend/public/favicon.svg` | 品牌印章 favicon（朱底纸色「匠」） | **新增** |
| `frontend/scripts/shot-audit.mjs` | 本轮截图验证脚本（playwright-core，复用项目脚本引用方式） | **新增** |
| `frontend/index.html` / `app.html` | 字体链接替换 + favicon + og:* | 修改 |
| `frontend/landing-b~f.html`（4 文件） | 字体链接替换 + favicon | 修改 |
| `frontend/src/styles/base.css` | 按下态清单 / tabular-nums / text-wrap / 气泡 66ch / `.skl` 骨架原子 / 时间线跳转手势 / `.is-jump-hl` 高亮脉冲 | 修改 |
| `frontend/src/styles/panels.css` | `.wb-boot` 品牌化 + dvh、`.auth` dvh | 修改 |
| `frontend/src/fx.css` | `.wb-boot .seal` 浮动动画 + reduced-motion 列表同步 | 修改 |
| `frontend/src/landing/shared.css` | 落地页按下态（`.sw-trigger` / `.sw-item` / `.egg-go` / `.egg-later`） | 修改 |
| `frontend/src/App.jsx` | boot 屏 JSX、时间线分轮推断 `turnOfEvent`、`jumpToMsg` 跳转与高亮、`data-midx` 锚、`attachStream` 合并 ref | 修改 |
| `frontend/src/components/Timeline.jsx` | 事件条目可点击化（`is-clickable` + role=button + 键盘） | 修改 |
| `frontend/src/components/ProjectArchive.jsx` | 加载态换 `.skl` 骨架 | 修改 |
| `frontend/src/components/ProjectDialog.jsx` | 内联 `style={{flex:1}}` → `.wb-fill` | 修改 |
| `frontend/src/skins/e-riso.css` | `.wb-boot` 补 `min-height: 100dvh`（唯一触碰的皮肤文件） | 修改 |
| `frontend/src/skins/CONTRACT.md` | z-index 七档规约、`.skl`/boot 契约、按下态规约、`.wb-tl-item` 可点态、`data-midx` 锚 | 修改 |
| `frontend/package.json` + `package-lock.json` | +3 依赖：`@fontsource/noto-sans-sc` / `noto-serif-sc` / `ibm-plex-mono`（v5） | 修改 |

合计（`git diff --stat --ignore-cr-at-eol`）：**19 文件 +253 / −45**，外加 3 个新增文件。八套皮肤中仅 e-riso 一行 dvh 兜底，其余**全部零改动**——本轮问题在共享层，不在皮肤层。

> **e-riso.css 的 diff 幻影说明**：`git diff` 会显示该文件整文件变更（+865/−864），是 `core.autocrlf=true` 与历史 blob 中 CRLF 的组合噪音，真实改动仅 2 行（`--ignore-cr-at-eol` 可见）；**提交时 autocrlf 会把 blob 归一为 LF，幻影自愈**，无需处理。

### 1.3 具体改动要点

| # | 改动 | 类型 |
|---|---|---|
| 1 | 字体自托管：`src/fonts/fonts.css` 经 @fontsource 引入 9 字重（黑体 400/500/700/900、宋体 700/900、Plex Mono 400/500/600），CJK 按 unicode-range 百余子集分包按需加载；7 个入口 HTML 的 Google Fonts 链接全部替换。字族名与 Google Fonts 完全一致，皮肤 `--font-*` 令牌零改动 | 修复（P1） |
| 2 | 按下反馈：base.css 统一 `:active { scale: .97 }`，覆盖 .btn / .wb-btn / .wb-view / .wb-side-tab / .wb-new / .wb-prompt / .wb-break-op / .wb-vol-del / .wb-tl-item / .sp-item；落地页 shared.css 覆盖 .sw-* / .egg-* | 修复（P2） |
| 3 | 按下态用独立 `scale` 属性而非 transform——`transform` 所有权归 fx 层（`[data-tilt].tilt-on` 以 !important 接管、`[data-magnet]` 常驻位移），`scale`/`translate` 是独立属性互不覆盖；写入 CONTRACT §四第 11 条 | 新增约定 |
| 4 | favicon.svg（朱底纸色「匠」，与皮肤 A 印章同源）+ 7 页接入；index/app 补 og:type/site_name/title/description | 修复（P3） |
| 5 | `tabular-nums`：time / .wb-msg-time / .wb-vol-meta / .wb-vol-no / .kh-score | 修复（P4） |
| 6 | `text-wrap: balance`（空态标题 / 弹窗标题 / 待确认问句 / markdown 标题）；`.wb-bubble p` 加 `text-wrap: pretty` + `max-width: 66ch` | 修复（P4） |
| 7 | boot 屏品牌化：印章 + 「正在铺纸研墨…」（fx-seal-float 浮动，reduced-motion 自动停）；ProjectArchive 换 `.skl` 骨架（三条错峰脉动占位条），原子入 base.css 供后续面板复用 | 修复（P5） |
| 8 | CONTRACT.md 写入 **z-index 七档规约**（0 氛围 / 5 流内 sticky / 20 列头 / 60 顶栏弹层 / 100 模态 / 120 fx 层 / 130 成就条；现存 88/90 允许保留不新增） | 新增约定（P6） |
| 9 | dvh 配对：`.wb-boot`（panels）、`.auth`、e-riso `.wb-boot` 三处补 `min-height: 100dvh`；八套皮肤 `.wb` 的 `min-height:100vh` 已被 layout.css 的 `height:100vh+100dvh` 链管辖，无需逐套修改 | 修复（P6） |
| 10 | 时间线点击跳转：渲染期分轮推断（见 §五）+ Timeline 可点击化 + 气泡高亮脉冲 | **新增功能** |
| 11 | ProjectDialog 一处内联样式 → `.wb-fill` 类 | 修复（P6） |
| 12 | 21 处皮肤 `:focus` 覆写逐一核对：全部为表单 border-color，**无一处**移除 outline 且无替代——base.css:66 的 `:focus{outline:none}` + `:focus-visible` 全局兜底模式完好，本轮不动 | 审计结论 |

### 1.4 与之前几轮修改的关系

- **修复**：v18 建立皮肤体系时「只管六套语言成立」留下的入口层与共享底座缺口（与 ROUND19 修皮肤层可读性互补，两层合起来 v18 的设计债清完）。
- **新增**：`.skl` 骨架原子、时间线跳转交互、z-index 规约、按下态规约（均入 CONTRACT.md）。
- **不涉及**：金碧 / 青花瓷两款新皮肤提案仍在 `design-samples/skin-g/` 探索（g-jinbi.css / h-qinghua.css 已有文件但 main.jsx 未接线，维持等拍板状态）；v15 的 C1~C3 仍待排期。

---

## 二、字体自托管（P1，本轮最大风险项）

**问题**：字体走 `fonts.googleapis.com`，本机网络环境（GitHub raw 直连 SSL 失败的同源问题）下加载慢或失败。不炸版——皮肤字体栈有宋体/楷体/雅黑兜底——但 **900 字重标题掉成系统粗体，六套皮肤的性格瞬间变平**。

**方案**：@fontsource（npm 包）自托管。CJK 包把字体按 unicode-range 切成百余个 woff2 子集，浏览器只拉当前页面用到的字符所在子集，无一次性大下载；构建时子集进 `dist/assets/`，与 GitHub Pages 部署兼容。

**接线**：`src/fonts/fonts.css` 作为唯一入口（@import 九个字重），7 个入口 HTML 以 `<link rel="stylesheet" href="/src/fonts/fonts.css">` 引入——与 `/src/landing/shared.css` 同一条 Vite 打包路径，build 自动进资源图。

**实测**（playwright，dev server）：`fonts.googleapis.com / fonts.gstatic.com` 请求 **0 次**；自托管 woff2 子集按需加载 **148 个**；`document.fonts.check('900 40px "Noto Serif SC"', '论匠')` 为 **true**（900 衬线真实渲染）。注：`fonts.check` 不带中文样张时对 CJK 子集字体恒 false（默认探测拉丁字符 "BESbswy"，所在子集未被使用未拉取），属按需加载的正确表现，不可用它判字体是否生效。

**遗留**：`public/easter/` 三个彩蛋页仍外链 Google Fonts，未纳入本轮（独立小页面，字重只有 400~600，掉字重影响小）。

---

## 三、交互态与数据排版（P2 / P4）

### 3.1 按下反馈的属性选型

按下态若用 `transform: scale(.97)` 会与 fx 层打架：`[data-tilt].tilt-on` 以 `!important` 接管 transform（不夺回会被皮肤 hover 位移覆盖），`[data-magnet]` 常驻 `transform: translate(--mgx, --mgy)`。CSS 独立变换属性 `scale` / `translate` / `rotate` 与 `transform` 是**叠加关系而非覆盖关系**，故按下态用 `scale`，两者互不干扰。项目 keyframes 已在用独立 `translate`（base-rise / fx-rise 的 `translate: 0 14px`），风格一致。

按下是离散状态而非动画，`prefers-reduced-motion` 下保留（与 base.css §8 的全局降级不冲突）。

### 3.2 数据排版三件

- **`tabular-nums`**：时间戳（`[14:32:07]` 呼号式）、会话序号/条数、知识库评分——比例字体数字每帧横向跳动，数据型文本锁定等宽数字。
- **`text-wrap: balance`**：中文大标题孤字（最后一行单字）自动重排；气泡内 markdown 标题同享。`pretty` 用于正文段落。
- **行宽**：AI 气泡段落 `max-width: 66ch`（约 40±5 字/行，与 ROUND19 定下的正文列宽口径一致）。只限 `p` 不限气泡整体——表格/代码块保持全宽。C 皮肤自己的 `.wb-bubble { max-width: 66ch }`（整泡限宽）与之一致不冲突。

---

## 四、品牌资产与加载态（P3 / P5）

- **favicon.svg**：64×64 圆角方章，朱底（#C0332A）+ 纸色「匠」（#F3EEE3），与皮肤 A 的印章同源；SVG 内字体栈与皮肤 A 展示字体一致。以 `./favicon.svg` 相对路径接入（GitHub Pages `base: /Lun-Assistant/` 下相对路径才能两栖）。
- **og meta**：index（站根）与 app 两页补 og:type / og:site_name / og:title / og:description。og:image 因无公网绝对 URL 暂缺，GH Pages 上线后可补。
- **boot 屏**：`<Seal size={40}/> + 「正在铺纸研墨…」`，复用 fx-seal-float 浮动；`.wb-boot` 的 DOM 变化已同步进 CONTRACT §三。
- **骨架屏 `.skl`**：三条 `--surface-2` 占位条错峰脉动（12px 高、82%/64% 递减宽度），ProjectArchive 加载态先行接入；base.css 原子级组件，后续 KnowledgePanel / TracePanel 可复用。

---

## 五、时间线点击跳转（grill-me 五问定案）

### 5.1 定案记录

| # | 决策 | 定案 |
|---|---|---|
| Q1 | 跳转粒度 | 事件 → **本轮 AI 消息气泡**（数据模型决定的最细粒度：每轮所有 SSE 事件只产出一条 assistant 消息） |
| Q2 | 跳转反馈 | 滚动 + 目标气泡 **1.2s 高亮脉冲**（--accent 淡色环，box-shadow 不与皮肤底色打架）；不做「当前查看」双向标记 |
| Q3 | 旧会话兼容 | **纯渲染期推断**，不动持久化结构，老会话全量可跳 |
| Q4 | 无障碍 | `role="button"` + `tabIndex` + Enter/Space（与 `.wb-vol` 同款先例） |
| Q5 | 范围 | 只做单向（时间线 → 消息）；反向联动不做 |

### 5.2 分轮推断规则（读后端源码定标）

- 后端事实：`intent` 只在每轮**首次进入 supervisor**（`not visited` 分支）时发射一次；`node_start` 是**每个节点发一次**（supervisor / planner / 各 specialist 各发）——**绝不能**当轮边界。`services/agent/supervisor.py` 为证。
- 推断：`intent` 为轮边界，第 k 段事件 → 第 k 条 assistant 消息（msgs 按用户/助手成对追加，助手在奇数下标 `2k+1`）；首个 intent 前的事件（error / interrupt 兜底轮）归最后一条消息；推断失败（`-1`）渲染为不可点。
- **已知边界**：resume 反馈轮后端可能不发 intent，该轮事件会归到上一段——渲染期推断的固有代价，换老会话全量可跳的收益；要根除需后端在事件里补 `turn`/`ts` 字段，另立轮次。

### 5.3 实现要点与一个真 bug

- 消息定位：`article.wb-msg` 挂 `data-midx={i}`，跳转时容器内 `querySelector('[data-midx="N"]')` + `scrollIntoView({block:'start'})`（容器的 `scroll-padding-top: 12px` 自动生效）。
- **真 bug**：首版用 `scrollRef.current` 查询——`scrollRef` 是 useStickyScroll 的 **callback ref**（`attach`），不是 RefObject，`.current` 恒为 undefined，被可选链静默吞掉：高亮照常出现、滚动纹丝不动。纯看代码发现不了，是浏览器行为测试揪出来的。修复：App 另挂 `streamElRef`，与 hook 的 callback ref 合并到同一节点（`useCallback` 保证 ref 身份稳定）。
- 流式中点击目标即最后一条时走粘底 `scrollToBottom('smooth')`，不打断跟随；跳转后「回到底部」按钮按既有粘底逻辑自然出现，无特判。
- reduced-motion 下 `scroll-behavior: auto !important` 会把程序化平滑滚动转为瞬时——跳转对弱动效用户自动降级为直接定位。

---

## 六、验证记录

- **构建**：`npm run build` ✓（2.0s）；字体子集入产物（woff 按 unicode-range 分包）。
- **静态**：`eslint .` 零告警（期间修掉两处：useMemo 内闭包改写外层变量违反 react-hooks/immutability → 改 memo 体内 for 循环；`useCallback` 漏 import）。
- **回归**：`scripts/verify-state.mjs` 三场景全过（连点重入锁 / 演示模式不污染持久化 / PATCH 按 id 命中），无页面错误。
- **行为**（playwright）：时间线 6 条全可点；点击/键盘均滚动到位（reduced-motion 路径实测 scrollTop 0→1854 封顶）；高亮挂到正确消息（data-midx=1）且 1.3s 自动消退；无页面错误。
- **截图**：`frontend/_audit-shots/` 三张（皮肤 A / 皮肤 B / 落地页 A），宋体 900 真实渲染、暗色对比度正常、时间戳等宽对齐。headless + `--disable-gpu` 下入场动画与平滑滚动会冻结在首帧——截图一律用 `reducedMotion: 'reduce'` 拿终态，行为断言也走 reduced-motion 路径（与生产语义等价）。

---

## 七、已知边界 / 未覆盖项

1. **resume 轮事件归上一段**（§5.2 已述），要根除需后端事件补字段，另立轮次。
2. **easter 彩蛋页仍用 Google Fonts**：`public/easter/*.html` 三页未纳入本轮。
3. **og:image 缺**：待 GH Pages 上线有绝对 URL 后补。
4. **z-index 现存 88/90 两档**属历史遗留，规约允许保留不新增；未回改各皮肤既有值（churn 大收益小）。
5. **审计达标项未动清单**（防止后续误「修」）：令牌契约架构、单一强调色 + 带色调阴影、CJK 字体栈、reduced-motion 全局降级、overscroll-behavior 阻断、ResizeObserver 顶栏实测、aria/键盘支持、真实中文文案。
6. **`.skl` 骨架**仅 ProjectArchive 接入；KnowledgePanel / TracePanel 的加载态仍是文本，待后续轮次统一。

---

## 八、追溯 / 关联文档

- 版本索引：[`README.md`](./README.md)
- 上一轮：[`OPTIMIZATION_ROUND19.md`](./OPTIMIZATION_ROUND19.md)（六套皮肤可读性与信息层次）
- 本轮修复的体系起点：[`CHANGELOG-v18.md`](./CHANGELOG-v18.md)（六套设计语言）
- 皮肤契约（本轮写入 z-index / 按下态 / 跳转锚约定）：[`../../frontend/src/skins/CONTRACT.md`](../../frontend/src/skins/CONTRACT.md)
- 时间线跳转的盘问定案：grill-me 五问（§5.1），实现于 `frontend/src/App.jsx` / `frontend/src/components/Timeline.jsx`
- 后端事实依据：`services/agent/supervisor.py`（intent 每轮一次 / node_start 每节点一次）
- 实机截图：[`../../frontend/_audit-shots/`](../../frontend/_audit-shots/)

---

*ROUND20 · 横切设计审计修复 + 时间线跳转 · 问题在共享底座不在皮肤层 · 八套皮肤仅 e-riso 一行 dvh*
