# ROUND20 补记 · 两页新语言落地为第 7/8 套皮肤（八套体系）

> 文档域：frontend-versions
> 文档类型：版本变更
> 主题版本：v18（皮肤体系 6 → 8 套）
> 轮次：ROUND20 补记
> 日期：2026-10-03
> 状态：已落地

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