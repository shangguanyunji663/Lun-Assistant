# 论匠前端 · 第十五轮修改 · 落地页（静态多页 + 双主题）

> 文档域：frontend-versions
> 文档类型：轮次记录
> 主题版本：—（工作台七主题体系未动）
> 轮次：ROUND15
> 日期：2026-09-30
> 状态：已落地

> 一句话背景：为仓库 Pages 入口新增「落地页」门面（WorkBuddy 六段产品站节奏 + B 编辑部排印 + C 职人细节），工作台入口迁至 `app.html`，全程零新依赖；落地页自带亮·天青 / 暗·玄墨双主题（独立于工作台七主题机制），动效纯 CSS + ~1.5KB 原生 JS。Grill Me 共识：Q1 混合式 / Q2 先落地页后编辑器重构 / Q3 双主题 / Q4=A 静态多页 / Q5 轻动效。

---

## 一、本轮改进总览

| 维度 | 上一轮（v13 / ROUND14） | 本轮（ROUND15） | 改动 |
|---|---|---|---|
| 站点入口 | `/` 即工作台 | `/` = 落地页，工作台迁 `app.html` | 是 |
| 落地页 | 无 | 六段叙事静态页（双主题） | 新增 |
| 构建形态 | 单页 | Vite 多页（main + app 双入口） | 是 |
| 工作台 | 七主题 | 功能与样式零改动（仅入口改名 + 登录页加返回链接 + 文末追加 @view-transition） | 否 |
| 新依赖 | — | **零** | 否 |
| 落地页 JS | — | 1.48 KB（gzip 0.67 KB） | 新增 |

## 二、文件级变更摘要

| 文件 | 改动 | 行号范围 | 类型 |
|---|---|---|---|
| `frontend/app.html` | 工作台入口（原 index.html 内容，标题改「论匠 · 工作台」） | — | 新增 |
| `frontend/index.html` | 重写为落地页（六段叙事 HTML） | 全文 | 重写 |
| `frontend/vite.config.js` | `build.rollupOptions.input` 双入口 + `fileURLToPath` import | 1-2, 11-19 | 修改 |
| `frontend/src/landing.css` | 落地页全量样式：双主题令牌 / 编辑部排印 / 暗色评测区 / 页脚描边大字 / 入场动画 / reduced-motion / 响应式 | ~370 行 | 新增 |
| `frontend/src/landing.js` | 主题切换（localStorage `lj_landing_theme`）/ IO 入场 / 数字滚动 / 年份 | 80 行 | 新增 |
| `frontend/src/styles.css` | 文末追加 `@view-transition` 声明 | 文末 §18 | 修改（纯追加） |
| `frontend/src/components/AuthPage.jsx` | 登录卡增加「← 返回论匠首页」链接 | 67-69 | 修改（+2 行） |
| `frontend/public/assets/preview-a.webp` | Hero 截图（柔雾青绿，159→24 KB） | — | 新增 |
| `frontend/public/assets/preview-f.webp` | 暗区截图（玄墨赭金，117→20 KB） | — | 新增 |

## 三、具体改动要点

### 3.1 落地页六段叙事（index.html）

1. **Nav**：朱砂钤印 + 衬线品牌字 + 章节锚点 + 主题切换按钮（内联 SVG 日/月，无 emoji）+「进入工作台」
2. **Hero**：衬线大标题「论匠，帮你把论文写完。」+ 真实工作台截图（mac 窗口框 + 极浅品牌色光晕）
3. **六能力**：01 选题立项 / 02 文献检索 / 03 分章写作 / 04 格式约束 / 05 引用核查 / 06 答辩准备——描述全部对应仓库真实能力（planner、RRF 融合、structured_memory、interrupt、trace）
4. **架构与评测（暗色区块）**：LangGraph / pgvector / Redis / Ollama 四要点 + 四项真实指标（意图 100%、Recall@5 100%、回归 16/16、离线用例 89）+ **诚实标注水位**（长尾 80% · 学术 95% · hold-out 75%），出处指向 `docs/EVALUATION_REPORT.md`
5. **人机协同三卡**：产出需确认 / 全链路留痕 / 记忆沉淀
6. **入口三卡 + 黑页脚**：在线试用（主卡）/ GitHub / 学习指南；页脚描边大字 `LUNJIANG>_`

### 3.2 双主题令牌（landing.css:11-46）

- 亮·天青：`--ln-bg #F2F5F2` / 墨 `#22302A` / 强调青绿 `#3A6B5C` / 朱砂 `#9E3B2C`
- 暗·玄墨：`--ln-bg #171512` / 象牙 `#E9E2D4` / 赭金强调 `#C2955A`（与工作台 F 主题同源）
- 反 AI 味约束：单强调色、实色 CTA、无毛玻璃、0.5px 边框、朱砂 ≤2%、仅 Hero 一层 10% 透明度光晕

### 3.3 动效（WorkBuddy 实测配方的零库实现）

| 效果 | 实现 | 成本 |
|---|---|---|
| 跨页丝滑 | `@view-transition { navigation: auto }`（styles.css:1294 + landing.css） | 0 KB JS |
| 入场 stagger | IntersectionObserver + `.ln-reveal` → `.ln-in` | ~0.5 KB |
| 评测数字滚动 | IO + rAF 缓动计数，`tabular-nums` 防抖动 | ~0.6 KB |
| 降级 | `prefers-reduced-motion` 下动画全关、内容直出；无 IO 能力时直出 | — |

## 四、与之前几轮 / 相邻版本的关系

| 关联项 | 关系说明 |
|---|---|
| v13（ROUND14） | 七主题体系与令牌零改动；落地页截图素材取自 v13-screenshots |
| ROUND12/13 | backend 域轮次，无交集 |
| Q2-C（编辑器式重构 C1~C3） | 后续轮次；落地页为纯静态，重构期间零波及 |

## 五、验证清单（已全部执行通过）

- [x] `npm run build`：双入口产物 `dist/index.html`（9.98 kB）+ `dist/app.html`；落地页 JS 1.48 KB；工作台 JS 331.58 kB（与改前一致）
- [x] eslint 0 error（landing.js / AuthPage.jsx）
- [x] playwright：落地页 h1 / 图片加载 / 主题切换（dark + 文案「亮色」）/ reload 持久化（stored=dark）/ 计数器动画（100、16）/ 入场 20+ reveal
- [x] 跳转 `app.html` → 登录页「登 录」+ 返回首页链接存在
- [x] mock 登录 → 工作台 7 主题 tab 完好、默认主题 a —— **工作台零回归**
- [x] 控制台 0 error；landing-light / landing-dark 截图留档

## 六、已知边界 / 未覆盖项

1. 编辑器式工作台重构（Q2-C1~C3）为后续轮次，本轮未动工作台信息架构。
2. 落地页双主题独立于工作台七主题（localStorage 键不同：`lj_landing_theme` vs `lj_theme`），互不同步——设计如此。
3. View Transitions 在不支持的浏览器（老 Firefox）自动降级为普通跳转。
4. Pages 部署：推送后由现有部署链自动生效，本轮未推送。
5. 「学习指南」入口指向 GitHub main 分支的中文文件名 URL（已编码），若文件改名需同步。

## 七、追溯 / 关联文档

- 版本索引：[`README.md`](./README.md)
- 上一轮：[`CHANGELOG-v13.md`](./CHANGELOG-v13.md)（ROUND14）
- 评测数字出处：[`../EVALUATION_REPORT.md`](../EVALUATION_REPORT.md)
- 格式规范：[`../FORMAT_STANDARD.md`](../FORMAT_STANDARD.md)

---

*ROUND15 · 落地页（静态多页 + 双主题）· 零新依赖 · 工作台零回归*
