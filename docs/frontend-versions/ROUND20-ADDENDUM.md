# ROUND20 补记 · 两页新语言落地为第 7/8 套皮肤（八套体系）

> 文档域：frontend-versions
> 文档类型：版本变更
> 主题版本：v18（皮肤体系 6 → 8 套）
> 轮次：ROUND20 补记
> 日期：2026-10-03
> 状态：已落地

> ⚠️ **变更标注（2026-10-05 · 后续小轮同步）**：本补记落档后，2026-10-04 又有三笔前端改动直接落在 G/H 两页与工作台，**正文保留不改**，现状以代码为准：
>
> - **皮肤切换器（`53e66d3`）**：落地页触发按钮文案由「当前皮肤名」统一为「**切换皮肤**」（`shared.js` 注入式 + 两页静态各一处）；how-it-works / dossier 的切换器条目 6 条 → **8 条**；修掉 A 原指向不存在的 `/landing-a.html`（改为 `/index.html`）；**拆除两页之间的内容互链**（导航 / CTA / 页脚），仅保留切换器里的 8 套导航（§二「六张旧落地页的导航与页脚加两页入口」对六张旧页仍成立）。
> - **入口语义分离（`c145c1a`）**：「工作台预览」保留 `/app.html?demo=1`（免登录演示），「进入工作台」改为 `/app.html`（未登录走登录页）。此前两页 9 处工作台链接全带 `?demo=1`，从这两页进入会强制演示模式、无法正常登录。
> - **工作台（`b320004`）**：切换项目即另起新会话（时间线随项目上下文归零，旧会话留在卷册可切回）；`Timeline` 渲染 `step_event` 的工具调用进度（进行中 / 完成+耗时 / 异常）。
> - 两页内容同时充实：how-it-works 补「配器表 / 指挥权在你手里 / 三种方式，开始排练」；dossier 补「技术附件 FILE 07-09」与收尾 CTA；八张落地页离线用例数口径 89 → **93**。

## 一、发生了什么

此前 ROUND20 正文记录了两页设计样张（「可演奏的总谱」/「解密卷宗」）经多轮迭代的过程。本次把这两页**正式落地**，并让它们以**独立设计语言**的身份加入皮肤体系——从六套扩为八套：

| 新增 | 语言 | 工作台皮肤 | 独立页面 | 机制 |
|---|---|---|---|---|
| 第 7 套 | 编队总谱（钴蓝谱纸） | `g-score.css` | `how-it-works.html` | 出声音符 / 演奏全曲 / fermata 停拍 |
| 第 8 套 | 论文底片（暗房单色） | `h-contact.css` | `dossier.html` | 逐条解密 / 阵风 / 打字机音效 |

## 二、决策链（grill-me 定案）

- **八套构成** = 6 工作台皮肤 + 2 新语言。机制**绑定独立页面**，不进工作台皮肤（CONTRACT「只写 CSS」契约不破）
- **金碧/青花候选废稿**：`g-jinbi.css` / `h-qinghua.css` / `design-samples/skin-g/` 全部删除
- **导航扩容**：六张旧落地页的导航与页脚加两页入口；registry 加 g/h；工作台换肤器 8 选 1
- **命名**：编队总谱 / 论文底片

## 三、落地清单

| 文件 | 改动 |
|---|---|
| `src/skins/g-score.css` | 新建。按 CONTRACT 全套：令牌 / 外壳 / 顶栏 / 按钮 / 选择器 / 三栏 / 会话卷册 / 对话主区 / 中断条 / 输入区 / 右栏 / 次级面板 / 三档响应式 / 专属 §15（花括号空态、音符头时间线、fermata 中断条） |
| `src/skins/h-contact.css` | 新建。同规格，专属 §15（撕边用户纸条、接触印样时间线帧、反白视图切换） |
| `src/skins/registry.js` | +g/h 两条（label/chip/desc/landing/themeColor） |
| `src/main.jsx` | +2 import（g-score / h-contact） |
| `src/components/SkinPicker.jsx` | 弹层提示「6 选 1」→ 动态 `{skins.length}` |
| `src/landing/shared.js` | 落地页切换器「6 选 1」→ 动态 |
| `app.html` / `index.html` | 皮肤校验正则 `[a-f]` → `[a-h]`；index 站根把 g/h 记忆跳转到两页 |
| `vite.config.js` | +2 入口（how-it-works / dossier） |
| `how-it-works.html` / `dossier.html`（根目录） | 从 design-samples 复制并改名、路径改正式、进构建 |
| 六张旧落地页 | 导航 + 页脚加「编队总谱」「论文底片」入口 |
| `src/skins/CONTRACT.md` | 八套体系说明、G/H 令牌注记、自检清单加两页语义一致项 |
| 删除 | `src/skins/g-jinbi.css` / `h-qinghua.css` / `design-samples/skin-g/` |

## 四、验证记录

- `npm run build` ✓（5.19s，两页入产物，新皮肤进 app.css 26.51kB gzip）
- `eslint .` 零告警；`verify-state.mjs` 三场景全过、无页面错误
- 工作台 `data-skin=g`：背景 `#F3F3EE` 钴蓝谱纸、三栏齐、零报错（截图 `_design-shots/workbench-g.png`）
- 工作台 `data-skin=h`：背景 `#141416` 暗房、三栏齐、零报错（`workbench-h.png`）
- 两页正式可达：标题「编队总谱 · 论匠工作原理」/「论文底片 · 一篇论文的全程留痕」

## 五、追溯

- 本轮设计过程的完整迭代史见 `OPTIMIZATION_ROUND20.md` 正文（样张 v1→v4、去 AI 味、机制补全、环境动效、密度、导航对齐）
- 原样张仍留档于 `design-samples/round20-pages/`（how-it-works.html / sample-dossier.html 为历史版本，不参与构建）