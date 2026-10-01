# 皮肤契约（skins/CONTRACT.md）

> v18 前端 · 六套设计语言的实现规约
> 本文件是**单一时真源**：新增皮肤、修改皮肤、审查皮肤，一律以本文件为准。

## 一、两套作用域

| 作用域 | 载体 | 实现方式 |
| --- | --- | --- |
| 工作台 | `app.html`（React SPA） | `<html data-skin="a…f">` + `src/skins/*.css` 换肤 |
| 落地页 | `landing-*.html`（6 个独立静态页） | 每套皮肤一个 HTML。六种版式结构差异过大，**无法**靠 CSS 换肤 |

两侧共用 `localStorage.lj_skin` 保持同步（落地页切了皮肤，工作台跟着切）。

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

---

## 三、DOM 与类名契约

下列类名与 React JSX 一一对应。**皮肤只能写 CSS，不得改 JSX、不得改类名、
不得新增依赖类名的 DOM 假设**。

### 根

```
.wb                        应用根（建议 flex column / min-height 100vh）
.wb-fill                   弹性占位（flex: 1 1 auto）
.wb-boot                   启动态（「加载中…」）
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
    a.sp-foot             跳「在落地页查看该皮肤」
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
    article.wb-msg(.is-user / .is-ai)
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

---

## 五、自检清单

- [ ] 令牌变量全部定义，且 `--accent` / `--accent-2` 有明确值
- [ ] 三栏在 1440 / 1280 / 1024 / 768 四个宽度下均可用
- [ ] `.skin-picker` 弹层能正常展开、点击项有选中态
- [ ] 空态（无会话 / 无消息 / 无时间线）不塌陷
- [ ] 中断确认条（`.wb-break`）在长问题文本下不破版
- [ ] 长标题在 `.wb-vol-title` / `.wb-tl-title` 内不溢出（ellipsis 或换行）
- [ ] `prefers-reduced-motion: reduce` 下无持续动画（fx.css 已兜底，皮肤不得反向覆盖）
- [ ] 无硬编码主题色（颜色只走变量或本皮肤独有的具名值）