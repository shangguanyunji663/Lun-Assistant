# 论匠前端 · ROUND19 — 六套皮肤可读性与信息层次

> 文档域：frontend-versions
> 文档类型：轮次记录
> 主题版本：v18
> 轮次：ROUND19
> 日期：2026-10-02
> 状态：已落地

> 一句话背景：v18 把工作台重写为六套完整设计语言后，**可读性与信息层次在六套里同时塌陷**——小字压到 8.5px、正文列只占全宽 37%、「待确认」条比消息还重、六条执行时间线完全等权、空态是居中模板。本轮逐套修复，**每套用各自的视觉语言实现**，不做统一模板。**编号依据**：前端版本线既有轮次止于 ROUND18，本轮顺延为 ROUND19；主题版本仍为 v18（皮肤体系未升级，六套 ID 与令牌契约均未变）。

---

## 一、本轮改进总览

### 1.1 背景

在 1680×1050 实机截图中逐项量测六套皮肤，发现五类问题（以皮肤 A 为例，余五套同源）：

| # | 问题 | 实测值 | 性质 |
|---|---|---|---|
| 1 | 硬编码小字号 | 单套最多 21 处用 8 / 8.5 / 9 / 9.5px（六套合计 89 处） | 可访问性缺陷 |
| 2 | 正文被挤窄 | `.wb-body` 左右栏合计 584px，正文列占全宽 37% | 可读性 |
| 3 | 「待确认」条喧宾夺主 | 3px 纯黑顶边 + 实底高饱和 badge，权重压过消息本身 | 信息层次 |
| 4 | 执行时间线等权 | 六条无任何区分（仅 `is-interrupt` 标题变色） | 信息层次 |
| 5 | 空态是居中模板 | 印章 + 标题 + 说明 + 三个胶囊按钮全居中 | 版式模板化 |

> 第 1 项的性质说明：中文在 Windows ClearType 下低于 11px 会糊成一团，这是**可访问性问题而非审美偏好**，六套一律提到 11px（B / D 因分别依赖等宽读数与竖排，下限抬到 12.5px / 12px）。

**一次返工**：本轮第一版把同一套改动（同样的 1px 竖线、同样的描边 badge、同样的 `counter()` 序号）套给六套皮肤，被判定为「统一模板 + 换数值」，本身仍是千篇一律，已全部推翻重写。第二版改为每套用自己的视觉语言实现同一批改进，见 §二。

### 1.2 涉及的前端模块或文件

| 文件 | 改动 | §15 段行号 | 类型 |
|---|---|---|---|
| `frontend/src/skins/a-letterpress.css` | 小字 15 处 + 专属修正段 | 648–726 | 修改 |
| `frontend/src/skins/b-console.css` | 小字 12 处 + `--fs-micro` + 专属修正段 | 950–1032 | 修改 |
| `frontend/src/skins/c-poster.css` | 小字 12 处 + `--fs-micro` + 专属修正段 | 818–893 | 修改 |
| `frontend/src/skins/d-bamboo.css` | 小字 15 处 + 专属修正段（含空态整块竖排） | 895–971 | 修改 |
| `frontend/src/skins/e-riso.css` | 小字 14 处 + `--fs-micro` + 专属修正段 | 782–865 | 修改 |
| `frontend/src/skins/f-archive.css` | 小字 21 处 + `--fs-micro` + 专属修正段 | 919–999 | 修改 |

合计 `+591 / -99`（`git diff --stat`）。**工作台 React 组件、后端、落地页、动效层 `fx.css`、共享底座 `base.css` / `panels.css` 全部零改动**——本轮只改皮肤 CSS，符合 [`CONTRACT.md`](../../frontend/src/skins/CONTRACT.md) §四「只写 CSS」与「追加段须置于文件末尾」的约定。

### 1.3 具体改动要点

| # | 改动 | 类型 |
|---|---|---|
| 1 | 六套中 89 处 `font-size: 8 / 8.5 / 9 / 9.5px` → `11px`；B/C/E/F 的 `--fs-micro: 10.5px` → `11px` | 修复 |
| 2 | 每套文件末尾追加「§ 15 · 可读性与信息层次」段（76–84 行），内含该套专属的七组改动 | 新增 |
| 3 | 正文放大：AI 正文 15.5 → 17px（B/C/E/F 为 16.5px），用户消息 15 → 16px，行宽落到每行 40±5 字 | 修改 |
| 4 | 侧栏收窄：A 262/322→240/272、B 252/312→244/296、C 236/292→224/280、E 262/322→240/296、F 250/286→238/276；D 为两栏，仅右栏 302→280 | 修改 |
| 5 | 命中区补到桌面 a11y 基线 30–32px（`.wb-vol-del` / `.wb-view` / `.wb-side-tab`） | 修复 |
| 6 | 六套空态全部去对称居中，改用各自语言重做（详见 §二） | 修改 |
| 7 | B 的告警灯 `@keyframes b-alarm` 提到**顶层**（原写法嵌在选择器块内，浏览器静默忽略） | 修复 |
| 8 | 新增实机截图归档 `docs/frontend-versions/v18-screenshots/`（10 张：六套主界面 + C/D/F 三套空态 + A 的优化前基线） | 新增 |

### 1.4 与之前几轮修改的关系

- **修复**：v18 建立皮肤体系时留下的可读性缺口（v18 关注「六套语言成立与否」，未逐套校对小字与行宽）。
- **新增**：「§ 15 修正段」这一约定本身——每套皮肤末尾保留一段专属于自己的可读性修正，可整体删除回退。
- **不涉及**：v15 的 C1~C3（工作台编辑器式重构）仍待排期；金碧 / 青花瓷两款新皮肤提案仍在 `frontend/design-samples/skin-g/` 探索中，**未进入本轮**。

---

## 二、六套皮肤的差异化改动

同一批改进目标（顶栏分组 / 待确认条降权 / 时间线分主次 / 命中区 / 空态去居中），六套各有自己的实现语言：

| 皮肤 | 顶栏分组 | 中断条「待确认」 | 时间线状态标记 | 空态 |
|---|---|---|---|---|
| **A 铅字印刷** | 字号阶梯分主次，**不画线**（报纸本就不用线分组） | 更正栏：淡朱底 + 左朱线 | 编号前**朱红校对方块**（红笔校对） | 报纸版面：衬线提纲，悬停整行泛朱 |
| **B 夜航仪表** | **发光分区状态灯** | 发光告警框（`inset ring` + 外发光） | interrupt 编号**闪烁**（`b-alarm`） | 待机画面：等宽 `/` 快捷指令 |
| **C 学术海报** | **3px 粗黑竖条**（海报 rule 本就粗） | 黑底荧光绿字印章 | `Fig.` 图注编号 | **64px 巨幅标题** + 44px 巨号序号 |
| **D 木牍竖排** | **方框**分组（简牍形制是方裁） | 朱印方章 | 编号**竖排方框签** | **整块 `writing-mode: vertical-rl`** |
| **E 孔版双色** | **错位套印**（粉块偏右 2px、青块偏左 2px） | 硬阴影方章（阴影色为辅色） | 撞色粉条 | 硬阴影拼贴卡，奇偶换阴影色 |
| **F 索引档案** | **字段名** `SKIN` / `VIEW` | 斜置图章 + 虚线撕口 | 走纸孔圆点 + 撕线 | 待录条目（等宽 +「待录 01」） |

### 2.1 A · 铅字印刷

顶栏右侧原本 4 组元素等距平铺、语义边界不清。A 的解法**不用分隔线**，而是把字号拉开层次：视图切换（15px，二级导航）> 用户名（13.5px）> 皮肤切换（11px，工具）。

```css
html[data-skin="a"] .wb-view { padding: 6px 0; font-size: 15px; letter-spacing: .06em; }
html[data-skin="a"] .sp-label { font-size: 11px; letter-spacing: .1em; }
```

时间线用**校对标记**而非左边条——编号前挂一枚 7px 的朱红/墨色方块，`.is-interrupt` 那条换朱红方块并给淡朱底。空态是未开天窗的报纸版面：`.wb-prompt` 用衬线 17px、左侧 44px 让位给等宽序号，悬停整行泛朱。

### 2.2 B · 夜航仪表

B 的语言是仪表台，所以分组用**发光状态灯**、待确认用**告警框**、时间线用**遥测灯**：

```css
html[data-skin="b"] .skin-picker::before,
html[data-skin="b"] .wb-views::before {
  content: ""; display: inline-block; width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent); box-shadow: 0 0 8px var(--accent); margin-right: 9px;
}
```

空态做成仪表的**待机画面**：提示词是等宽 `/` 前缀的快捷指令，悬停时整行微亮并在左侧浮现 `▸` 光标。

> **修复**：`@keyframes b-alarm` 原写成 `html[data-skin="b"] @keyframes b-alarm { … }`，`@keyframes` 嵌套在选择器块内是无效语法，浏览器静默忽略、只有构建器给警告。已提至顶层（`b-console.css:1000`）。

### 2.3 C · 学术海报

海报的 rule 本来就粗，所以顶栏分组用 **3px 实心黑条**而非 1px 细线。空态是本轮改动幅度最大的一套——**64px 巨幅标题 + 44px 巨号序号**，因为巨幅排版正是海报的语言：

```css
html[data-skin="c"] .wb-empty h2 {
  font-size: 64px; line-height: .92; font-weight: 900; letter-spacing: -.02em;
  text-transform: uppercase;
}
html[data-skin="c"] .wb-prompt::before {
  font-size: 44px; line-height: 1; font-weight: 900; color: var(--accent);
}
```

C 是唯一保留**满幅排版**的皮肤（不加 `max-width`），改为在 `.wb-bubble` 上限制单行行宽 `max-width: 66ch`。

### 2.4 D · 木牍竖排

空态是六套里唯一**整块改 `writing-mode`** 的皮肤：从右向左排成一列竹简（朱印 → 标题 → 说明 → 三条带序号的签条）。

> **两次返工**：① `flex-direction` 方向搞反——`vertical-rl` 下 `row` 沿行内轴（**竖直**）、`column` 才是块轴（水平右→左），初版用 `row` 导致元素竖着堆下来、布局全乱；② 固定高度 460px 让下半屏留出大片空白，改为有界高度 330px 并加上下外边距。

```css
html[data-skin="d"] .wb-empty {
  writing-mode: vertical-rl; text-orientation: upright;
  display: flex; flex-direction: column; align-items: flex-start; gap: 30px;
  height: 330px; margin: 40px 0 40px auto; padding-left: 28px;
}
```

D 是两栏皮肤（卷册已改为顶部横排书签栏），故只收窄右栏、不动列数。

### 2.5 E · 孔版双色

顶栏分组直接用**错位套印**：粉块 `translate(2px, -2px)`、青块 `translate(-2px, 2px)`，套印故意不对齐。消息气泡统一硬阴影（AI 用墨色、用户用辅色），空态是三张硬阴影拼贴卡，`nth-child(even)` 换阴影色。

### 2.6 F · 索引档案

顶栏分组用**档案字段名**（等宽 `SKIN` / `VIEW`）而非线条——这正是 F 顶栏原有的「档案号 / 卷宗 / 密级」字段条语言的延续。时间线左侧是**打印纸撕线 + 走纸孔圆点**，空态提示词是「待录 01」式的待填档案条目。

---

## 三、全局共性改动

只有两项是六套共用的，且都属于**可访问性底线**而非风格：

1. **元信息字号下限 11px**（共 89 处）：`.wb-msg-role` / `.wb-msg-time` / `.wb-vol-no` / `.wb-vol-meta` / `.wb-tl-no` / `.wb-tl-meta` / `.wb-ch-en` / `.wb-ch-cn` / `.wb-break-badge` / `.wb-compose-hint` / `.sp-caret` 等。中文低于 11px 在 Windows ClearType 下会糊。
2. **命中区 30–32px**：`.wb-vol-del` 20×20 → 30×30（`.wb-view` / `.wb-side-tab` 按各自 padding 补齐），视觉符号尺寸不变，仅扩大点击热区。

---

## 四、验证结论

- **构建**：`npm run build` 通过（`✓ built in 3.01s`），无 CSS 警告。
- **静态校验**：六文件大括号配平（差值 0）；`font-size: 8px / 8.5px / 9px` 残留 **0 处**；各文件 `§ 15` 段唯一。
- **实机取证**：1680×1050 下逐套截取真实界面（headless Chrome + `?demo=1` 预览模式），归档 `docs/frontend-versions/v18-screenshots/`；C / D / F 的空态改动在有消息的界面里不可见，另用 `preview-empty.html` 单独取证。
- **自查未覆盖**：仅在 1680 宽下取证；1280 / 1024 / 768 三档响应式沿用各皮肤既有 `@media` 规则，本轮未改断点值，但新增的 `max-width`（A / E）在 `≤1380px` 下已同步解除。

---

## 五、已知边界 / 未覆盖项

1. **中栏两侧的留白是刻意的**：`.wb-inner` 限宽让正文列占全宽约 40±5 字，两侧留白是长文可读性的必要代价（Medium / GitHub 同此策略），**未再放宽**——放宽到 900px 会让每行 48 字，超出舒适上限。
2. **中栏下半部空白**在 demo（仅 2 条消息）下较明显，属数据状态而非设计缺陷；真实使用会填满。若要处理，正确做法是在留白区放低干扰的卷宗抬头（需改 JSX 新增 DOM），不在本轮。
3. **落地页六页未同步**：本轮只改工作台皮肤 CSS。落地页是每皮肤一个独立 HTML，其版式与工作台不同构，另行处理。
4. **金碧 / 青花瓷两款新皮肤**仍在 `frontend/design-samples/skin-g/` 探索中，未进入生产；其落地需要先修订 `CONTRACT.md` §四第 2 条（「只写 CSS，不得修改任何 .jsx/.html/.js」）以允许可选的皮肤增强脚本。
5. **§ 15 段的维护约定**：新增皮肤时须自行补齐该段（本轮六套的写法互不相同，不存在可复制的模板）。

---

## 六、追溯 / 关联文档

- 版本索引：[`README.md`](./README.md)
- 上一轮：[`OPTIMIZATION_ROUND18.md`](./OPTIMIZATION_ROUND18.md)（落地页一致性 + 三枚彩蛋机关）
- 本轮所修的体系起点：[`CHANGELOG-v18.md`](./CHANGELOG-v18.md)（六套设计语言）
- 皮肤契约：[`../../frontend/src/skins/CONTRACT.md`](../../frontend/src/skins/CONTRACT.md)
- 格式规范：[`../FORMAT_STANDARD.md`](../FORMAT_STANDARD.md)
- 实机截图：[`v18-screenshots/`](./v18-screenshots/)（`skin-a-before.png` 为优化前基线）

---

*ROUND19 · 六套皮肤可读性与信息层次 · 每套以各自视觉语言实现 · 工作台 React 组件 / 后端 / 落地页零改动*