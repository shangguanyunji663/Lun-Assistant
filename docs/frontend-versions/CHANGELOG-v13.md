# 论匠前端 · v13 新增三主题（雨过天青 / 玄墨赭金 / 秋香宣纸）— 变更文档

> 文档域：frontend-versions
> 文档类型：版本变更
> 主题版本：v13
> 轮次：ROUND14
> 日期：2026-09-30
> 状态：已落地

> 一句话背景：在不改动现有 A/B/C/D 四主题的前提下，以与现有主题完全一致的接入方式新增三个主题，并同步落实「去 AI 味」设计要求（克制单强调色、无紫蓝渐变、收紧圆角、去毛玻璃、去彩色光晕）。生产代码直改，无设计稿侧变更。

---

## 一、总览（结论先行）

| 维度 | v12（现状） | 本版（v13） | 改动 |
|---|---|---|---|
| 主题数 | 4（A/B/C/D） | 7（+E/F/G） | 是 |
| 现有主题样式 | — | **零改动**（styles.css 纯追加 262 行、0 删除） | 否 |
| 切换机制 | body[data-theme] + THEMES 注册 | 完全复用，仅扩展注册数组 | 否（机制不变） |
| 新主题配色 | — | 单强调色轴，无紫/蓝渐变 | 新增 |
| 新主题背景图 | A/C/D 有 | E/F/G 均无（实色底 + 遮罩全零） | 新增 |
| 新主题圆角 | pill 999px / xl 22px | E/F/G 作用域内收紧为 pill 6px / xl 12px | 新增（仅新主题） |
| 新主题面板 | rgba 半透明 + blur 毛玻璃 | 实色 var(--bg-panel)，backdrop-filter: none | 新增（仅新主题） |
| 顶栏主题 tab | 4 个文字标签 | 961~1760px 自动切色块模式（沿用 ≤960px 既有策略） | 是（追加媒体查询） |

变更结论：

1. **结构**：主题注册仍单一真源（`useTheme.js` THEMES / VALID_THEMES），App.jsx 的 tab 渲染数据驱动，无需改动组件。
2. **样式系统**：新主题遵循既有「body[data-theme] 覆盖 :root 令牌」范式；所有反 AI 味覆写均为新增选择器。
3. **token 维度**：E/F/G 各覆盖 28 个令牌（与 B/C/D 同 schema），另覆写圆角 / 阴影两组共享令牌（作用域限新主题）。
4. **文案**：顺带清理共享 JSX 中的 AI 味残留（emoji / 架构术语外露），不影响功能与信息结构。

### 1.1 三个新主题设计定位

| 主题 | id | 底色 | 文字 | 单强调色 | 与相邻主题的区分 |
|---|---|---|---|---|---|
| 雨过天青 | `e` | `#E3E9E5` 釉灰青 | `#22302A` 墨绿黑 | 黛青 `#3A6B5C` / CTA 青瓷 `#589384` | 对 A（柔雾青绿）：去蓝调、偏灰绿釉色 |
| 玄墨赭金 | `f` | `#171512` 暖炭黑 | `#E9E2D4` 象牙 | 赭金 `#C2955A` CTA / 象牙链接 | 对 C（暗墨夜山）：中性偏暖 vs 蓝调夜山 |
| 秋香宣纸 | `g` | `#EFE8D9` 暖米 | `#322C20` 深茶褐 | 茶褐 `#6B5B36` / CTA `#A0824A` | 对 D（青绿金碧）：低饱和宣纸 vs 高饱和金绢 |

对比度关键值（WCAG）：E 正文 ≈11:1、F ≈14:1、G ≈11:1；三主题 CTA 深字（#17222B）对比 4.9 / 6.2 / 4.7:1，均 ≥4.5:1。

---

## 二、文件级变更摘要

| 文件 | 改动 | 行号范围 | 类型 |
|---|---|---|---|
| `frontend/src/styles.css` | v13 三主题令牌块 ×3 + 反 AI 味覆写 + 主题 tab 选中态 ×3；§17 tab 容量适配（文末） | +262 行 / 0 删除（git numstat 实测） | 修改（纯追加） |
| `frontend/src/hooks/useTheme.js` | THEMES 追加 E/F/G 三项；VALID_THEMES 扩为 a~g；头注释补 v13 行 | 3-14 | 修改（+7/-2） |
| `frontend/src/App.jsx` | 「🎛 控制台」→「调参台」；空态文案去架构术语；「＋ 新建」→「新建项目」；会话「＋」→「新建」；介入条去 ⏸ + 兜底文案自然化 | 109 / 113 / 124 / 170 / 196 / 219 | 修改（仅文案） |
| `frontend/src/components/Timeline.jsx` | ▶ / ✓⚠ / ✔ / ⏸ / ✖ 符号 → 文字（（完成）/（异常）/ 已完成 / 待确认 / 错误·） | 11-18 | 修改（仅文案） |
| `frontend/src/components/KnowledgePanel.jsx` | 上传徽章符号 → 文字前缀（已入库·/已存在·/失败·）；拖拽图标「入」→「…」；检索示例去 RRF 术语 | 92 / 103 / 111 | 修改（仅文案） |
| `frontend/src/components/ProjectDialog.jsx` | 示例题目改为真实论文向（去 LangGraph 自指） | 48 | 修改（仅文案） |
| `docs/frontend-versions/v13-screenshots/` | theme-a~g.png 共 7 张（1600×900，mock 登录实拍） | — | 新增 |

---

## 三、全局工程变更

### 3.1 主题注册（useTheme.js:4-14）

```jsx
// v13 · 新增三主题（样式见 styles.css「v13 · 新增三主题」节）
{ id: 'e', label: '雨过天青', chip: '#C7D3CB' },
{ id: 'f', label: '玄墨赭金', chip: '#171512' },
{ id: 'g', label: '秋香宣纸', chip: '#E6DECB' },
```

VALID_THEMES 白名单同步扩为 `['a','b','c','d','e','f','g']`（useTheme.js:16）。持久化（`localStorage.lj_theme`）、跨页签 storage 事件联动、切换音效均数据驱动，自动覆盖新主题。

### 3.2 新主题令牌块（styles.css:288-543，纯追加于 D 主题块之后）

每个新主题覆盖与 B/C/D 相同 schema 的 28 个令牌（bg 三阶 / ink 三阶 / jade·pine·gold·seal / line 五系 / 字体继承 :root / bg-rgb 三组 / --ink-bg-url: none / wood 三阶 / veil 全零）。

### 3.3 反 AI 味覆写（仅 E/F/G 作用域的新增选择器）

- 实色面板去毛玻璃：`.chat-col / .side-col / .trace-panel / .sessions / .auth-card { background: var(--bg-panel); backdrop-filter: none }`，`.modal-mask` 去模糊；
- 实色 CTA：`.btn-ink / .auth-card > button` 由渐变改 `var(--gold)` 并去三层金色光晕 box-shadow；
- 去装饰性墨滴：`.ink-blob { display: none }`；
- 圆角收紧：`--r-pill: 999px → 6px`、`--r-xl: 22px → 12px`（令牌作用域覆写）；
- 焦点环 / 主题 tab 选中态按各主题强调色重定义。

### 3.4 主题 tab 容量适配（styles.css 文末 §17，约 :1556-1564）

tab 4 → 7 后，961~1760px 宽度沿用 ≤960px 既有「只留色块」策略（`font-size: 0` + 色块 14px），>1760px 显示完整文字标签，并补 `.theme-tabs button { white-space: nowrap }`。

> ⚠️ **级联顺序教训**：该规则初版插在 v13 主题节（styles.css:548 区域），位于 §7 的 `.theme-tabs button` 基础规则**之前**，同特异性下被后者的 `font-size: 12px` 覆盖而失效（同会话实测 `btnFont: 12px`）。已移至文件末尾修正。**后续在同文件追加同选择器规则时，必须放在基础规则之后。**

---

## 四、与相邻版本 / 轮次的关系

| 关联项 | 关系说明 |
|---|---|
| v12（B 黑白瑞士） | B/C/D/E/F/G 的令牌块彼此独立，v13 未触碰任何 v11/v12 规则 |
| ROUND12 / ROUND13 | 均为 backend 域轮次（主题版本 —），本版为 ROUND14（前端域） |
| 2026-09-30「去 AI 味」要求 | 原指令针对现有主题的清理被本指令替代（「不改动现有主题」）；该要求的反 AI 味原则全部落实到 E/F/G 设计与共享 JSX 文案 |

---

## 五、视觉验证清单（已全部执行通过）

- [x] `npm run build` 通过（vite 8.6s，css 42.14 kB）；eslint 0 error
- [x] `git diff --numstat`：styles.css **+262 / -0**（纯追加，现有主题样式结构级不受影响）
- [x] 七主题切换终值断言（playwright + Edge + mock API，点击 tab 路径）：a `rgb(232,239,243)` / b `rgb(255,255,255)` / c `rgb(10,20,36)` / d `rgb(201,181,138)` / e `rgb(227,233,229)` / f `rgb(23,21,18)` / g `rgb(239,232,217)` 全部精确匹配
- [x] 新主题反 AI 味断言：E/F/G `send-radius=6px`、`chat-blur=none`、CTA 无渐变；A-D 保持 `999px / blur(16px) / 渐变`（原样）
- [x] 持久化：切到 g/f 后 reload 主题保持；`localStorage.lj_theme` 写入正确
- [x] 控制台 0 error
- [x] 顶栏无溢出：1600 / 1920 / 2200 / 1440 四档实测 `scrollWidth == clientWidth`；tab 色块高度 28px
- [x] 七主题截图归档 `v13-screenshots/theme-{a..g}.png`

---

## 六、同步与状态保留

- 持久化键：`localStorage.lj_theme`（a~g）、`localStorage.lj_ink_op` 不变；
- 跨页签联动：storage 事件同步对新主题 id 自动生效（VALID_THEMES 已扩展）；
- 调参台（`frontend/public/console/tuner.html`）：为 v10 时代的独立原型工具，自带旧三主题写死样式，**未**接入 E/F/G；其写入 `lj_theme` 的值若为新 id，主应用仍可正确应用。不影响主应用主题体系。

---

## 七、已知边界 / 未覆盖项

1. **既有 bug（未修，超出本版范围）**：`useTheme.js` `loadInkOp` 对缺失的 `lj_ink_op` 返回 0 而非默认 0.16（`Number(null) === 0` 通过 `>= INK_MIN` 校验），新访客山水底图默认不显示。该问题影响所有主题，修复会改变现有主题表现，留待专门轮次处理。

   > ⚠️ **变更标注（2026-09-30 · 同日补丁）**：本条已修复——`loadInkOp` 对「键缺失 / 空串」先回落 `INK_DEFAULT`（0.16）再做区间校验；storage 联动对「他页删除该键（newValue=null）」同样回落默认。显式 `0` 仍为合法持久值（用户拉到 0 会被记住）。playwright 场景矩阵实测：fresh→0.16、0.3→0.3、显式 0→0、非法串→0.16、主题切换 smoke ✓。styles.css 零改动（仅 useTheme.js +9/-4）。
2. E/F/G 无背景图，「山水浓度」滑杆对三新主题无可调对象（滑杆为共享 UI，按「不改现有结构」保留）。
3. 961~1100px 区间顶栏依然偏挤（历史遗留：≤960px 有换行布局，>960 中窄区间从未适配），与本次无关，未处理。
4. 未来主题数超过 7 时需重估 §17 的 1760px 阈值。
5. 旧截图工具（tuner.html）与设计稿侧（preview.html）不随本版更新。

---

## 八、追溯 / 关联文档

- 版本索引：[`README.md`](./README.md)
- 上一版本：[`CHANGELOG-v12.md`](./CHANGELOG-v12.md) · [`OPTIMIZATION_ROUND11.md`](./OPTIMIZATION_ROUND11.md)
- 主题切换机制起点：[`OPTIMIZATION_ROUND8.md`](./OPTIMIZATION_ROUND8.md)（v10 三主题）
- 格式规范：[`../FORMAT_STANDARD.md`](../FORMAT_STANDARD.md)

---

*变更版本：v13 · 新增三主题（E 雨过天青 / F 玄墨赭金 / G 秋香宣纸）· design tokens 单一真源 · 现有主题零改动（styles.css +262/-0）*
