# 皮肤契约（skins/CONTRACT.md）

> v18 前端 · 八套设计语言的实现规约
> 本文件是**单一真源**：新增皮肤、修改皮肤、审查皮肤，一律以本文件为准。
> 项目级术语与数字基准另见 [`docs/CANON.md`](../../../docs/CANON.md)。

## 一、两套作用域

| 作用域 | 载体 | 实现方式 |
| --- | --- | --- |
| 工作台 | `app.html`（React SPA） | `<html data-skin="a…h">` + `src/skins/*.css` 换肤（八套） |
| 落地页 | `index.html` + `landing-{b…f}.html`（前六套）+ `how-it-works.html` / `dossier.html` | 前六套每套一个独立 HTML；第 7/8 套是带独立机制的完整页面（编队总谱 / 论文底片） |

> **第 7/8 套的机制归属**：编队总谱（出声音符 / 演奏全曲 / fermata 停拍）与论文底片
> （逐条解密 / 阵风 / 打字机音效）是**页面级机制**，绑定在 `how-it-works.html` /
> `dossier.html` 两个独立页面，**不进工作台皮肤**。工作台的 `g-score.css` /
> `h-contact.css` 只实现这两套语言的**视觉**（令牌 / 材质 / 排版 / 交互态），
> 三栏结构与 JSX 契约不变，符合 §四第 2 条「只写 CSS」。

两侧共用 `localStorage.lj_skin` 保持同步（落地页切了皮肤，工作台跟着切）。

**皮肤切换器的两处实现（数据同源、文案已统一）**：

| 作用域 | 实现 | 触发按钮文案 | 条目 |
| --- | --- | --- | --- |
| 工作台 | `src/components/SkinPicker.jsx`（`.skin-picker` / `.sp-*`） | 当前皮肤名（`.sp-label`，带色点 `.sp-chip`） | 读 `registry.js` 动态渲染 8 套 |
| 落地页 | `src/landing/shared.js`（`.sw-trigger` / `.sw-item`）；G/H 两页为页内静态 HTML | 固定「切换皮肤」 | 读 `registry.js` 动态渲染 8 套 |

> 落地页触发按钮**不显示当前皮肤名**（2026-10-04 统一为「切换皮肤」），工作台仍显示当前皮肤名以便一眼确认当前语言。
> 两侧数据都来自 `src/skins/registry.js`，新增皮肤无需改切换器代码。

### 注册表字段契约（`src/skins/registry.js`）

新增一套皮肤 = 在 `SKINS` 数组追加一条（**数组顺序 = 弹层与落地页切换器的展示顺序**；`id` 取 `a`…`h`，与 `<html data-skin>` 取值一致）。字段固定 7 项：

| 字段 | 取值 | 消费方 |
| --- | --- | --- |
| `id` | `'a'…'h'`，即 `<html data-skin>` 取值与 `localStorage.lj_skin` 存储值 | `src/hooks/useSkin.js` / 两侧切换器 |
| `label` | 中文皮肤名 | 工作台 `.sp-label`、落地页切换器条目 |
| `en` | 英文名 | `.sp-name > em` |
| `chip` | 色点颜色 | `.sp-chip` 内联 `background` |
| `desc` | 一句话设计语言描述 | `.sp-desc` |
| `landing` | 该皮肤落地页相对路径 | `.sp-foot` 的 `href` |
| `themeColor` | `<meta name="theme-color">` 用色 | `src/hooks/useSkin.js` |

导出面（`registry.js:86`–`:108`）：`SKINS`、`SKIN_IDS`、`DEFAULT_SKIN = 'a'`、`findSkin(id)`、`loadSkin()` / `saveSkin(id)`、`LS_SKIN = 'lj_skin'`。

---

## 二、令牌契约（每套皮肤必须定义全部变量）

皮肤样式依赖这些变量。缺失时 `base.css` / `panels.css` / `fx.css` 会退化为 fallback，
不炸版但会显得扁平。全部定义在 `html[data-skin="X"] { … }` 里。

```
明暗层次   --bg  --surface  --surface-2
文字       --text  --text-2  --text-3
描边       --line  --line-2
强调       --accent  --accent-2  --accent-ink
危险       --danger
字体       --font-display  --font-body  --font-mono
动效       --ease  --dur  --dur-slow
圆角       --r-card  --r-btn  --r-pill
阴影       --shadow-card  --shadow-pop  --shadow-glow
间距       --s-1 … --s-6      （4 / 8 / 12 / 16 / 22 / 28 px 量级）
字号       --fs-micro --fs-sm --fs-md --fs-lg --fs-xl --fs-2xl
可选       --stamp-display / --stamp-text-display  （知识库「已入库」是否用椭圆章）
           --scan-display: none                     （关闭 fx.css 的扫描线）
```

`--accent` / `--accent-2` 会被 `fx.js` 直接读取（粒子、遮罩、印章、光晕），必须给值。

> 皮肤 G（总谱）`--accent` 为钴蓝 `#2E4FA3`、`--accent-2` 为墨黑；皮肤 H（底片）
> `--accent` 为纸白 `#E8E7E2`、`--accent-2` 为弱化灰——两套都是无彩或单彩语言，
> `--danger` 分别取钴蓝系深红与暗房淡红。

### 层级（z-index）规约

z-index 不走皮肤令牌，用下面的固定档位；新增浮层时从档位表取最近的档，
不要发明新数值（当前散落的 88 / 90 属历史遗留，允许保留但不新增）：

```
 0        背景氛围层（.ambient-lines / .wb::after 扫描线）
 5        流内 sticky 元素（.wb-jump）与拖拽中的会话行
 20       顶栏 `.wb-top`（八套皮肤实测一致）与列头 / 卷册等局部粘性元素
 60       皮肤弹层 `.skin-pop`
 100      模态遮罩（.modal-mask，base.css）
 120      fx 全屏层（.fx-layer：粒子 / 换肤遮罩）
 130      顶部成就条（.ach-bar，最高优先展示层）
```

---

## 三、DOM 与类名契约

下列类名与 React JSX 一一对应。**皮肤只能写 CSS，不得改 JSX、不得改类名、
不得新增依赖类名的 DOM 假设**。

### 根

```
.wb                        应用根（建议 flex column / min-height 100vh）
.wb-fill                   弹性占位（flex: 1 1 auto）
.wb-boot                   启动态（.seal + p，印章由 fx.css 做浮动呼吸）
.skl / .skl-line           骨架屏原子（base.css，面板加载中替代纯文本）
```

### 顶栏 `.wb-top`

```
.wb-brand
  .seal                    ← decor.jsx 输出（形状/配色由皮肤决定）
  .wb-brand-text > b      中文名
                 > i      英文小字
.wb-proj
  select.wb-proj-sel      项目下拉
  .wb-btn.wb-btn-ghost ×2 「项目设置」「新建项目」
.skin-picker              皮肤选择器（相对定位容器）
  button.skin-trigger     触发按钮（.wb-btn.wb-btn-ghost）
    .sp-chip              色点（内联 background）
    .sp-label             当前皮肤名
    .sp-caret             ▾
  .skin-pop               弹层（绝对定位）
    .sp-head > .sp-title + .sp-hint
    .sp-grid > button.sp-item(.on)
        .sp-chip + .sp-body > .sp-name(内含 em 英文名) + .sp-desc  + .sp-check
    a.sp-foot             跳「在落地页查看「<皮肤名>」→」（href = 该皮肤的 `landing`）
.wb-views > button.wb-view(.is-on)
.wb-user > b(用户名) + i(角色)
button.wb-btn.wb-btn-ghost.wb-exit
```

> `.skin-picker` / `.sp-*` 需要**每套皮肤各自实现**观感（A 的实现见
> `a-letterpress.css` 第 5 节，可直接参考布局思路，但视觉必须重做）。

### 横幅 `.wb-banner`（`.is-err` / `.is-warn`）

```
.wb-banner > 文本 + button.wb-banner-x（关闭）
```

### 三栏 `.wb-body`

```
aside.wb-col.wb-volumes
  .wb-colhead > .wb-ch-en + .wb-fill + .wb-ch-cn
  button.wb-new > span(＋) + 文本
  .wb-vollist
    .wb-vol(.is-on / .is-dragging)
      .wb-vol-no            序号
      .wb-vol-body > .wb-vol-title + .wb-vol-meta
      button.wb-vol-del     ×
  .wb-vol-empty

section.wb-col.wb-main(.is-streaming)
  .wb-stream > .wb-inner
    .wb-empty > .seal + h2 + p.wb-empty-lead + .wb-prompts > button.wb-prompt ×3
    article.wb-msg(.is-user / .is-ai / .is-jump-hl)   data-midx=消息序号（跳转定位锚）
      .wb-msg-head > .wb-msg-mark + .wb-msg-name + .wb-msg-role + .wb-fill + time.wb-msg-time
      .wb-bubble            markdown 渲染结果（结构见 base.css 第 7 节）
  .wb-break
    .wb-break-head > .wb-break-badge + .wb-break-note + .wb-fill + .wb-break-note
    p.wb-break-ask
    .wb-break-ops > button.wb-break-op ×n + input.wb-break-input + button.wb-btn.wb-btn-ink
  .wb-compose
    .wb-compose-box > textarea.wb-compose-ta + button.wb-compose-send(.wb-btn.wb-btn-ink, .is-busy)
    p.wb-compose-hint

aside.wb-col.wb-side
  nav.wb-side-tabs > button.wb-side-tab(.is-on) ×3
  .wb-side-body
    ol.wb-tl > li.wb-tl-item
        .is-start .is-end .is-intent .is-route .is-plan .is-step .is-interrupt .is-error
        (.is-clickable + role=button + tabIndex —— 推断出对应消息的条目可点击，
         点击跳转并高亮对话区的目标气泡；皮肤可覆写手势观感，不得移除 role/tabIndex)
      > span.wb-tl-no + span.wb-tl-body > span.wb-tl-title + span.wb-tl-meta
    （另两个 tab 的内容由 panels.css 实现）
```

### 其它

```
main.wb-trace-main > .trace-panel       可观测视图
.wb-btn / .wb-btn-ghost / .wb-btn-ink / .wb-btn.is-busy
```

---

## 四、皮肤 CSS 书写规范

1. **所有选择器必须以 `html[data-skin="X"]` 开头**，避免污染其它皮肤。
2. 只写 CSS。不得修改任何 `.jsx` / `.html` / `.js`。
3. 不滥用 `!important`；仅在需要压过 `base.css` / `panels.css` 同优先级声明时使用，
   并在注释里写明压的是哪条规则。
4. 必须覆写 `.skin-picker` / `.skin-pop` / `.sp-*` 全套。
5. 二级面板（知识库 `.kb-*` / 档案 `.arch-*` / 可观测 `.trace-*` / 登录页 `.auth-*`）
   由 `panels.css` 吃令牌自动适配；**仅在本皮肤的性格与之冲突时**做定向覆写。
6. 必须给三档响应式：`≤1380px`（收窄右栏）、`≤1080px`（右栏折到下方）、
   `≤820px`（单列 + 顶栏换行）。
7. 动效只允许作用于 `transform` / `opacity` / `translate`；不得动画 `width` / `height` /
   `top` / `left`（会触发布局重排）。
8. **不要**写跟随光标的拖尾 / 光晕（`fx.js` 已明确不做，属「AI 味」重灾区）。
9. 注释用中文，写「为什么」而不是「做了什么」。
10. **文件末尾保留「§ 15 · 可读性与信息层次」段**，集中处理七件事：元信息字号下限、
    正文行宽、命中区、顶栏分组、待确认条降权、时间线分主次、空态去对称居中。
    该段与前文同特异性、置于末尾以便覆盖旧值，**回退只需删除本段**。
    八套的写法**互不相同**（各自用自身的视觉语言实现，如 A 用校对方块、D 用竖排方框签、
    F 用字段名、E 用错位套印）——**新增皮肤须自行编写，不得从任一套复制**。
    详见 [`docs/frontend-versions/OPTIMIZATION_ROUND19.md`](../../../docs/frontend-versions/OPTIMIZATION_ROUND19.md)。
11. 按下反馈由 `base.css` 统一提供（`:active { scale: .97 }`，scale 为独立属性，
    与 fx 层的 transform 所有权互不冲突）；皮肤自带的 hover 位移**无需重复声明**按下态。

---

## 五、自检清单

- [ ] 令牌变量全部定义，且 `--accent` / `--accent-2` 有明确值
- [ ] 三栏在 1440 / 1280 / 1024 / 768 四个宽度下均可用
- [ ] `.skin-picker` 弹层能正常展开、点击项有选中态
- [ ] 空态（无会话 / 无消息 / 无时间线）不塌陷
- [ ] 中断确认条（`.wb-break`）在长问题文本下不破版
- [ ] 长标题在 `.wb-vol-title` / `.wb-tl-title` 内不溢出（ellipsis 或换行）
- [ ] `prefers-reduced-motion: reduce` 下无持续动画（fx.css 已兜底，皮肤不得反向覆盖）
- [ ] 皮肤 G/H 的视觉语言与其独立页面（`how-it-works.html` / `dossier.html`）的机制语义一致：
      总谱看谱线底纹 / fermata 中断条，底片看撕边纸条 / 接触印样帧
- [ ] 无硬编码主题色（颜色只走变量或本皮肤独有的具名值）
- [ ] 元信息字号 ≥ 11px（中文在 Windows ClearType 下的可读性下限）
- [ ] 可点击元素命中区 ≥ 30×30px（`.wb-vol-del` / `.wb-view` / `.wb-side-tab`）
- [ ] 空态不是「印章 + 标题 + 说明 + 三个胶囊」的对称居中模板
- [ ] 文件末尾有 § 15 段，且写法为本皮肤独有（未被其它皮肤复制）