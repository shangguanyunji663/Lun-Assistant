# 论匠前端 · 第十一轮修改 · B 主题由「水墨留白」翻转为「黑白瑞士」

> 文档域：frontend-versions
> 文档类型：轮次记录
> 主题版本：v12
> 轮次：ROUND11
> 日期：2026-09-02
> 状态：已落地

> 背景触发：v11 四主题切换落地后，B 宣纸米 `#ECE6D6` 与 D 古绢黄 `#C9B58A` 同属暖色域、明度差仅 ~10%，切换时视觉区分度不足。本轮把 B 主题整体重做为 **E2 黑线瑞士**（Swiss Black Outline）方案，与 D 形成「冷 vs 暖 × 黑 vs 金」双重对比，区分度从约 1.5 档跃至 7 档。

---

## 一、本轮改进总览

| 项 | 改造前（B 水墨留白） | 改造后（B 黑白瑞士） |
|---|---|---|
| 主色 | 宣纸米 `#ECE6D6` | 纯白 `#FFFFFF` |
| 文字 | 墨黑 `#2C2820` | 纯黑 `#000000` |
| 强调 | 墨黑单色 | **纯黑单色 + 反白** |
| 描边 | 半透明暖墨 `rgba(60,56,42,0.12)` | **1.5px 实线黑 `#000000`** |
| 圆角 | 14 px（mockup）/ 10 px（col）/ 8 px（topbar） | **0（直角）** |
| 字体 | STKaiti 楷体主导 | **Helvetica Neue / Arial / PingFang SC** |
| 字距（brand） | 0.46em（楷体宽字距） | 0.16em（瑞士紧凑） |
| 背景图 | `bg-b-inkwash.webp`（右下 60%） | **none（黑线瑞士无装饰图）** |
| 卷轴木轴 | 宣纸纹理灰（28,28,26,.12~.30） | **9px 纯黑实线** |
| 中缝线 | 可见（`.ink-divider` opacity:1） | **隐藏（opacity:0）** |
| 纸纹 mix-blend | multiply | overlay + opacity 0.015 |
| tab 激活态 | 墨黑半透明 + 1px 墨黑边 | **纯黑底白字 + 1.5px 黑边** |
| 与 D 区分度 | ~1.5 档（同暖色域） | **~7 档（冷暖 × 黑金双对比）** |

---

## 二、本轮修改涉及的前端模块 / 文件

| 模块 | 文件 | 行号 |
|---|---|---|
| B 主题主 token 块 | `frontend/src/styles.css` | :115–180（重写） |
| B `.ink-divider` 中缝 | `frontend/src/styles.css` | :351 |
| B `.paper-grain` 纸纹 | `frontend/src/styles.css` | :415 |
| B `.theme-tabs button.on` | `frontend/src/styles.css` | :715–718 |
| THEMES 元数据 | `frontend/src/App.jsx` | :119 |
| 设计稿 token + mockup-b | `design-concepts/preview.html` | :203–247 / :380 / :398 / :451 / :624 / :748 / :814 |
| 设计稿 token + stage + THEME_META | `design-concepts/tuner.html` | :69 / :89 / :119–120 / :127 / :170 / :173 / :380–408 / :492 / :498 / :683 / :690 |
| 工程变更文档 | `design-concepts/CHANGELOG-v12.md` | 新建 |
| 文档导航表 | `README.md` | :14–23 |

---

## 三、具体改动要点

### 3.1 主 token 块（styles.css :115–180）— 整体重写

关键改动（17 个 token）：
- `--bg-deep / panel / raise`：`#ECE6D6 / #F2EEE1 / #F8F5EA` → `#FFFFFF / #FFFFFF / #F5F5F5`
- `--ink-hi / mid / low`：`#2C2820 / #4A4842 / #6E6B62` → `#000000 / #333333 / #6B6B6B`
- `--jade / jade-deep / pine`：墨黑系 → `#000000 / #000000 / #1A1A1A`
- `--gold / gold-hi`：`#2C2820 / #1F1F1C` → `#000000 / #1A1A1A`
- `--seal`：`#A3382B`（枣红） → `#000000`（黑线瑞士不用红钤印）
- `--line / line-mid / line-hi / line-gold / line-jade`：`rgba(60,56,42, 0.12~0.34)` → `#000000`（半透明改实色）
- `--font-kai / song / body`：STKaiti 楷体 → **Helvetica Neue / Helvetica / Arial / PingFang SC**
- `--bg-rgb / bg-panel-rgb / bg-raise-rgb`：`236,230,214 / 242,238,225 / 248,245,234` → `255,255,255 / 255,255,255 / 245,245,245`
- `--ink-bg-url`：`url('/bg/bg-b-inkwash.webp')` → **`none`**（黑线瑞士无背景图）
- `--wood-top / mid / bot`：`rgba(28,28,26, .12/.22/.30)` → **`#000000 / #000000 / #000000`**（9px 纯黑实线卷轴）
- `--ink-veil-top / mid / bot`：`0.12 / 0.30 / 0.62` → **`0 / 0 / 0`**（无遮罩）

> 备注：1.5px 黑实线统一靠 `--line: #000000` 接管，无需逐处改 border 宽度——所有用 `var(--line)` 的组件自动获得实色硬边。

### 3.2 B 装饰修饰符

| 选择器 | 旧值 | 新值 | 说明 |
|---|---|---|---|
| `body[data-theme="b"] .ink-divider` | `opacity: 1` | `opacity: 0` | E2 黑线瑞士无中缝 |
| `body[data-theme="b"] .paper-grain` | `mix-blend-mode: multiply` | `overlay; opacity: 0.015` | 减弱纸纹不破坏纯白 |
| `body[data-theme="b"] .theme-tabs button.on` | 半透明墨黑 + 1px 墨边 | **`#000` 底白字 + 1.5px 黑边** | 瑞士单色主导 |

### 3.3 App.jsx THEMES 元数据（:119）

```jsx
{ id: 'b', label: '黑白瑞士', chip: '#000000' },
```
- `label: '水墨留白' → '黑白瑞士'`
- `chip: '#ECE6D6' → '#000000'`：主题切换 tab 上的小色块由米色改为纯黑，与其他三主题（A 青蓝 / C 墨夜 / D 古绢黄）形成明显对比。

### 3.4 设计稿 preview.html（4 处同步）

- **token 块 :203–247**：整体重写为黑线瑞士（同 styles.css 17 token），但走 preview 自己的变量集（`--bg-page / --bg-card / --surface / --border / --shadow-mockup / --radius-card / --font-serif` 等 22 个）。
- **.mockup-b 子样式**：隐藏 `.ink-bg`、移除 `::before` 中缝短线、`.bubble` 改直角 + 1.5px 黑边、`.kb-switcher button.on` 改黑底白字、`.kb-pill .dot` 改纯黑。
- **tab button :380**：title 改「黑白瑞士（黑线瑞士 · ROUND11）」、chip 改 `linear-gradient(135deg,#FFFFFF,#000000)`。
- **legend :398**：B 色块改 `#FFFFFF` + `#000` border + 名「B · 黑白瑞士」。
- **mockup-b 标签 :451 / :624**：注释 + label 改「B · 黑白瑞士」，移除 img 引用（黑线瑞士无背景图）。
- **compare 列名 :748**：「B · 水墨」→「B · 黑白瑞士」。
- **footer :814**：「v11 四主题」→「v11 → ROUND11 · B 由水墨留白翻转为黑白瑞士」。

### 3.5 设计稿 tuner.html（10 处同步）

- **.ink-photo :69–72**：`display: none`（黑线瑞士无背景图）。
- **.ink-veil :89–94**：`background: transparent`（无遮罩）。
- **.ink-blob-1/2 :119–120**：`display: none`（无墨晕）。
- **.paper-grain :127**：`overlay + opacity 0.015`（极淡纤维感）。
- **.ink-divider :142**：`opacity: 0`（无中缝）。
- **.brand :170**：字距 `0.46em → 0.16em`（瑞士紧凑）。
- **.brand::before :173**：`display: none`（隐藏楷体装饰线）。
- **B 主题 token 块 :380–408**：整体重写为黑线瑞士（preview 同样的 22 token + 3 radius 全 0）。
- **tab button :498**：title 改「B 黑白瑞士 · Swiss Black Outline（ROUND11）」。
- **footer :683 / THEME_META :690**：「B 水墨留白」→「B 黑白瑞士」+ bg/img RGB 改 `255,255,255` + text 改 `0,0,0` + 6 个预设值统一调零。

### 3.6 InkBackground.jsx — **无需改动**

`InkBackground.jsx:43–44` 的 `.ink-divider` 与 `.ink-stamp` 通过 styles.css 的 `body[data-theme="b"]` 选择器控制可见性，A/B 主题天然不显示 stamp（`opacity: 0` 默认）。本轮只在 CSS 层加 `body[data-theme="b"] .ink-divider { opacity: 0 }` 即可关闭 B 主题的中缝，组件本身无需修改。

---

## 四、与之前几轮修改的关系

| 轮次 | 关系 |
|---|---|
| ROUND5 | 文墨山水浅黛美化（首次引入楷体字距美学） |
| ROUND7 | v9 青绿长卷·放松版（首次建立 design token 体系） |
| ROUND8 | v10 三主题切换（preview/tuner 设计稿落地） |
| ROUND9 | v10 主题图 WebP 压缩 + 部署（资产优化） |
| ROUND10 | v10 三主题遗留项落地（L-2 gitignore / L-3 内置 / L-4 装饰 / L-5 grain / L-6 移动端 / L-7 音效 / L-8 截图） |
| **ROUND11（本轮）** | **B 主题翻转为黑白瑞士 — 修复 B↔D 区分度不足问题（属修复 + 迭代优化）** |

> 本轮属「**修复**」（修复 v11 B↔D 暖色域区分度不足的设计缺陷）兼「**迭代优化**」（沿用 v11 的 token 体系框架，仅替换 B 一套主题）。属于局部主题替换，不影响 a/c/d 三主题的任何行为与样式。

---

## 五、视觉验证要点

1. **与 D 区分度**：
   - B 底色 `#FFFFFF`（亮度 255）vs D 底色 `#C9B58A`（亮度约 188），明度差 67。
   - B 文字 `#000`（亮度 0）vs D 文字 `#2C2418`（亮度约 56），黑金对比一眼可辨。
   - B 字距 0.16em / Helvetica vs D 字距 0.36em / 楷体，字体本身拉开档次。
2. **黑线瑞士的"硬"**：
   - 所有容器 border 1.5px 实线黑，硬边硬角。
   - tab 激活态 / 按钮主色 / brand 短线——三处全黑实心块。
3. **黑线瑞士的"简"**：
   - 无背景图、无遮罩、无墨晕、无中缝、无楷体装饰线、无 paper grain 强纹理。
   - 仅保留 `.paper-grain` opacity 0.015 作为极淡纤维感（不破坏纯白）。

---

## 六、向后兼容

- 旧 `bg-b-inkwash.webp`（`frontend/public/bg/bg-b-inkwash.webp`）本轮**不再被引用**，但保留文件不删除（用户可手动清理或在 ROUND12 阶段统一清理 v8/v9/v10 主题遗留资产）。
- `localStorage.lj_theme='b'` 的旧用户：自动获得新 B 主题（黑线瑞士），无需任何迁移操作。
- 跨页签联动 `storage` 事件逻辑未变（A/B/C/D 四主题仍同步）。
- 主题切换音效未变（A/C/D 三角主题音色不变，B 由"卷轴木轴咔哒"改为同一音色——音效与卷轴视觉脱钩）。

---

## 七、已知边界 / 未覆盖项

1. **楷体完全弃用**：原 B 主题楷体气质（STKaiti）的所有视觉痕迹（brand 0.42em 字距 / ::before 装饰线 / topbar 字距 / bubble 楷体 fallback）已全部清除。如果未来想恢复"中式排版气质"，需要重新设计 D 之外的中式主题。
2. **黑线瑞士无 hover 装饰**：所有 hover 仅靠 `--bg-raise: #F5F5F5`（极淡灰）切换，没有 v9 的青绿微光、v10 的木轴咔哒那种反馈感。如果用户希望保留"精致交互"，可在 ROUND12 给 E2 增加 1px 黑边 → 2px 黑边的 transition 反馈。
3. **卷轴木轴变成"两条黑横线"**：原 B 主题木轴是宣纸纹理（28,28,26,.12~.30 半透明），E2 是 9px 纯黑实线 + `box-shadow: 0 2px 10px rgba(0,0,0,.35)` 阴影。在 1440×900 屏上看起来是"上下两条粗黑条"，与黑线瑞士风格一致，但与"卷轴"语义已完全脱钩——可考虑在 ROUND12 移除整个 `.wood-roll` 组件。
4. **tuner.html B 主题 stage 默认隐藏**：因为 `bg-b-inkwash.webp` 已被 `.ink-photo { display: none }` 隐藏，所以 tuner 切换到 B 时 stage 看起来"空"。这是黑线瑞士的应有效果（瑞士设计不要装饰图），但用户首次切到 B 可能会感到"少了一层"。可在 ROUND12 给 tuner 的 stage 加占位提示文案。
5. **移动端未单独验证**：B 主题直角 + 1.5px 黑边在窄屏（<720px）下按钮可点击面积仍 ≥44px（圆角 0 但 padding 充足），理论上无回归，但实测需在 ROUND12 阶段用 360px 模拟器跑一遍。
6. **跨页面 tab 同步未变**：preview 与 tuner 仍是独立页，theme 不联动。如需联动可加 `storage` 事件订阅（v11 已记为已知边界）。

---

## 八、追溯 / 关联文档

- v11 设计稿全景：[`CHANGELOG-v11-design.md`](./CHANGELOG-v11-design.md)
- v11 生产侧改造：[`CHANGELOG-v11-frontend.md`](./CHANGELOG-v11-frontend.md)
- 本轮工程变更：[`CHANGELOG-v12.md`](./CHANGELOG-v12.md)
- 前端 token 体系起点：[`OPTIMIZATION_ROUND7.md`](./OPTIMIZATION_ROUND7.md)（v9 青绿长卷）
- 三主题切换设计：[`OPTIMIZATION_ROUND8.md`](./OPTIMIZATION_ROUND8.md)（v10 → 主应用生产代码落地 §18）
- v10 主题图压缩与部署：[`OPTIMIZATION_ROUND9.md`](./OPTIMIZATION_ROUND9.md)
- v10 遗留项落地 L-2~L-8：[`OPTIMIZATION_ROUND10.md`](./OPTIMIZATION_ROUND10.md)
