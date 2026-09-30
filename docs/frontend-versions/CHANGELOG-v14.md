# 论匠前端 · v14 顶栏容量修复 + 落地页 mock 化 — 变更文档

> 文档域：frontend-versions
> 文档类型：版本变更
> 主题版本：v14
> 轮次：ROUND16
> 日期：2026-09-30
> 状态：已落地

> 一句话背景：截图诊断发现 v13 后顶栏在 1440px 即被挤爆（nav 按钮竖排变形）；将落地页过时的静态截图替换为纯 HTML/CSS mock（产品展示 mock 化）；调参台追平 v12/v13 主题体系并修正失真的对比度测算。

---

## 一、总览（结论先行）

| 维度 | 上一版（v13） | 本版（v14） | 改动 |
|---|---|---|---|
| 主题令牌（7 主题） | A–G 七套 | A–G 七套（零改动） | 否 |
| 顶栏布局 | 1440px 挤爆 | 1760px 起分档减法，全宽不变形 | 是 |
| disabled 态 | 雾化渐变不可辨 | 统一中性浅底 + 边框 | 是 |
| 落地页产品展示 | 静态 webp 截图（旧 UI） | 纯 HTML/CSS mock（A 主题快照） | 是 |
| C1~C3（工作台编辑器化） | 待排期 | 仍待排期（本版未动工作台信息架构） | 否 |
| 调参台 | A/B/C/D 四主题（落后两版） | A–G 七主题 + B v12 翻转 + 测算修正 | 是 |
| 键盘可达性 | 会话列表 div 仅鼠标 | role=button + tabIndex + 焦点环 | 是 |

变更结论：
1. **结构**：无 JSX 结构变更，仅 `sess-item` 增加键盘语义属性（`App.jsx:176-179`）。
2. **样式系统**：`styles.css` 追加 §19 / §20 两段（`styles.css:1575` / `:1634`），不改任何既有规则；`landing.css` 追加 §12 mock 段（`landing.css:444`）。
3. **token 维度**：七主题令牌零改动；mock 使用独立的 `--ma-*` 快照令牌（A 主题取值，与主应用解耦）。
4. **响应式**：顶栏新增 1760 / 1500 / 1366 / 1240 / 1140 五档减法（§19）；mock 在 ≤760px 收侧栏保对话区。

---

## 二、文件级变更摘要

| 文件 | 改动 | 行号范围 | 类型 |
|---|---|---|---|
| `frontend/src/styles.css` | §19 顶栏容量修复 + disabled 可辨性 + E/F/G composer 边界补强 | 1575–1632 | 新增 |
| `frontend/src/styles.css` | §20 登录页可辨性 + sess-item 焦点环 | 1634–1648 | 新增 |
| `frontend/src/App.jsx` | 会话列表项键盘可达（role/tabIndex/onKeyDown/aria-pressed） | 176–179 | 修改 |
| `frontend/index.html` | C1：hero 静态截图 → 三栏工作台 mock | 43–74 | 修改 |
| `frontend/index.html` | C2：架构段静态截图 → Trace 面板 mock | 149–173 | 修改 |
| `frontend/index.html` | C3：协同段追加 interrupt 确认条 mock | 190–196 | 新增 |
| `frontend/src/landing.css` | §12 编辑器式 mock 样式（含响应式与 reduced-motion） | 444–758 | 新增 |
| `frontend/public/console/tuner.html` | E/F/G 主题 + B v12 追平 + THEMES/字色/BG_MAP/写入守卫 | 全文件 | 修改 |
| `frontend/public/bg/shanshui-mist.jpg` | 零引用清理（v8 时代遗留） | — | 删除 |
| `frontend/public/bg/bg-b-inkwash.webp` | 零引用清理（ROUND11 挂账项） | — | 删除 |
| `frontend/public/assets/preview-a.webp` `preview-f.webp` | 被 mock 替换后零引用清理（ROUND15 截图资产） | — | 删除 |

---

## 三、全局工程变更

### 3.1 顶栏容量分档减法（styles.css:1575–1630）

根因：v13 将 theme-tabs 扩到 7 主题后，顶栏元素总需求 ≈1457px > 1440px 视口，`nav` 按钮无 `white-space: nowrap` 被压缩成竖排。修复为五档纯 CSS 减法：

| 断点 | 减法项 | 释放宽度约 |
|---|---|---|
| 保底（全宽） | 全部顶栏子元素 `nowrap + flex-shrink:0`；ghost 按钮 ink-low → ink-mid | 消除变形 |
| ≤1760px | 隐藏品牌副标题；滑杆 88→64px；隐藏角色徽章 | ~160px |
| ≤1500px | 隐藏「山水」标签；按钮 padding 收紧 | ~60px |
| ≤1366px | 隐藏用户名（退出保留） | ~85px |
| ≤1240px | 隐藏山水滑杆（调参台写入同一 `lj_ink_op` 键） | ~110px |
| ≤1140px | 隐藏调参台入口；项目选择器 max-width 200→150px | ~90px |

### 3.2 disabled 态统一（styles.css:1622–1627）

`.btn-ink:disabled` 与 `.auth-card > button:disabled` 从「渐变底 + opacity 0.36」改为中性浅底（`rgba(228,225,214,0.12)`）+ `--ink-low` 字色 + 边框保留，修复发送按钮/登录按钮文字不可辨。

### 3.3 调参台测算修正（tuner.html）

`TEXT_COLOR` 全局常量 `#E4E1D6`（v9 深底时代遗留）导致浅底主题对比度测算全线失真。修正为 THEMES 表内 `text` 字段（取各主题 `--ink-hi`）。修正后实测：A 10.06 / B 21.00 / C 12.69 / D 7.27 / E 11.19 / F 14.14 / G 11.35，全部 AAA，与 v11/v13 文档记录吻合。

### 3.4 `lj_ink_op` 写入守卫（tuner.html apply()）

E/F/G 无背景图，切到这三主题时不再写 `localStorage.lj_ink_op`，避免把主应用山水浓度污染为 0（显式 0 在主应用 `loadInkOp` 是合法持久值）。

### 3.5 mock 快照令牌（landing.css:448–461）

mock 内部配色为独立的 `--ma-*` 作用域令牌（工作台 A 主题取值），不随落地页双主题翻转——产品展示取「实物快照」语义，暗色区块中的亮窗与原截图观感一致。

---

## 四、与相邻版本 / 轮次的关系

| 关联项 | 关系说明 |
|---|---|
| v13（ROUND14） | 七主题令牌零改动；修复其引入的顶栏挤压；composer 边界补强属 v13 覆盖遗漏的追加 |
| v12（ROUND11） | tuner 的 B 主题视觉追平黑白瑞士翻转（主应用已在 ROUND11 落地） |
| ROUND15 | 落地页产品展示 mock 化（两处静态截图 → mock，旧 UI 截图资产下线）；ROUND15 记录的 C1~C3 原义为**工作台编辑器式重构**（C1 章节树+稿纸 / C2 AI 块写入 / C3 选中改写），**仍待排期**，本版未动工作台信息架构 |
| §17（v13 容量适配） | §19 与其互补：§17 管 theme-tabs，§19 管其余顶栏元素 |

---

## 五、视觉验证清单（已全部执行通过）

- [x] `vite build` 通过（301 modules，9.17s）
- [x] `eslint src/App.jsx` 0 error
- [x] 1440 / 1280 / 1024 三档顶栏截图：无按钮变形（`.workbuddy/diag-shots/fix-topbar-*.png`）
- [x] tuner 七主题截图 + 测算值核对（`tuner-{a..g}.png`）
- [x] 落地页亮/暗 + 移动端 mock 截图（`c1-hero-mock.png` 等 7 张）
- [x] 七主题对比度审计（`scripts/_contrast_audit.py`）：正文全 AAA

---

## 六、同步与状态保留

- 持久化键：`localStorage.lj_theme`（七主题）、`lj_ink_op`（E/F/G 下 tuner 不写入）、`lj_landing_theme`（落地页双主题，互不同步——设计如此）。
- 跨页签联动：tuner ↔ 主应用的 storage 事件同步不受影响。

---

## 七、已知边界 / 未覆盖项

1. **G 秋香宣纸 CTA 对比度 4.45:1**（差 0.05 到 AA）：v13 遗留取值，改令牌会破坏单强调色轴一致性，收益 0.05，如实标注不改。
2. **D 青绿金碧 ink-low 对主底 2.56:1 / ink-mid 对面板 3.53:1**：v11 时代取值，影响占位符与次级文字层级，属既有视觉语言，标注不改。
3. **移动端 ≤1024px 会话卷册与右栏不可达**：既有设计决策（§15 注释「窄屏收起卷册，保住对话区」），统一解决属工作台信息架构重构轮。
4. **C1~C3（工作台编辑器式重构）仍待排期**：其原义见 ROUND15 日志——C1 章节树+稿纸、C2 AI 块写入、C3 选中改写；本版的「落地页 mock 化」是相邻的展示层改进，不构成 C1~C3 落地。
5. mock 为静态复刻，不承载真实交互；内容与当前工作台 A 主题视觉一致，工作台后续改版需同步 mock（成本低：纯 HTML/CSS）。

---

## 八、追溯 / 关联文档

- 轮次记录：[`OPTIMIZATION_ROUND16.md`](./OPTIMIZATION_ROUND16.md)
- 版本索引：[`README.md`](./README.md)
- 格式规范：[`../FORMAT_STANDARD.md`](../FORMAT_STANDARD.md)
- 审计脚本：`scripts/_contrast_audit.py`（七主题对比度审计，可复用）；截图诊断脚本为临时件，验证后已清理

---

*变更版本：v14 · 顶栏容量修复 + 落地页 mock 化 · design tokens 统一管理 · 七主题令牌零改动*
