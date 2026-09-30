# 论匠前端 · ROUND17 — 现代艺术四主题落地 · 落地页双结构共存

> 文档域：frontend-versions
> 文档类型：优化轮次记录
> 主题版本：v15
> 轮次：ROUND17
> 日期：2026-09-30
> 状态：已落地

> 一句话背景：承接用户「推翻固有模板思路、旧 7 版保留共存、主页与工作台注入现代艺术气息」需求——样图确认（四方向全选、共存切换、引入开源 web 字体）后全量落地：工作台 +4 主题（共 11）、落地页编辑部双结构（共 6 主题），功能与内容零改动。

---

## 一、本轮改进总览

### 1.1 背景

v14 收尾后用户提出视觉升级需求：现有 7 版偏复古要保留，但整体要摆脱「千篇一律的 AI 生成风格」，要求流畅入场动画、滚动动效、悬停微交互、页面过渡，以及更有层次的配色 / 个性化字体排版 / 质感背景装饰。本轮以「样图先行 → 用户拍板 → 生产落地」三段推进。

### 1.2 涉及的前端模块或文件

- 样图阶段：`frontend/design-samples/sample-{a,b,c,d}.html`（零依赖静态样图 ×4，含可交互动效）
- 生产落地：`app.html` / `index.html` / `src/styles.css` / `src/landing.css` / `src/landing.js` / `src/hooks/useTheme.js` / `public/console/tuner.html`

### 1.3 具体改动要点

| # | 改动 | 类型 |
|---|---|---|
| 1 | 工作台新增 H 墨格编辑部 / I 新构成主义 / J 夜航诗意 / K 拓印套色 四主题（令牌 + 个性覆盖 + 纹理 + 字体覆盖） | 新增 |
| 2 | 落地页编辑部双结构：#ed-site 新版式（masthead/揭示 hero/marquee/目次/指标带/mock/版权页），light/dark 走原结构，h/i/j/k 走新结构 | 新增 |
| 3 | 主题切换扩容：工作台 A–K 十一档；落地页六档循环切换（label 显示下一档） | 迭代优化 |
| 4 | 字体接入：Noto Serif SC 700/900 + Archivo Black + IBM Plex Mono（CDN + 系统栈回退） | 新增 |
| 5 | tuner.html 追平至 A–K 十一主题（预览级还原 + v14 写入守卫延续） | 迭代优化 |
| 6 | 动效体系：hero 逐行揭示（切换自动重播）、marquee、几何漂浮（i）、hover 硬阴影位移（i）、目次行位移、信号灯（j）、套色阴影（k） | 新增 |

### 1.4 与之前几轮修改的关系

- **新增**：四主题令牌与个性覆盖（styles.css §21）、落地页编辑部结构与六主题机制（landing.css §13）。
- **迭代优化**：useTheme/tuner 主题注册与切换扩容。
- **修复**：无（本轮纯增量，A–G 与 light/dark 既有规则零修改）。
- 承接：ROUND16 的 tuner 写入守卫、追加式约定；C1~C3 工作台编辑器化仍待排期（勿与本轮混淆）。

## 二、样图 → 生产还原说明

| 样图方向 | 落地为 | 还原度 | 舍弃项 |
|---|---|---|---|
| A 墨格编辑部 | 工作台 H + 落地页 ed-site 骨架 | 高 | 样图专属「期刊 folio 竖排页码」（落地页双结构下与现有 nav 冲突，舍） |
| B 新构成主义 | 工作台 I + 落地页 h 下几何变体 | 高 | Archivo Black 英文展示字（ed-site 中文为主，未用；工作台 brand 保留行楷体系外主题） |
| C 夜航诗意 | 工作台 J + 落地页 j 变体 | 高 | 打字机 JS（落地页改用零 JS 的逐行揭示；工作台流式输出本身即打字机） |
| D 拓印套色 | 工作台 K + 落地页 k 变体 | 中高 | data-t 双层真叠印（落地页改 text-shadow 错位模拟，零结构成本） |

## 三、验证记录

- 构建：`vite build` 8.47s ✓；`eslint` 0 error ✓；landing.js 语法校验 ✓
- 截图：工作台 4 新主题 + 2 移动端、落地页 6 主题 + 1 移动端，共 13 张，0 页面错误
- 对比度：四主题正文/主底 H 12.9:1 / I 14.9:1 / J 15.4:1 / K 12.6:1（均 AAA）；CTA 见 CHANGELOG-v15 §七.4

## 四、工程纪律

- 追加式：styles.css §21（1649–2036）、landing.css §13（765–1056）全为文末追加，A–G/light/dark 零改动
- Python 补丁脚本 + assert count==1 + 写后 grep 复验；临时脚本已清理（design-samples 保留）
- 纹理零图片、动效全 GPU 属性、prefers-reduced-motion 全量降级（styles/landing 两处媒体查询覆盖新动画）

## 五、已知边界

1. J 中文标题回落系统黑体（Plex Mono 无中文），落档标注
2. CDN 字体离线降级；woff2 子集化本地化为后续可选项
3. ed-site 与 ln-site 文案为同源静态副本，需人工同步
4. 移动端既有决策（≤1024px 侧栏收起）不变

## 六、追溯

- 版本变更：[`CHANGELOG-v15.md`](./CHANGELOG-v15.md)
- 设计样图：`frontend/design-samples/`
- 上一轮：[`OPTIMIZATION_ROUND16.md`](./OPTIMIZATION_ROUND16.md)
