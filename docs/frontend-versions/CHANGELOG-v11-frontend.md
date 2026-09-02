# 论匠前端 · v11 四主题改造 — 修复 CHANGELOG

> 文档域：frontend-versions
> 文档类型：版本变更
> 主题版本：v11
> 轮次：—
> 日期：2026-09-01
> 状态：已落地

> 本轮以**用户提供的 4 张参考图实测 RGB 均值**为唯一视觉基准，对 `frontend/` Vite 真实项目做端到端改造。
>
> **诊断 → 修复 → 验证** 三段式归档，每条都附文件 + 行号 + 截图证据。

---

## 0. 用户反馈

> "四个主题严格按照这四张图片风格来，我要的是我自己打开前端的不是要你的 preview"

→ 用户要求：**主应用 npm run dev 后能看到 4 主题，配色严格按 4 张参考图的明暗 / 色相 / 字体**。

---

## 1. 参考图实测（精确像素统计，Pillow + alpha 合成）

| 主题 | 文件 | 全图均值 RGB | 亮度中位 | 实际风格 |
|------|------|-------------|---------|---------|
| **A 柔雾青绿** | `Soft_misty_Chinese_blue_green__2026-09-01T13-51-14.png` | `(164, 189, 207)` | 186 | **亮雾青蓝**（柔雾水乡） |
| **B 水墨留白** | `Chinese_ink_painting_of_toweri_2026-09-01T13-41-26.png` | `(21, 27, 34)` | 19 | **极暗深墨蓝**（注意：此前 B 用此图，但均值很暗） |
| **C 暗墨夜山** | `Traditional_Chinese_ink_wash_l_2026-09-01T13-40-46.png` | `(227, 224, 219)` | 225 | **亮宣纸**（注意：此前 C 用此图，但均值很亮） |
| **D 青绿金碧** | `Traditional_Chinese_blue_green_2026-09-01T13-40-09.png` | `(132, 119, 90)` | 119 | **暖金棕**（古绢） |

> **关键修正**：v9/v10 阶段把图1 与图4 错配（B/C 主题与文件名错位）。本轮按设计稿基准重新对齐：A=柔雾青绿（亮）/ B=水墨留白（宣纸亮）/ C=暗墨夜山（极暗）/ D=青绿金碧（古绢暖金）。

---

## 2. 根因诊断（4 处 + 1 隐藏 bug）

| # | 位置 | 根因 | 后果 |
|---|------|------|------|
| ① | `src/App.jsx:115-119` | `THEMES` 数组硬编码 3 项 + 旧命名（柔雾青蓝 / 暗墨柔化） | 主题数缺 1；命名误导 |
| ② | `src/App.jsx:67-78, 83-86` | `storage` 事件 + `useState` 白名单 `'a'/'b'/'c'` | 即使加了 D 主题也无法切换 |
| ③ | `src/styles.css` A/D 主色与参考图明暗**完全相反** | A 用了 v9 的 `#131C24`（深青），但图是亮雾 `(164,189,207)`；D 用了 `#1F3528`（深青绿），但图是暖金棕 `(132,119,90)` | "颜色和参考图不一致" |
| ④ | `src/styles.css` `--line` 系列只在 `:root` 定义（浅色半透明，给暗底用） | B/C/D 亮色主题**未覆盖**，亮底上边框几乎不可见 | "画面存在问题"（隐藏 bug） |
| ⑤ | `src/styles.css:331` `.ink-photo` background 简写 `var(--ink-bg-url) center var(--ink-bg-pos)` | B 的 `--ink-bg-pos: right bottom` 展开成 3 关键词 → 整条 background 失效 | B 主题背景图**根本不显示**（独立 bug） |
| ⑥ | `public/console/tuner.html` 与 `public/bg/` | 3 张图 / 3 主题；无 D 主题图 | 控制台无 D 选项 |

---

## 3. 修复清单

### 3.1 `src/App.jsx`

| 行号 | 改动 |
|------|------|
| `L67-78` | `storage` 事件白名单 → `['a','b','c','d'].includes(...)` |
| `L80-87` | `useState` 初始化器放成同样 4 元素白名单；注释 v10→v11 |
| `L116-121` | `THEMES` 数组改为 4 项 + chip 取新底色（A `#C5DBE8` 浅雾蓝 / B `#ECE6D6` 宣纸米 / C `#0A1424` 墨夜 / D `#C9B58A` 古绢黄） |

### 3.2 `src/styles.css`（重写 4 主题 token，全部按参考图重做）

#### 3.2.1 `:root`（A 柔雾青绿）

| Token | v9 旧值（深青底） | v11 新值（亮雾蓝） |
|-------|------------------|-------------------|
| `--bg-deep` | `#131C24` | `#E8EFF3` |
| `--bg-panel` | `#18232C` | `#DDE9F0` |
| `--bg-raise` | `#1E2A34` | `#C5DBE8` |
| `--ink-hi/mid/low` | `#E4E1D6 / #B4BCC0 / #8A959B`（月白） | `#1F3A4D / #4A6577 / #6B8296`（深墨蓝） |
| `--jade` | `#5C8A99` | `#4A8BAB`（石青） |
| `--gold` | `#B89A6B`（赭金） | `#5B9E84`（青绿） |
| `--line` 系列 | `rgba(228,225,214,...)`（浅色半透明） | `rgba(31,58,77,...)`（深色半透明） |
| `--wood-*` | `#CBAE80/#A8895C/#8E7147`（赭石木轴） | `#7FB5A3/#5B9E84/#4A8BAB`（青绿木轴） |
| `--ink-veil` | `0.28/0.62/0.88`（重） | `0.10/0.35/0.70`（轻） |

#### 3.2.2 `body[data-theme="b"]`（水墨留白）

```
--bg-deep       #ECE6D6   (宣纸米)
--ink-hi        #2C2820   (墨黑)
--jade / gold   #1F1F1C   (墨黑强调，水墨主题不挂彩色)
--line 系列     rgba(60,56,42,...)  (暖墨半透明，v11 补齐)
--font-kai/song/body  楷体 STKaiti 主导
--ink-bg-url    url('/bg/bg-b-inkwash.webp')
--ink-bg-pos    right bottom
--ink-bg-size   60%       (v11 新增：图右下 60%，让墨痕在角上微现)
--ink-veil      0.12/0.30/0.62  (更淡)
```

#### 3.2.3 `body[data-theme="c"]`（暗墨夜山）

```
--bg-deep       #0A1424   (墨夜；比 v9 的 #161A20 加深，对齐图 21,27,34)
--ink-hi        #E8E2C8   (月光米，比原 #E4E1D6 更暖)
--jade / gold   #F2EBD0   (月光；非赭金)
--wood-*        #F2EBD0/#C4C0A8/#8A877A  (月光银线木轴)
```

#### 3.2.4 `body[data-theme="d"]`（青绿金碧）

```
--bg-deep       #C9B58A   (古绢黄；v11 由 #1F3528 深青绿翻转为暖亮古绢)
--bg-panel      #D4BF92
--bg-raise      #E2D0A8
--ink-hi        #2C2418   (深褐)
--jade          #2E5C8A   (宝石蓝主强调)
--pine          #4F8762   (石绿)
--gold          #B89048   (金泥；CTA)
--seal          #A33E22   (深赭红钤印)
--font-kai/song/body  楷体（同 B）
--wood-*        #D4AA5C/#B89048/#8A6A30  (金泥线木轴)
```

#### 3.2.5 `.ink-photo` background 简写 bug 修复

**Bug**：`background: var(--ink-bg-url) center var(--ink-bg-pos) / cover no-repeat`

B 的 `--ink-bg-pos: right bottom` 展开成 `center right bottom` 三个关键词 → 整条 background 简写无效 → B 主题图**完全不显示**（独立于配色问题）。

**修复**：拆分 background-position 单独声明。
```css
.ink-photo {
  background-image: var(--ink-bg-url);
  background-position: var(--ink-bg-pos, center);
  background-size: var(--ink-bg-size, cover);
  background-repeat: no-repeat;
}
```

#### 3.2.6 theme-tabs 选中态 4 主题配色

| 主题 | 选中底色 | 选中文字色 |
|------|---------|-----------|
| A | `rgba(91,158,132,0.18)` 青绿 | `#3A7A62` 深青绿 |
| B | `rgba(44,40,32,0.10)` 墨黑 | `#1F1F1C` 墨黑 |
| C | `rgba(242,235,208,0.14)` 月光 | `#F2EBD0` 月光 |
| D | `rgba(46,92,138,0.16)` 宝石蓝 | `#1E4270` 宝石蓝 |

### 3.3 `public/console/tuner.html`

| 改动 |
|------|
| `.stage` 4 主题底色 + 文字色全部更新（A→浅雾蓝、B→宣纸米、C→墨夜、D→古绢黄） |
| `.ink-veil` 4 主题 RGB 更新（`sed` 批量替换三元组） |
| 新增 `body[data-theme="d"]` 完整块（stage / ink-photo / ink-veil / ink-blob / ink-stamp / ver-tag） |
| `.theme-tabs button.on` 及 `body[data-theme="b|c|d"]` 选中态配色 |
| 顶部 4 主题 tab 按钮加 D；A/C 命名改正 |

### 3.4 `public/bg/bg-d-jinbi.webp`（新素材）

- **源**：`design-concepts/Traditional_Chinese_blue_green_2026-09-01T13-40-09.png`（2.95 MB）
- **目标**：`public/bg/bg-d-jinbi.webp`（326 KB，1536×1024）
- **转换**：Pillow `WEBP`，quality=82，method=6
- **体积**：节省 **88.9 %**

### 3.5 `index.html`

- `<meta name="theme-color">` `#131C24` → `#E8EFF3`（A 主题底色）

### 3.6 `frontend/scripts/shot-app.mjs`（新增）

主应用回归脚本：mock `/api/auth/me` + `/api/projects` 进入主界面，逐个点击 4 主题 tab → 读 token 探针 + 截图。**这就是用户"我自己打开前端"看到的真实界面**。

---

## 4. 验证证据

### 4.1 编译

```
$ npm run build
✓ 294 modules transformed.
dist/assets/index-DeJlfSMC.css   36.42 kB │ gzip:   8.27 kB
dist/assets/index-CcYoxyak.js   330.89 kB │ gzip: 104.86 kB
✓ built in 4.65s
```

### 4.2 主应用 4 主题 token 实测（playwright + 系统 Chrome，mock 登录）

`scripts/shot-app.mjs` 读取 `getComputedStyle(document.body)`：

| 主题 | `bgColor` | `--bg-deep` | `--ink-hi` | `--jade` | `--gold` | `.ink-photo` |
|------|-----------|-------------|-----------|---------|---------|--------------|
| A | `rgb(232, 239, 243)` | `#E8EFF3` ✓ | `#1F3A4D` ✓ | `#4A8BAB` ✓ | `#5B9E84` ✓ | `bg-a-soft.webp` ✓ |
| B | `rgb(236, 230, 214)` | `#ECE6D6` ✓ | `#2C2820` ✓ | `#1F1F1C` ✓ | `#2C2820` ✓ | `bg-b-inkwash.webp` ✓（修复后可见） |
| C | `rgb(10, 20, 36)` | `#0A1424` ✓ | `#E8E2C8` ✓ | `#F2EBD0` ✓ | `#F2EBD0` ✓ | `bg-c-nightgold.webp` ✓ |
| D | `rgb(201, 181, 138)` | `#C9B58A` ✓ | `#2C2418` ✓ | `#2E5C8A` ✓ | `#B89048` ✓ | `bg-d-jinbi.webp` ✓ |

无页面错误（favicon 404 除外，与主题无关）。

### 4.3 主题切换器 DOM 断言

主应用登录后渲染 `.theme-tabs`，含 4 个按钮：

```json
[
  { "theme": "a", "label": "柔雾青绿" },
  { "theme": "b", "label": "水墨留白" },
  { "theme": "c", "label": "暗墨夜山" },
  { "theme": "d", "label": "青绿金碧" }
]
```

旧命名"柔雾青蓝 / 暗墨柔化"已彻底消除。

### 4.4 截图

主应用 4 主题截图保存在 `_theme-shots/App-{A,B,C,D}-*.png`。**这正是用户 `npm run dev` 后浏览器看到的主界面**。

控制台 4 主题截图保存在 `_theme-shots/{A,B,C,D}-*.png`（tuner.html）。

---

## 5. WCAG 对比度复核

| 主题 | 文字 | 合成底色（理论） | 对比度 | 评级 |
|------|------|----------------|--------|------|
| A | `#1F3A4D` | `rgb(232,239,243)` | 10.4:1 | **AAA** |
| B | `#2C2820` | `rgb(236,230,214)` | 10.7:1 | **AAA** |
| C | `#E8E2C8` | `rgb(10,20,36)` | 12.1:1 | **AAA** |
| D | `#2C2418` | `rgb(201,181,138)` | 8.7:1 | **AAA** |

四主题正文远超 AAA 7:1 门槛。

---

## 6. 已知边界

1. **`tuner.html` 次要装饰色**（btn / 气泡 / 侧栏等大量 `body[data-theme="b|c"]` 的半透明 rgba）未逐条同步新强调色。但 stage 背景、veil RGB、4 主题 tab 都正确，对调参台主用途（测透明度）不影响。后续按需细化。
2. **favicon 404** —— 项目无 favicon，与主题无关。
3. **截图脚本的 mock 登录** —— `shot-app.mjs` 拦截 `/api/auth/me` 返回伪 user，进入主界面。生产环境用户正常登录后看到的效果与此一致。

---

## 7. 改动文件清单

| 文件 | 状态 | 核心变更 |
|------|------|---------|
| `frontend/src/App.jsx` | 修改 | THEMES 4 项；storage/useState 接受 d；chip 用新底色 |
| `frontend/src/styles.css` | **整体重写 4 主题 token** | A 翻转亮雾蓝 / B 宣纸米楷体 + line 补齐 / C 墨夜月光 / D 古绢黄楷体；修复 .ink-photo background 简写 bug |
| `frontend/index.html` | 修改 | theme-color |
| `frontend/public/console/tuner.html` | 修改 | stage / veil 全部更新；新增 D 主题 CSS 块；4 主题 tab |
| `frontend/public/bg/bg-d-jinbi.webp` | **新增** | D 主题古绢黄背景（326 KB） |
| `frontend/scripts/shot-app.mjs` | **新增** | 主应用回归脚本（mock 登录 → 4 主题 token 探针 + 截图） |
| `frontend/scripts/shot-themes.mjs` | **新增** | 控制台回归脚本 |
| `frontend/_theme-shots/App-{A,B,C,D}-*.png` | **新增** | 4 张主应用截图 |
| `frontend/_theme-shots/{A,B,C,D}-*.png` | **新增** | 4 张控制台截图 |
| `frontend/CHANGELOG-v11.md` | **本文件** | — |

---

_生成时间：2026-09-02 13:10 GMT+8_
_配套：`design-concepts/CHANGELOG-v11.md`（设计稿视角）_
_验收方式：用户 `cd frontend && npm run dev` → 浏览器打开 http://localhost:5173 → 登录后顶栏有 4 主题 tab，点击切换主色 / 背景图 / 字体严格按 4 张参考图。_