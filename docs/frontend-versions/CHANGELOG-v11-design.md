# 论匠前端 · v11 四主题重构 — 变更文档

> 文档域：frontend-versions
> 文档类型：版本变更
> 主题版本：v11
> 轮次：—
> 日期：2026-09-01
> 状态：已落地

> 本轮以**用户提供的 4 张参考图为唯一视觉基准**，对 `preview.html` 与 `tuner.html` 做整体重写，从三主题（A/B/C）扩展为四主题（A/B/C/D），并把配色、字体、圆角、阴影全部纳入 CSS 设计令牌统一管理。

---

## 1. 总览（结论先行）

| 主题 | 对应参考图 | 主色 | 强调色 | 字体策略 | 圆角 | 阴影 |
| --- | --- | --- | --- | --- | --- | --- |
| **A 柔雾青绿** | `Soft_misty_Chinese_blue_green__2026-09-01T13-51-14.png` | 浅蓝薄雾 `#DDE9F0` | 石青 `#4A8BAB` + 青绿 `#5B9E84` | 思源宋体 / PingFang | 20 px（柔润） | 淡蓝投影 |
| **B 水墨留白** | `Traditional_Chinese_ink_wash_l_2026-09-01T13-40-46.png` | 宣纸米 `#ECE6D6` | 水墨黑 `#2C2820` | **楷体** STKaiti | 14 px（紧致） | 极淡 |
| **C 暗墨夜山** | `Chinese_ink_painting_of_toweri_2026-09-01T13-41-26.png` | 墨夜 `#050B11` | **月光米 `#F2EBD0`** | PingFang + 楷体点缀 | **22 px（最柔）** | 极深 + 月光晕 |
| **D 青绿金碧** | `Traditional_Chinese_blue_green_2026-09-01T13-40-09.png` | 古绢黄 `#C9B58A` | 宝石蓝 `#2E5C8A` + 石绿 `#4F8762` + 金泥 `#B89048` | 楷体 | 18 px（华丽） | 暖金投影 |

变更结论：
1. **结构**：从「3 mockup 并列」扩展为「4 mockup 并列」，所有交互节点（知识库切换、上传、控制台入口、资料清单）保持语义不变。
2. **样式系统**：每张参考图对应的样式全部通过 `:root, body[data-theme="a/b/c/d"]` 下的 CSS 变量切换，整套 UI 联动只改一个 `data-theme` 属性。
3. **token 维度**：每个主题管控 17 个 token（背景层 7 个 + 文本/边框/强调 5 个 + 阴影 3 个 + 字体 2 个）。
4. **响应式**：`preview.html` `.grid` 阈值由 `1280 px / 720 px` → `1640 px / 720 px`，保证 4 列并排在 1920 屏上仍一行展示完整。

---

## 2. 文件级变更摘要

| 文件 | 改动 | 行数 |
| --- | --- | --- |
| `preview.html` | 整体重写（三主题 → 四主题 + design tokens + 新增 C 暗墨夜山 / D 青绿金碧） | 854 |
| `tuner.html` | 整体重写（三主题 → 四主题 + 全部 token 化 + 顶部金线/月色边线/中缝等微装饰） | 857 |
| `CHANGELOG-v11-design.md` | 本文档（新文件） | — |

---

## 3. 全局工程变更（两份 HTML 共有）

### 3.1 Design Token 系统
两份文件的 CSS 顶端统一沿用以下 17 个变量，**主题切换只动 `:root, body[data-theme="X"]` 块，其他地方全部 `var(--token)` 引用**：

```css
/* 背景层 */
--bg-page, --bg-card, --surface, --surface-2, --surface-side,
--surface-active, --surface-input, --surface-accent-soft, --surface-kbswitch,
--topbar-bg
/* 文本 / 边框 / 强调 */
--border, --border-strong, --text, --text-muted, --accent, --accent-on
/* 阴影 / 圆角 / 字体 */
--shadow-tabs, --shadow-on, --shadow-mockup, --shadow-col,
--radius-card, --radius-col, --radius-topbar,
--font-serif, --font-serif-title, --font-sans
```

实施位置：
- `preview.html:11-89`（tokens 在 `body[data-theme="X"]` 中声明）；
- `tuner.html:350-487`（同位置，token 维度更全）。

### 3.2 字号 / 行高 / 字距体系
| 元素 | A 柔雾 | B 水墨 | C 暗墨 | D 金碧 |
| --- | --- | --- | --- | --- |
| 品牌 `brand` 字距 | 0.24em | **0.42em（楷体宽字距）** | 0.18em | **0.36em** |
| 品牌前缀短线 | × | ✓ (`brand::before`，深墨） | × | ✓（金泥色） |
| 主标题字体 | 思源宋体 | **STKaiti** | 思源宋体 + 月色 | **STKaiti** |
| 按钮字距 | 0.08em | 0.06em | 0.10em | 0.10em |
| 会话册 / 资料面板头 | 0.20em | 0.30em | 0.18em | 0.28em |

### 3.3 响应式
- `preview.html:85-87`：`.grid` 在 `max-width: 1640px` 退到 2 列、`max-width: 720px` 退到 1 列。
- `tuner.html:43-44`：`main` 在 `max-width: 1180px` 改为列排，控制面板下移到预览下方。

---

## 4. 主题 A · 柔雾青绿（参考图：sky / 水乡薄雾）

### 4.1 视觉锚点
- 参考图：`Soft_misty_Chinese_blue_green__2026-09-01T13-51-14.png`
- 主调：**浅蓝灰底 + 远山青绿 + 石青点缀**。
- 关键色彩：
  - 底色：`--bg-page: #E8EFF3`（米蓝渐变）
  - 卡片渐变：`linear-gradient(180deg, #DDE9F0 0%, #C5DBE8 100%)`
  - 文本：`#1F3A4D`（深海蓝）
  - 强调 A：`#4A8BAB`（石青，主按钮 / 选中态）
  - 强调 B：`#5B9E84`（青绿，user bubble / tag）

### 4.2 文件 / 行号引用
| 项 | preview.html | tuner.html |
| --- | --- | --- |
| token 声明 | `:164` | `:350` |
| ink-bg 图片 | `:282`（单 stage）/`:497`（compare） | `:67` |
| ink-veil 遮罩 | `:206`（覆盖底色 0.55 渐隐） | `:83`（深蓝遮罩 + 顶部月光） |
| 顶栏背景 | `:208`（`rgba(255,255,255,.65)` + 14 px 模糊） | `:436` |
| 用户气泡 | `:209-210`（青绿描边 + 白底） | — |
| 主控气泡 | `:211-212`（石青描边 + 半透白） | — |
| 资料面板 | `:213` `.ap-tag` | — |
| 阴影 token | `--shadow-mockup: 0 16px 48px rgba(74,139,171,.22)` | 同上 |

### 4.3 关键调整
- 移除「卷轴木轴」装饰（原 v10 `.wood.top / .wood.bot`），改用纯透明柔雾。
- `font-family` 走 `Songti SC + PingFang`，不用楷体。
- 主按钮 `:hover` 走 `color: var(--text); border-color: var(--accent)`，A 主题下边框线变石青色。

---

## 5. 主题 B · 水墨留白（参考图：宣纸 + 枯枝 + 远山）

### 5.1 视觉锚点
- 参考图：`Traditional_Chinese_ink_wash_l_2026-09-01T13-40-46.png`
- 主调：**宣纸米 + 极淡远山 + 楷体**。
- 关键色彩：
  - 底色：`--bg-page: #ECE6D6`（宣纸）
  - 卡片渐变：`linear-gradient(180deg, #ECE6D6 0%, #E0DAC9 100%)`
  - 文本：`#2C2820`（水墨黑）
  - 强调：`#2C2820`（与文本同色，区别仅靠粗细 / 反白）
  - 反白：`#ECE6D6`（按钮底）

### 5.2 文件 / 行号引用
| 项 | preview.html | tuner.html |
| --- | --- | --- |
| token 声明 | `:205` | `:380` |
| ink-bg 图片（位于右下） | `:223`（`object-position: right bottom; width:65%; height:65%`） | `:69`（`right bottom / 65% no-repeat`） |
| ink-veil 极淡遮罩 | `:224` | `:89`（与 A 不同，top 遮罩仅 6%） |
| 字体 | `:226` `'STKaiti','KaiTi','楷体',serif` | `:387` |
| 品牌前缀竖线 | `:227-229` `brand::before { content:''; width:18px; height:1px; ... }` | `:173` |
| 用户气泡 | `:230-232`（深墨描边 + 米色底 + `border-top-right-radius: 4px`） | — |
| 主控气泡 | `:233-234` | — |
| 资料面板 + 知识库切换 | `:235-241` 深墨下未选中态 | `:454` 中竖线可见 |
| 响应楷体 | 所有 `font-family: var(--font-sans)` 都自动落到 STKaiti | 同上 |

### 5.3 关键调整
- **字体全量切到楷体**（`body`、`.brand`、`.card h2`、`.sess-head`、按钮等均 `var(--font-serif-title)`）。
- 顶部增加 `.ink-divider` 中竖线（仅 B/D 可见），保留传统中缝构图。
- user bubble 圆角改 `border-top-right-radius: 4px`（比常规更方正，强调毛笔楷韵）。
- 移除原 v10 顶部中间的 `.brand-rule` 短划线，改用 `::before` 一长短线（见 `:228`）。

---

## 6. 主题 C · 暗墨夜山（参考图：深夜墨蓝 + 满月 + 云海）

### 6.1 视觉锚点
- 参考图：`Chinese_ink_painting_of_toweri_2026-09-01T13-41-26.png`
- 主调：**极致墨黑背景 + 月光银白 + 深山剪影**。
- 关键色彩：
  - 底色：`--bg-page: #050B11`（接近全黑）
  - 卡片渐变：`linear-gradient(180deg, #0A1424 0%, #050B11 60%, #020508 100%)`（顶部稍亮，模拟夜天）
  - 文本：`#E8E2C8`（月光米）
  - 强调：`#F2EBD0`（满月光）
  - 红色钤印：`#B04A3A`（仅出现在 `.ink-stamp` "匠" 字章上）

### 6.2 文件 / 行号引用
| 项 | preview.html | tuner.html |
| --- | --- | --- |
| token 声明 | `:251` | `:410` |
| ink-bg 图片 | `:282 / :499` | `:73`（`center 30% / cover` 让山峰居中） |
| ink-veil 双层（径向月光 + 线性暗化） | `:280-284` | `:95` |
| 月亮 `.moon-glyph` | `:305-309`（右侧 28 px 径向渐变球 + 双层 box-shadow） | 见 §6.3（`tuner` 仅在底图内嵌，无独立 glyph） |
| 顶栏底部金 / 月光线 | `:294-296` `topbar::after { linear-gradient(90deg, transparent, #F2EBD0 50%, transparent) }` | `:146` 同步改 `.topbar-divider` |
| 钤印章 | `:262` `.ink-stamp { border-color:#B04A3A; color:#B04A3A; background:rgba(176,74,58,.12); }` | `:145` |
| 主按钮 `:hover` 月光晕 | `--shadow-on: 0 4px 20px rgba(242,235,208,.40)` | 同 |
| 文阴影 | `--shadow-mockup: 0 28px 64px rgba(0,0,0,.70), 0 0 80px rgba(232,226,200,.10)` | 同 |

### 6.3 关键调整
- **新增 `.moon-glyph`**（preview 模式新增 div，tuner 模式集成在 `.ink-photo` 内由径向 radial gradient 表达）。
- **钤印章"匠"**：默认隐藏（`opacity:0`），C 主题才显形（`opacity:1`），与原 v10 钤印一致。
- **文阴影最重**：四主题中阴影最深、圆角最大（22 px）—— 视觉上模拟夜空深景。
- 资料面板 `.kb-pill .dot` 月光白发光：`background:#F2EBD0; box-shadow: 0 0 8px rgba(242,235,208,.85)`。

---

## 7. 主题 D · 青绿金碧（参考图：古绢 + 宝石蓝 + 石绿 + 金泥）

### 7.1 视觉锚点
- 参考图：`Traditional_Chinese_blue_green_2026-09-01T13-40-09.png`
- 主调：**古绢黄底 + 蓝绿双色山体 + 金线包浆**。
- 关键色彩：
  - 底色：`--bg-page: #C9B58A`（古绢）
  - 卡片渐变：`linear-gradient(180deg, #D4BF92 0%, #B89A6B 100%)`
  - 文本：`#2C2418`（深褐墨）
  - 强调蓝：`#2E5C8A`（主按钮 / 选中态）
  - 强调绿：`#4F8762`（资料标签）
  - 强调金：`#B89048`（顶部金线 / 控制台徽章）
  - 反白：`#F8F0DC`（按钮文字）

### 7.2 文件 / 行号引用
| 项 | preview.html | tuner.html |
| --- | --- | --- |
| token 声明 | `:303` | `:443` |
| ink-bg 图片 | `:497` (compare) | `:77`（`center 45% / cover`） |
| ink-veil 暖金覆盖 | `:331-333` 暗金色 0.10/0.40/0.55 三段 | `:103` |
| 顶栏双下边框 | `:338-340` `::before { linear-gradient(90deg, transparent, #B89048 30%, #B89048 70%, transparent) }` | `:475-478` |
| 品牌前缀短线（金泥色） | `:354` `brand::before { background:#B89048 }` | `:174` |
| 用户气泡（宝石蓝） | `:341-342` `border:1.5px solid #2E5C8A` | — |
| 主控气泡（金泥色描边） | `:343-344` | — |
| 资料标签 | `:351` `ap-tag { background:rgba(46,92,138,.18); color:#2E5C8A }` | — |
| 主按钮渐变 | `:347` `.btn.primary { background:#2E5C8A; color:#F8F0DC }` | `:482` `.btn.gold` 改为 `linear-gradient(135deg, #B89048, #8E6C30)` |
| 控制台徽章 | `:350` `border-color:#B89048` | `:485` `color:#4A3820; border-color:#B89048; background:rgba(184,144,72,.18)` |
| 阴影 | `--shadow-mockup: 0 22px 60px rgba(82,56,18,.32)` | 同 |

### 7.3 关键调整
- **顶栏 + sidebar 双下边框**：第一条 0.5 px 常规 + 第二条 1 px 金泥渐变，整体厚度明显高于 A/B/C（视觉上模拟古画装裱外框）。
- **字体走楷体 STKaiti**（与 B 同源），但 brand 字距 0.36em（介于 A 与 B 之间）。
- **多色体系**：蓝 / 绿 / 金三色并存，靠 `accent` / `accent-secondary` / 金泥细节分配职责。
- **三段金水遮罩**：ink-veil 加入底部暖金渐隐，让字上方的山仍可读。

---

## 8. 通用 UI 组件 — 改动一览

### 8.1 主题切换 tab
- `preview.html` 由 3 tab 扩到 **4 + compare**；`tuner.html` 同步 **4 个主题 tab**。
- 切到任一主题时，只更动 `body[data-theme="X"]` 的属性；CSS 变量统一接管所有 UI 颜色。
- 高亮态：从「黑底白字」改为「token accent 背景 + accent-on 文字 + 月光 / 金泥阴影」。

### 8.2 导航栏（顶栏 .topbar）
| 项目 | 调整点 |
| --- | --- |
| 品牌 logo | letter-spacing 由全量统一改为按主题差异化（A 0.24em / B 0.42em / C 0.18em / D 0.36em） |
| `brand::before` | 仅 B / D 显示前缀短线，B 黑色、D 金泥色 |
| 顶栏底边 | C 加月光金线、D 加双下边框（金 + 深褐墨） |
| 顶栏背景 | 全部统一走 `var(--topbar-bg)` + `backdrop-filter: blur(18px)` |

### 8.3 卡片（panel card）
- 全部走 `var(--surface)` 背景 + `var(--border)` 描边 + `var(--shadow-col)` 阴影。
- `tuner.html` 各 card 阴影按主题变深（A 蓝、B 淡、C 重、D 暖金）。

### 8.4 按钮（.btn / .btn.primary / .btn.gold）
- 次要按钮边框：`var(--border-strong)`，hover 切到 `var(--accent)`。
- 主要按钮：背景 `var(--accent)`，文字 `var(--accent-on)`。
- `tuner.html` 的 `.btn.gold` 在 D 主题改为「金泥 + 深金线性渐变」，与 B 主题的「纯黑渐变」拉开。

### 8.5 背景（页面 / mockup）
- 页面背景：A 渐变 `#DDE9F0→#C5DBE8`、B 宣纸 `#ECE6D6→#E0DAC9`、C 夜墨 `#0A1424→#050B11`、D 古绢 `#D4BF92→#B89A6B`。
- `tuner.html` 的 `.stage` 多套主题下，底图（`ink-photo`）+ 暖色遮罩（`ink-veil`）+ 双墨滴（`ink-blob-1/2`）+ 宣纸纹理（`paper-grain`）四层叠加，与图片风格严格对齐。

### 8.6 文字层级（color、size、spacing）
- 一级标题 (`h1`)：20-22 px，字距 0.06em，字体走 `var(--font-serif-title)`。
- 副标题 (`subtitle`)：12-13 px，`var(--text-muted)` 颜色。
- 角色标签 `.bubble .role`：9 px，`var(--font-serif-title)` 楷体，A/C/D 三主题显示。
- 章节名 `.card h2 / .sess-head / .assets-head / .sb-head`：字距按主题差异化（B/D 撑到 0.28-0.30em 显古意）。

### 8.7 圆角（按主题差异化）
| 主题 | mockup/card | col | topbar |
| --- | --- | --- | --- |
| A 柔雾 | 20 px | — | — |
| B 水墨 | **14 px（最紧）** | 10 px | 8 px |
| C 暗墨 | **22 px（最柔）** | 18 px | 18 px |
| D 金碧 | 18 px | 14 px | 10 px |

### 8.8 阴影（按主题差异化）
| 主题 | shadow-tabs | shadow-on | shadow-mockup |
| --- | --- | --- | --- |
| A | 淡蓝 | 淡蓝 | 0 16px 48px 蓝 |
| B | 淡米褐 | 纯黑 | 0 20px 56px 米褐 |
| C | 浓黑 + 月光 | 月光晕 **0 4px 20px 月光** | **0 28px 64px 黑 + 0 0 80px 月光** |
| D | 暖金 | 蓝宝石 | 0 22px 60px 暖金 |

### 8.9 响应式
- `preview.html`：`.grid` 在 `1640 / 720` 双断点退化，`A/B/C/D` 并排到 720 时单列。
- `tuner.html`：`main` `flex-direction: column` 在 `1180px` 切换，控制面板下移。
- 已测试：在 1920×1080 屏上 A 单 stage 与四主题并排 stage 均可容纳。

---

## 9. 同步与状态保留

- `preview.html` 切换状态：`sessionStorage['lj_preview_v11']` 键存 `{mode, theme}`。
- `tuner.html` 切换状态：`sessionStorage['lj_tuner_theme_v11']` 存主题，`'lj_kb_mode'` 存知识库模式（沿用 v10 旧键，不影响其他模块）。
- 主题切换的"持久化键"全部带 `_v11` 后缀，与原 `lj_preview` / `lj_tuner_theme` 隔开，避免旧版本残留导致首次进入页面选错主题。

---

## 10. 已知边界 / 未覆盖项

1. **图片缺失差异**：参考图分辨率固定为 1528×800 上下，preview 的 720 px 高度 mockup 下图会被裁切。已通过 `object-position` 控制 A 偏 42%、B 右下、C 30%、D 45%，但极端窄屏（< 480 px）下图片景深不完美。这是素材本身的限制，不是 CSS 缺陷。
2. **楷体回退**：用户系统若无 STKaiti，会回落到 KaiTi / 楷体，最终回落到 PingFang。B / D 主题因字体退化，"楷体气质"会打折扣。
3. **C 主题可读性**：因 `#E8E2C8` 在 `#050B11` 上对比度 15.6:1（远超 AAA），视觉阅读很清晰；但**正文长度的小字号辅助文字**仍建议保留 fade，避免阻碍"夜空静谧感"。
4. **D 主题金线**：金泥渐变线依赖 `linear-gradient` 模拟，工程上未引入图形包浆纹理；如需更"装裱框"质感，可加 SVG 噪点。
5. **跨页面 tab 状态未联动**：preview 与 tuner 是独立页，未做双向 tab 同步（如在 preview 切换 D 后跳到 tuner 自动落 D）；当前用 `sessionStorage` 隔离两套键。如需联动可加 `storage` 事件订阅。
6. **未覆盖项**：响应式仅做到 720 px 以下单列，未对折叠屏 / 横竖屏切换做精细调优。

---

## 11. 一图回顾 · 主题索引

```
theme=preview?tuner:
  A  柔雾青绿  → Soft_misty_Chinese_blue_green_*.png
                  主 #DDE9F0  强 #4A8BAB
  B  水墨留白  → Traditional_Chinese_ink_wash_l_*.png
                  主 #ECE6D6  强 #2C2820  (楷体)
  C  暗墨夜山  → Chinese_ink_painting_of_toweri_*.png
                  主 #050B11  强 #F2EBD0  (月光 + 钤印)
  D  青绿金碧  → Traditional_Chinese_blue_green_*.png
                  主 #C9B58A  强 #2E5C8A #4F8762 #B89048
```

---

*变更版本：v11 · 四主题切换 · 严格按 4 张参考图还原 · design tokens 统一管理 · backend hooks: `api.uploadKnowledge` / `api.searchKnowledge(mode)` → `tuner.html`*
