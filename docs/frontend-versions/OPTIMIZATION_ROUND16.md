# 论匠前端 · ROUND16 — 顶栏修复 · 一致性收尾 · 落地页 mock 化 · 可访问性

> 文档域：frontend-versions
> 文档类型：优化轮次记录
> 主题版本：v14
> 轮次：ROUND16
> 日期：2026-09-30
> 状态：已落地

> 一句话背景：以「截图诊断 → 分向修复」推进的混合轮：一致性收尾（tuner 追平 + 资产清理）、P0 顶栏容量修复、落地页产品展示 mock 化（替换过时截图）、性能与可访问性专项，全程零新依赖、七主题令牌零改动。

---

## 一、本轮改进总览

### 1.1 背景

ROUND15 收尾时遗留三类问题：① 落地页用旧 UI 的静态 webp 截图做产品展示（C1~C3 编辑器式重构共识待排期）；② 工作台 7 主题化后顶栏容量未复检；③ tuner.html 调参台停留在 v11（B 未翻转、E/F/G 未接入）。本轮以 Playwright + msedge 截图诊断（12 张全主题）确认问题清单后分向修复。注意：ROUND15 记录的 C1~C3 原义为**工作台编辑器式重构**（C1 章节树+稿纸 / C2 AI 块写入 / C3 选中改写），**仍待排期**；本轮 1.3 表 #6 的 mock 化是落地页展示层的相邻改进，不构成 C1~C3 落地。

### 1.2 涉及的前端模块或文件

- 工作台生产侧：`src/styles.css`（§19/§20 追加）、`src/App.jsx`（会话列表键盘语义）
- 落地页：`index.html`（C1/C2/C3）、`src/landing.css`（§12 mock 段）
- 调参台：`public/console/tuner.html`（E/F/G 接入 + B v12 追平 + 测算修正）
- 资产：删除 4 件零引用文件（共 220KB）

### 1.3 具体改动要点

| # | 改动 | 类型 |
|---|---|---|
| 1 | tuner 接入 E/F/G + B 追平 v12 黑白瑞士 + 对比度测算字色随主题 | 修复/迭代优化 |
| 2 | 清理零引用资产：shanshui-mist.jpg(123KB) / bg-b-inkwash.webp(51KB) / preview-a.webp(25KB) / preview-f.webp(21KB) | 修复（性能） |
| 3 | 顶栏五档容量减法（≤1760/1500/1366/1240/1140px），消除 nav 按钮竖排变形 | 修复（P0） |
| 4 | `.btn-ink:disabled` / 登录按钮 disabled 中性浅底化，文字可辨 | 修复 |
| 5 | 顶栏 ghost 按钮 ink-low→ink-mid；登录页副标题提级；E/F/G composer 边界补强 | 迭代优化 |
| 6 | 落地页 mock 化：两处静态截图 → 纯 HTML/CSS mock（三栏工作台 / Trace 面板），协同段追加确认条 mock（C1~C3 工作台编辑器化仍待排期） | 新增 |
| 7 | 会话列表项键盘可达（role=button + tabIndex + 焦点环）；reduced-motion 覆盖 mock 光标 | 新增（a11y） |
| 8 | 七主题对比度审计脚本 + 报告（正文全 AAA；G CTA 4.45 / D ink-low 2.56 遗留标注） | 新增（工具） |

### 1.4 与之前几轮修改的关系

- **修复**：顶栏挤压（v13 引入）、tuner 测算失真（v11 A 主题翻浅底后遗留）、composer 边界弱（v13 覆盖遗漏）。
- **迭代优化**：tuner 从 v11 状态追平至 v13（B 翻转 + E/F/G）。
- **新增**：落地页 mock 体系（§12）、会话列表键盘语义、对比度审计脚本。
- ROUND15 遗留共识 Q2-C（C1~C3 工作台编辑器式重构：章节树+稿纸 / AI 块写入 / 选中改写）**仍待排期**；本轮落地页 mock 化仅解决其展示层相邻问题（过时截图）。

## 二、验证记录

### 2.1 构建

- `vite build`：301 modules，9.17s，通过（App.jsx JSX 改动经 esbuild 编译验证）。
- `eslint src/App.jsx`：0 error。

### 2.2 视觉

- 截图诊断 12 张（修复前）+ 修复后 13 张（顶栏三档 / tuner 七主题 / 落地页亮暗+移动端），均存 `.workbuddy/diag-shots/`。
- 关键确认：1440px 顶栏无变形；tuner 七主题测算值 B 21:1 / D 7.27:1 等与文档吻合；C1 mock 三栏/气泡/时间线与工作台 A 主题一致。

### 2.3 可访问性

- prefers-reduced-motion：styles.css §16 全局兜底 + landing.css 已有 + 本轮 mock 光标闪烁纳入。
- 键盘：会话列表可达（Enter/Space 切换）；焦点环沿用既有 gold 样式。
- 对比度：`scripts/_contrast_audit.py` 输出七主题 × 4 色对矩阵，正文全 AAA；两处遗留临界如实标注于 CHANGELOG-v14 §七。

## 三、工程纪律

- 全程「追加式」：styles.css / landing.css 均为文末追加段（§19/§20/§12），不修改任何既有选择器；tuner 的 B/E/F/G 视觉为追加覆盖段（同特异性后者胜出）。
- 多文件改动遵循「Python 补丁脚本 + `assert count==1` + 写后 grep 复验」流程（`scripts/_patch_round16_*.py`），无一处 Edit 静默丢失。
- 移动端 mock 断点 ≤760px 收侧栏保对话，与主应用「窄屏保对话区」决策一致。

## 四、已知边界

1. G CTA 4.45:1、D ink-low 2.56:1 为 v11/v13 遗留令牌取值，本轮如实标注不动（详见 CHANGELOG-v14 §七）。
2. 移动端 ≤1024px 会话卷册/右栏不可达为既有决策，归工作台信息架构重构轮。
3. mock 为静态复刻，工作台改版需低成本同步。

## 五、追溯

- 版本变更文档：[`CHANGELOG-v14.md`](./CHANGELOG-v14.md)
- 上一轮：[`OPTIMIZATION_ROUND15.md`](./OPTIMIZATION_ROUND15.md)
- 版本索引：[`README.md`](./README.md)
