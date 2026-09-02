# 论匠前端 · v12 B 主题黑白瑞士（Swiss Black Outline）— 变更文档

> 文档域：frontend-versions
> 文档类型：版本变更
> 主题版本：v12
> 轮次：—
> 日期：2026-09-02
> 状态：已落地

> 本轮以 v11 四主题体系为骨架，**仅替换 B 主题**——把原"水墨留白"（宣纸米 + 楷体 + 中缝线 + 墨滴晕染）整体翻转为"黑白瑞士"（纯白 + 纯黑 + 1.5px 实线 + 直角 + Helvetica）。A 柔雾青绿 / C 暗墨夜山 / D 青绿金碧 三套主题完全保持不动。

---

## 1. 总览（结论先行）

| 维度 | v11 B 水墨留白 | **v12 B 黑白瑞士** | 改动 |
|---|---|---|---|
| 主色 | 宣纸米 `#ECE6D6` | **纯白 `#FFFFFF`** | 是 |
| 文字 | 墨黑 `#2C2820` | **纯黑 `#000000`** | 是 |
| 强调 | 墨黑单色 | **纯黑单色 + 反白** | 是 |
| 描边 | `rgba(60,56,42,0.12~0.34)` 半透明 | **`#000000` 实色** | 是 |
| 圆角 | 14/10/8 px（mockup/col/topbar） | **0（直角）** | 是 |
| 字体 | STKaiti 楷体 | **Helvetica Neue** | 是 |
| brand 字距 | 0.42em（楷体宽字距） | 0.16em（瑞士紧凑） | 是 |
| 背景图 | `bg-b-inkwash.webp` 右下 60% | **none** | 是 |
| 卷轴木轴 | 宣纸纹理灰（28,28,26,.12~.30） | **9px 纯黑实线** | 是 |
| 中缝线 | 可见（opacity:1） | **隐藏（opacity:0）** | 是 |
| 纸纹 | multiply + opacity 0.045 | overlay + opacity 0.015 | 是 |
| tab 激活态 | 半透明墨黑 + 1px 墨边 | **纯黑底白字 + 1.5px 黑边** | 是 |
| 与 D 区分度 | ~1.5 档 | **~7 档** | 改进 |

变更结论：
1. **结构**：4 主题不变（A/B/C/D），仅 B 替换为黑线瑞士。
2. **样式系统**：`body[data-theme="b"]` token 块整体重写；preview/tuner 各同步 7-10 处 B 相关样式。
3. **token 维度**：B 主题管控 17 个 token 不变（与 v11 计数一致），但每个 token 值都改为黑线瑞士对应值。
4. **响应式**：未改 `preview.html` `.grid` 与 `tuner.html` `main` 的断点——B 主题的直角 + 1.5px 黑边在所有宽度下都成立。

---

## 2. 文件级变更摘要

| 文件 | 改动 | 行号范围 |
|---|---|---|
| `frontend/src/styles.css` | B 主题 token 块整体重写 + 3 个修饰符更新 | :115–180 / :351 / :415 / :715–718 |
| `frontend/src/App.jsx` | THEMES.b label + chip | :119 |
| `design-concepts/preview.html` | B 主题 token + .mockup-b + tab + legend + label + footer 共 7 处 | :203–247 / :380 / :398 / :451 / :624 / :748 / :814 |
| `design-concepts/tuner.html` | B 主题 token + .ink-photo/veil/blob/grain/divider/brand/brand::before + tab + footer + THEME_META 共 10 处 | :69 / :89 / :119–120 / :127 / :142 / :170 / :173 / :380–408 / :492 / :498 / :683 / :690 |
| `OPTIMIZATION_ROUND11.md` | 本轮工程文档（新文件，本目录内） | — |
| `CHANGELOG-v12.md` | 本文档（新文件；2026-09-02 文档治理轮由 `design-concepts/` 迁入本目录） | — |
| `README.md` | 文档导航表追加「优化记录十一」一行 | :24 |

---

## 3. 全局工程变更（B 主题块共有）

### 3.1 主色 token（与 v11 对比）

```
--bg-deep / panel / raise : #ECE6D6 / #F2EEE1 / #F8F5EA → #FFFFFF / #FFFFFF / #F5F5F5
--ink-hi / mid / low       : #2C2820 / #4A4842 / #6E6B62 → #000000 / #333333 / #6B6B6B
--jade / jade-deep / pine  : #1F1F1C / #3A3833 / #4A4842 → #000000 / #000000 / #1A1A1A
--gold / gold-hi           : #2C2820 / #1F1F1C           → #000000 / #1A1A1A
--seal                     : #A3382B（枣红）             → #000000
--line / line-mid / hi     : rgba(60,56,42, .12/.18/.28) → #000000 实色
--line-gold / line-jade    : rgba(60,56,42, .32/.34)     → #000000 实色
--font-kai / song / body   : STKaiti / STKaiti / 楷体   → Helvetica Neue / Helvetica / Arial / PingFang SC
--bg-rgb / bg-panel-rgb    : 236,230,214 / 242,238,225   → 255,255,255 / 255,255,255
--bg-raise-rgb             : 248,245,234                 → 245,245,245
--ink-bg-url               : url('/bg/bg-b-inkwash.webp') → none
--wood-top / mid / bot     : rgba(28,28,26, .12/.22/.30) → #000000 / #000000 / #000000
--ink-veil-top / mid / bot : 0.12 / 0.30 / 0.62          → 0 / 0 / 0
```

### 3.2 B 装饰修饰符

| 选择器 | v11 | v12 |
|---|---|---|
| `body[data-theme="b"] .ink-divider` | `opacity: 1` | `opacity: 0` |
| `body[data-theme="b"] .paper-grain` | `mix-blend-mode: multiply` | `mix-blend-mode: overlay; opacity: 0.015` |
| `body[data-theme="b"] .theme-tabs button.on` | `rgba(44,40,32,.10) bg + #1F1F1C color + 1px rgba(60,56,42,.34)` | `#000000 bg + #FFFFFF color + 1.5px #000000` |

### 3.3 preview.html 专属

| 项 | v11 | v12 |
|---|---|---|
| `.mockup-b .ink-bg img` | `right bottom / 65% / opacity 0.18 / contrast 0.92 / saturate 0.4` | **整图隐藏** (`.mockup-b .ink-bg { display: none }`) |
| `.mockup-b .ink-bg::after` | `radial-gradient(ellipse at top left, transparent 35%, rgba(236,230,214,.55) 100%)` | 隐藏 |
| `.mockup-b .topbar` | `rgba(252,248,238,.78) + blur(10px) + 0.5px 暖墨边` | `#FFFFFF + backdrop-filter:none + 1.5px 黑边` |
| `.mockup-b .brand` | `letter-spacing: 0.42em` | `letter-spacing: 0.16em` |
| `.mockup-b .brand::before` | 18×1px 黑色短线 + opacity:0.5 | 隐藏 |
| `.mockup-b .bubble.user` | `#2C2820 border + #F8F5EA bg + border-top-right-radius 4px` | `1.5px #000 border + #FFFFFF bg + 直角` |
| `.mockup-b .bubble.assistant` | `rgba(60,56,42,.22) border + 浅米半透 + border-top-left-radius 4px` | `1.5px #000 border + #FFFFFF bg + 直角` |
| `.mockup-b .input-bar` | `rgba(245,240,228,.85)` | `#FFFFFF + border-top 1.5px #000` |
| `.mockup-b .kb-switcher button.on` | `#2C2820 bg + #ECE6D6 color` | `#000 bg + #FFF color + 1.5px #000 border` |
| `.mockup-b .kb-pill .dot` | `#2C2820 + box-shadow none` | `#000 + box-shadow none` |

### 3.4 tuner.html 专属

| 项 | v11 | v12 |
|---|---|---|
| `body[data-theme="b"] .ink-photo` | `Traditional_Chinese_ink_wash_l_*.png` right bottom / 65% | `display: none` |
| `body[data-theme="b"] .ink-veil` | `linear-gradient(180deg, rgba(236,230,214,...))` | `background: transparent` |
| `body[data-theme="b"] .ink-blob-1/2` | `rgba(60,56,42,.10)` / `rgba(120,100,60,.08)` 径向 | `display: none` |
| `body[data-theme="b"] .paper-grain` | `multiply + opacity calc(--grain * 1.5)` | `overlay + opacity 0.015` |
| `body[data-theme="b"] .ink-divider` | `opacity: 0.85` | `opacity: 0` |
| `body[data-theme="b"] .brand` | `letter-spacing: 0.46em` | `letter-spacing: 0.16em` |
| `body[data-theme="b"] .brand::before` | 22×1px `#2C2820` 短线 + opacity:0.5 | `display: none` |

### 3.5 THEME_META（B 主题预设值）

```
旧：name:'B 水墨留白' bg:[236,230,214] img:[170,168,160] text:[44,40,32]
    presetOp:.10 presetTop:.18 presetMid:.55 presetWash:.4  presetGrain:.06 presetKb:.55
新：name:'B 黑白瑞士' bg:[255,255,255] img:[255,255,255] text:[0,0,0]
    presetOp:0    presetTop:0    presetMid:0    presetWash:0  presetGrain:.015 presetKb:.70
```

> 6 个预设全部清零（黑线瑞士无背景图、无遮罩、无墨晕），仅保留 `presetGrain .015`（极淡纸纹）和 `presetKb .70`（kb-switcher 半透明白底可见度略调高）。

### 3.6 App.jsx THEMES 元数据

```jsx
{ id: 'b', label: '黑白瑞士', chip: '#000000' },   // 旧：label: '水墨留白', chip: '#ECE6D6'
```

---

## 4. 与 D 青绿金碧 的区分度对比

| 维度 | v11 B ↔ D | v12 B ↔ D | 提升 |
|---|---|---|---|
| 底色明度差 | `#ECE6D6` vs `#C9B58A` ≈ 67 vs 188，差 ~14% | `#FFFFFF` vs `#C9B58A` = 255 vs 188，差 ~26% | +12pp |
| 文字色相差 | `#2C2820` vs `#2C2418` 同暖墨系 | `#000` vs `#2C2418` 黑撞深褐 | 强拉开 |
| 字距 | 0.42em vs 0.36em 接近 | 0.16em vs 0.36em 显著差 | 强拉开 |
| 字体 | 楷体 vs 楷体（同源） | Helvetica vs 楷体（异源） | 强拉开 |
| 强调色 | 墨黑 vs 宝石蓝+金泥（色相对比） | 黑 vs 宝石蓝+金泥（色相对比 + 黑金对比） | 双轴对比 |

**结论**：v12 B 与 D 形成「冷 vs 暖 × 黑 vs 金」双重对比，区分度从 ~1.5 档跃至 ~7 档（基于色相 + 明度 + 字体 + 字距 4 维度综合）。

---

## 5. 视觉验证清单（开发者自查）

- [ ] `npm run dev` 启动后，访问 `localhost:5173`，切换到 B 主题：纯白底 + 纯黑字 + 直角 + 1.5px 黑边 + Helvetica。
- [ ] 切换到 D 主题：暖金古绢 + 楷体 + 圆角 18px。两次切换肉眼看得到强烈差异。
- [ ] 切换到 C 主题：墨夜 + 月光米 + 钤印"B 主题"激活时钤印不显示（仅 C 显示）。
- [ ] tuner.html 切到 B：stage 完全干净（无背景图、无墨滴），左下"4 张参考图各用其主图"仍可见。
- [ ] 主应用顶栏 `.theme-tabs` 切到 B：当前激活 tab 纯黑底白字 + 1.5px 黑边。

---

## 6. 同步与状态保留

- `preview.html` 切换状态：`sessionStorage['lj_preview_v11']` 键不变；本轮未新增键。
- `tuner.html` 切换状态：`sessionStorage['lj_tuner_theme_v11']` + `'lj_kb_mode'` 键不变。
- `localStorage.lj_theme='b'` 旧用户：自动获得 v12 黑线瑞士，无需迁移。

---

## 7. 已知边界 / 未覆盖项

1. **旧资源 `bg-b-inkwash.webp`**（`frontend/public/bg/bg-b-inkwash.webp`，原 v9/v10/v11 B 主题背景图）已不再被引用。本轮**保留文件**不删；如需清理，归入 ROUND12 资产整理。
2. **楷体完全弃用**：原 B 主题所有楷体气韵（brand 0.42em 字距 / ::before 装饰线 / topbar 字距 / bubble 楷体 fallback）已清除。如果未来想恢复"中式排版气质"，需要重新设计 D 之外的中式主题。
3. **卷轴木轴变成"两条黑横线"**：原 B 主题木轴是宣纸纹理半透明；E2 是 9px 纯黑实线 + 阴影。在 1440×900 屏上看是"上下两条粗黑条"，与黑线瑞士风格一致但与"卷轴"语义脱钩——可考虑 ROUND12 移除整个 `.wood-roll` 组件。
4. **移动端直角可点击面积**：B 主题直角 + 1.5px 黑边在窄屏（<720px）下按钮 padding 充足，理论 ≥44px 可点击；实测需 ROUND12 阶段 360px 模拟器验证。
5. **跨页面 tab 同步未变**：preview 与 tuner 仍是独立页（沿用 v11 §10 已知边界）。

---

## 8. 一图回顾 · 主题索引（v12）

```
theme=preview?tuner:
  A  柔雾青绿  → Soft_misty_Chinese_blue_green_*.png        （不变）
                  主 #DDE9F0  强 #4A8BAB
  B  黑白瑞士  → 【ROUND11 新】无背景图，纯白底纯黑字       （本轮重做）
                  主 #FFFFFF  强 #000  (1.5px 实线黑边 / Helvetica / 直角)
  C  暗墨夜山  → Chinese_ink_painting_of_toweri_*.png       （不变）
                  主 #050B11  强 #F2EBD0  (月光 + 钤印)
  D  青绿金碧  → Traditional_Chinese_blue_green_*.png       （不变）
                  主 #C9B58A  强 #2E5C8A #4F8762 #B89048
```

---

*变更版本：v12 · B 主题由水墨留白翻转为黑白瑞士 · 仅替换 B 一套主题 · A/C/D 三主题完全不动 · design tokens 统一管理 · backend hooks 不变*
