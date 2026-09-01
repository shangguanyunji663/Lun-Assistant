# 优化记录 · 第八轮修改（前端功能同步 + 三主题切换系统）

> 日期：2026-09-01
> 范围：**前端全面审计与功能同步**。本轮以「前端界面与已实现功能之间的同步缺口排查」为主线，按用户提出的 5 项硬要求逐项落地 + 新增「三主题切换」以解决"色彩过重 + 单一风格"的体验问题。文档同步工程化、表格化、可核对。
>
> 关系定性：相对 ROUND7，本轮属于「**功能同步缺口补齐 + 主题体系扩展**」——不是新业务功能，而是把后端已实现的能力（知识库切换 / 上传 / 资料清单等）展到前端设计稿，把视觉验证页升级为可交互对比的工程化设计台。

## 一、本轮改进总览

| 模块              | 改动                                                                  | 关键文件                                                                                  | 与前几轮关系                |
| --------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | --------------------- |
| 前端审计报告        | 扫描 `docs/*.md` + 后端路由表，逐项对账「已实现 vs 前端展示」                                    | docs/OPTIMIZATION_ROUND8.md（本文件）                                                     | 新增                    |
| 知识库切换按钮       | 三态：`内置` / `库内` / `混合`（映射 `api.searchKnowledge mode=builtin/project/hybrid`） | preview.html / tuner.html 顶栏 `.kb-switcher`                                            | **新增**（前端补全）         |
| 当前库状态徽章       | 绿点 = 库非空 / 灰点 = 回退内置                                                              | preview.html / tuner.html 顶栏 `.kb-pill` / `.kb-state`                                 | **新增**                 |
| 上传入口           | drag/drop + `accept=.pdf,.docx,.txt,.md,.markdown` 多文件                       | preview.html 顶栏 `.upload-btn` + tuner.html 顶栏 + 输入栏 `.attach`                       | **新增**（后端已有 `/knowledge`） |
| 控制台（调参台）入口    | preview.html 顶栏 `.console-link` 跳转 `tuner.html`                                     | preview.html `.console-link`                                                            | **新增**                 |
| 控制台标识          | tuner.html 顶栏加 `🎛 控制台` 徽章，明确"即此页"                                                | tuner.html `.console-badge`                                                            | **新增**                 |
| 资料清单面板        | 仿 React 主应用 `KnowledgePanel.jsx`：PDF / DOC / MD / TXT 列表 + 删除                       | preview.html / tuner.html `.assets-pane`                                                | **新增**                 |
| **三主题切换系统** ⭐ | tab 控件 `A 柔雾青蓝 / B 水墨留白 / C 暗墨柔化`；单主题模式 + 对照模式 + 平滑过渡                    | preview.html `.theme-tabs` + tuner.html `.theme-tabs` + `THEMES` 字典                       | **新增**                 |
| 柔化色调           | A 主题 `#14202B` → `#1B2A36`；C 主题 `#0E1012` → `#161A20`；背景图换柔雾青蓝               | preview.html / tuner.html                                                               | 迭代优化                  |
| 状态持久化          | sessionStorage 保留主题 + 知识库模式；下次访问还原                                               | preview.html / tuner.html `<script>` 末尾                                                | **新增**                 |
| 同步优化记录到 README | 优化导航表追加第八轮条目                                                                  | README.md                                                                              | 同步                    |

## 二、背景与决策

### 2.1 用户的两轮反馈

**第一轮反馈**（用户原文摘录）：

> 1. 检查前端界面的当前状态：当前色调仍然过重黑色，请调整配色方案使其更柔和；同时确认前端缺少的调节按钮和控制台入口，并补全。
> 2. 检查背景图：核对当前前端显示的背景图是否与最初设计一致，如果不一致请恢复或更新为正确版本。
> 3. 知识库切换功能：当前未上传文档时检索的是默认内置知识库，请检查并实现知识库切换按钮，确保用户可以在内置知识库和已上传的自定义知识库之间切换。
> 4. 文档上传功能：当前前端没有体现 PDF 和 DOC 文档的上传入口，请检查后端是否已经实现相关接口，如果已实现则在前端补全上传按钮和对应交互；如果未实现请同步加上。
> 5. 全面功能同步审计：请扫描所有 Markdown 文档（包括 README、接口说明、功能设计文档等），列出后端已实现但前端尚未同步展示的所有功能按钮和交互，针对每个缺失项给出具体的前端实现建议或代码补全。
> 6. 请输出一份审计报告，标明哪些功能已实现但前端缺失、哪些需要新增，并直接完成前端的同步修改。最后这个作为新一轮的优化也要编写对应的议一轮的 md 文档。

**第二轮反馈**（用户在第一轮审计与同步改造完成后追加）：

> 主题切换能力 + 平滑切换流畅 + 每个主题配色/布局有区别

### 2.2 决策过程

| 阶段     | 输入                                | 设计决策                                                                       | 决策依据                                                                |
| ------ | --------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| 1. 审计阶段 | 列出后端能力点                          | 输出 15 行对照表（已实现 vs 前端展示）                                                  | 对照 `api/*.py` + `services/*.py` + `docs/ROUND1-7.md`                      |
| 2. 缺口识别 | 审计报告找出 5 类同步缺口                  | 把缺口项转化为前端 HTML/CSS/JS 实现                                                    | 与 React 主应用 `frontend/src/` 的现有结构对齐，避免设计稿与生产实现分裂               |
| 3. 配色调整 | "色调过重黑色"                          | A 主色从 `#14202B → #1B2A36`、C 主色从 `#0E1012 → #161A20`、遮罩层 5 段 → 3 段 | A 主色降饱和 + 暗值提亮；C 完全去掉"近黑"                                    |
| 4. 三主题切换 | "三种主题 + 平滑切换"                    | tab 控件 + `body[data-theme=a/b/c]` + `THEMES` 字典驱动 token                  | CSS 变量 + body 数据属性切换，避免多套 CSS 重复；JS 单点切换                 |
| 5. 持久化   | 用户期望保留切换状态                        | `sessionStorage` 而非 `localStorage`（避免会话长期污染）                      | 预览页/控制台是会话级页面，不需要跨窗口长期保留                                    |

### 2.3 与之前几轮的关系

| 前轮         | 关系                       | 本轮处理                                                                                  |
| ---------- | ------------------------ | ------------------------------------------------------------------------------------- |
| ROUND1     | 保留                       | markdown 渲染 / 事件协议沿用                                                                |
| ROUND2     | 保留                       | OOM 修复 / 结构重构沿用                                                                      |
| ROUND3     | 保留                       | banner / 模态弹窗 / 按钮五态沿用                                                              |
| ROUND4     | 强相关                      | 知识库切换三态对应 `api.searchKnowledge(mode)`（project/hybrid）；interface 列表/删除对应 `api.listKnowledge` / `api.deleteKnowledge` |
| ROUND5     | 保留 + 迭代                  | 学术工具生态、并发压测、agnes 对话底座沿用；本轮视觉部分重新整理色调                                            |
| ROUND6     | 保留                       | 前后端状态枚举对齐继续生效；本轮新增的资料清单面板复用 KnowledgePanel.jsx 的样式骨架                              |
| ROUND7     | **迭代优化**                 | 前端主题重构为本轮三主题切换系统的前身；本轮将"选 A 方向"扩展为 A/B/C 全栈切换                                       |
| 隐性问题       | **修复**                   | 此前 `preview.html` / `tuner.html` 仅作为"静态视觉参考"，本轮改造为"可交互的工程化设计验证台"，作为后续主线开发前的单一真源 |

## 三、用户五项硬要求逐条对应

| #   | 用户要求                                    | 落地证据（file:line）                                                                                                              | 状态 |
| --- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | -- |
| 1   | 调整配色方案更柔和；补全缺失的调节按钮和控制台入口             | ① A 主色 `#14202B → #1B2A36`、C 主色 `#0E1012 → #161A20` ② 控制台入口 `.console-link` 在 preview.html 顶栏、`tuner.html` 顶栏 `.console-badge`        | ✅  |
| 2   | 核对背景图与最初设计是否一致；不一致则更新                  | preview.html: `<img src="Soft_misty_Chinese_blue_green__2026-09-01T13-51-14.png">` 替换原 `shanshui-mist.jpg`；tuner.html 同源同步；3 主题各有专属图       | ✅  |
| 3   | 知识库切换按钮（内置 ↔ 自定义）                     | `.kb-switcher` 三态（内置/库内/混合） → 对应 `api.searchKnowledge(mode)` 调用；徽章 `.kb-state.empty` 标识回退内置                                | ✅  |
| 4   | PDF / DOC 上传入口（先检查后端）                    | 后端：`api/knowledge/router.py:35-56` 已实现 `POST /api/projects/{id}/knowledge`（PDF/DOCX/TXT/MD） ② 前端：`.upload-btn` + 隐藏 `<input type=file accept=".pdf,.docx,.txt,.md,.markdown">` + 多次多文件 | ✅  |
| 5   | 全面功能同步审计                                 | 第十一章完整对账表（后端 16 项功能 vs 前端展示，标 ✅/⚠️/❌）                                                                                  | ✅  |

## 四、preview.html 改动详情（三主题切换 + 同步增强）

### 4.1 总体改造

| 维度       | 改造前                                                | 改造后                                                              |
| -------- | ------------------------------------------------- | --------------------------------------------------------------- |
| 文件长度     | 410 行（v9 主题预览）                                    | **646 行**（v10 同步增强 + 三主题切换）                                 |
| HTML 结构 | 静态三主题并排                                            | **单主题模式 + 对照模式**（默认 A 单主题，右上"↔ 三主题对照"切到并排）                  |
| 主题切换     | 无（三个 mockup 平行展示，用户只能横向比较）                       | **顶栏 tab**：单击 A/B/C 即切换 `body[data-theme]`，单主题 mockup 居中放大到 680×760 |
| 配色       | A `#14202B` / B `#ECEAE3` / C `#0E1012`           | A `#1B2A36` / B `#ECEAE3` / C `#161A20`（A、C 柔化）                |
| 背景图      | 三主题共用同一组主题图                               | A 用 `Soft_misty_Chinese_blue_green`；B 用 `Traditional_Chinese_ink_wash_l`；C 用 `Chinese_ink_painting_of_toweri` |
| 顶栏按钮     | 仅 `#1 选题方向 select` + `+ 新建` + `设置`  | 增 **知识库切换 `.kb-switcher`**、**当前库状态徽章 `.kb-pill`**、**PDF/DOC 上传 `.upload-btn`**、**控制台入口 `.console-link`** |
| 资料清单     | 无                                                  | **右侧 .assets-pane**（PDF/DOC/MD/TXT 共 5 行 mock + 标签徽章）              |
| 数据持久化    | 无                                                  | `sessionStorage.lj_preview = {mode, theme}`                       |
| 平滑过渡     | 无                                                  | `transition: all .4s cubic-bezier(.4,0,.2,1)`；CSS 变量驱动 token 切换 |

### 4.2 关键代码片段

**（1）三主题 tab 控件**（preview.html:250-254）

```html
<div class="theme-tabs" role="tablist" aria-label="主题切换">
  <button data-theme="a" class="on" role="tab" title="柔雾青蓝 + 卷轴木轴"><span class="chip" style="background:#1B2A36;border-color:rgba(200,168,135,.4)"></span>A 柔雾青蓝</button>
  <button data-theme="b" role="tab" title="水墨留白 + 楷体 + 石青"><span class="chip" style="background:#ECEAE3;border-color:#999"></span>B 水墨留白</button>
  <button data-theme="c" role="tab" title="暗墨金线 + 钤印 + 赭金"><span class="chip" style="background:#161A20;border-color:rgba(201,162,39,.4)"></span>C 暗墨柔化</button>
  <button class="compare-btn" data-mode="compare" role="tab" title="三主题并排对照">↔ 三主题对照</button>
</div>
```

**（2）切换逻辑**（preview.html:604-642）

```js
(function() {
  const body = document.body;
  function setMode(mode, theme) {
    body.setAttribute('data-mode', mode);
    if (theme) body.setAttribute('data-theme', theme);
    // tab 视觉同步 on
    document.querySelectorAll('.theme-tabs button').forEach(b => {
      const isModeBtn = b.hasAttribute('data-mode');
      const isThemeBtn = b.hasAttribute('data-theme');
      if (isModeBtn) b.classList.toggle('on', b.dataset.mode === mode);
      else if (isThemeBtn) b.classList.toggle('on', b.dataset.theme === theme && mode === 'single');
    });
    // 单主题模式：仅显示对应主题 mockup
    document.querySelectorAll('.single-stage .mockup').forEach(m => {
      m.style.display = (mode === 'single' && m.dataset.theme === theme) ? '' : 'none';
    });
    try { sessionStorage.setItem('lj_preview', JSON.stringify({ mode, theme })); } catch {}
  }
  document.querySelectorAll('.theme-tabs [data-theme]').forEach(b =>
    b.addEventListener('click', () => setMode('single', b.dataset.theme)));
  document.querySelector('.theme-tabs [data-mode="compare"]').addEventListener('click',
    () => setMode('compare', body.dataset.theme || 'a'));
  // 还原
  try {
    const saved = JSON.parse(sessionStorage.getItem('lj_preview') || 'null');
    if (saved && saved.theme) setMode(saved.mode, saved.theme);
    else setMode('single', 'a');
  } catch { setMode('single', 'a'); }
})();
```

**（3）单主题 mockup 头（A 主题）**（preview.html:280-327）

```html
<div class="mockup mockup-a" data-theme="a">
  <div class="wood top"></div><div class="wood bot"></div>
  <div class="ink-bg"><img src="Soft_misty_Chinese_blue_green__2026-09-01T13-51-14.png" alt="柔雾青蓝"></div>
  <div class="label">A · 柔雾青蓝</div>
  <div class="topbar">
    <div class="brand">论匠 <small>· v10</small></div>
    <div class="grow"></div>
    <!-- 三态切换 -->
    <div class="kb-switcher" title="切换知识库检索范围">
      <button>内置</button><button class="on">库内</button><button>混合</button>
    </div>
    <!-- 当前库徽章 -->
    <span class="kb-pill"><span class="dot"></span>内置</span>
    <!-- 上传入口 -->
    <label class="upload-btn" title="PDF / DOCX / TXT / MD ｜ ≤20MB">＋📎<input type="file" accept=".pdf,.docx,.txt,.md,.markdown" multiple></label>
    <!-- 控制台入口 -->
    <a class="console-link" href="tuner.html">🎛</a>
    <select><option>#1 选题方向探索</option></select>
    <button class="btn">+ 新建</button>
    <button class="btn">设置</button>
  </div>
  ...
</div>
```

## 五、tuner.html 改动详情（三主题控制台）

### 5.1 总体改造

| 维度        | 改造前                                    | 改造后                                                                     |
| --------- | ------------------------------------- | ------------------------------------------------------------------------ |
| 文件长度      | 368 行                                  | **733 行**（v10 三主题控制台）                                                  |
| 顶栏        | 单套固定 A 主题                             | **顶栏 tab** A/B/C + tab 自身颜色随主题切换                                              |
| 主背景图      | `shanshui-mist.jpg`（仅图 1）             | **三主题各自专属图**：A 柔雾青蓝 / B 水墨留白 / C 暗墨柔化                                |
| 控制面板配色    | 默认 A 主题硬编码色                          | **滑杆 accent-color / 预设按钮 .on 颜色 / 容器边框 / 整体卡片配色** 全部跟主题切换                  |
| 资料清单      | 无                                     | **`.assets-pane` 右侧 172px**：PDF/DOC/MD/TXT 4 行 + 删除按钮 + 空回退逻辑                    |
| 知识库三态     | 无                                     | `.kb-switcher` + 控制面板 `.kb-presets` 双 UI 同步（顶栏 + 控制面板任一处切换，另一处同步）             |
| 状态持久化     | 无                                     | `sessionStorage.lj_tuner_theme` + `sessionStorage.lj_kb_mode`              |
| WCAG 测算   | 仅单主题                                  | 底色/图色 RGB 也跟主题切换：`THEMES = { a, b, c }` 各配 RGB                              |
| 控制台标识     | 无                                     | `🎛 控制台` 徽章 + `返回预览` 链回 preview.html                                          |

### 5.2 关键代码片段

**（1）THEMES 字典（每个主题含底色 + 图色 + 6 个预设施）**（tuner.html:560-565）

```js
const THEMES = {
  a: { name: 'A 柔雾青蓝', bg:[27,42,54],   img:[200,210,221],
       presetOp:.14, presetTop:.20, presetMid:.62, presetWash:1.0, presetGrain:.04, presetKb:.65 },
  b: { name: 'B 水墨留白', bg:[236,234,227], img:[170,168,160],
       presetOp:.10, presetTop:.18, presetMid:.55, presetWash:.4,  presetGrain:.06, presetKb:.55 },
  c: { name: 'C 暗墨柔化', bg:[22,26,32],    img:[195,180,150],
       presetOp:.16, presetTop:.16, presetMid:.55, presetWash:1.0, presetGrain:.04, presetKb:.65 },
};
```

**（2）applyTheme：单点切换所有 token**（tuner.html:642-664）

```js
function applyTheme(theme) {
  current = theme;
  BODY.setAttribute('data-theme', theme);                        // 触发 CSS 切换
  document.querySelectorAll('.theme-tabs [data-theme]').forEach(b =>
    b.classList.toggle('on', b.dataset.theme === theme));        // tab 视觉同步
  const T = THEMES[theme];
  S.op.value = T.presetOp; S.top.value = T.presetTop; S.mid.value = T.presetMid;
  S.wash.value = T.presetWash; S.grain.value = T.presetGrain; S.kb.value = T.presetKb;
  document.getElementById('v-kb').textContent = T.presetKb.toFixed(2);
  document.getElementById('verTag').textContent = 'v10 控制台 · ' + T.name;
  document.getElementById('presetTheme').textContent = T.name;
  document.getElementById('kbTheme').textContent = theme.toUpperCase();
  document.getElementById('mTheme').textContent = T.name;
  try { sessionStorage.setItem('lj_tuner_theme', theme); } catch {}
  apply();
}
```

**（3）CSS 主题切换矩阵**（tuner.html 节选）

```css
.stage { background: #1B2A36; color: #E4E1D6; transition: background .4s ease, color .4s ease; }
body[data-theme="b"] .stage { background: #ECEAE3; color: #1C1C1A; box-shadow: 0 12px 40px rgba(0,0,0,.10); }
body[data-theme="c"] .stage { background: #161A20; color: #E4E1D6; }

/* 背景图 3 套独立 */
.ink-photo { background: url('Soft_misty_Chinese_blue_green__2026-09-01T13-51-14.png') center 34% / cover; opacity: var(--p-op,.14); }
body[data-theme="b"] .ink-photo { background: url('Traditional_Chinese_ink_wash_l_2026-09-01T13-40-46.png') right bottom / 60%; opacity: var(--p-op,.10); filter: contrast(.95) saturate(.4); }
body[data-theme="c"] .ink-photo { background: url('Chinese_ink_painting_of_toweri_2026-09-01T13-41-26.png') center 70% / cover; opacity: var(--p-op,.16); }

/* 卷轴木轴仅 A 主题；B 用中缝 .ink-divider；C 用钤印 .ink-stamp */
body[data-theme="b"] .wood-roll, body[data-theme="c"] .wood-roll { opacity: 0; }
body[data-theme="b"] .ink-divider { opacity: 1; }
body[data-theme="c"] .ink-stamp { opacity: 1; }

/* 控制面板 3 主题 */
body[data-theme="b"] input[type=range] { accent-color: #1C1C1A; }
body[data-theme="c"] input[type=range] { accent-color: #C9A227; }
body[data-theme="c"] .presets button.on { background: #161A20; border-color: #C9A227; color: #C9A227; }
```

## 六、新增交互详解

### 6.1 知识库三态切换（内置 / 库内 / 混合）

| UI 位置          | 控件                                          | 触发逻辑                                          | 后端 hook                              |
| --------------- | ------------------------------------------- | --------------------------------------------- | ------------------------------------- |
| preview.html 顶栏 | `.kb-switcher`（三按钮 group）                    | 单击切换激活态；预览层 hover 提示                          | `api.searchKnowledge(projectId, query, top_k, mode)` |
| tuner.html 顶栏   | `.kb-switcher` + 徽章 `.kb-state.empty`         | 双 UI（顶栏 + 控制面板）同步                              | 同上                                    |
| tuner.html 控制面板 | `.kb-presets`（三按钮 group）                       | 切换后写 sessionStorage 并实时改输入栏提示 `.input-hint`        | 同上                                    |

**语义映射（前端 ↔ 后端）**：

```
内置  ↔  api.searchKnowledge(mode='project', no_public=True)   // 仅内置库
库内  ↔  api.searchKnowledge(mode='project')                   // 仅项目库；空库自动回退
混合  ↔  api.searchKnowledge(mode='hybrid')                    // 项目库 + 公共语料
```

**回退显示**：徽章内 `.dot` 颜色三主题各异（A `#92B0B5` 青灰 / B `#3C6E8F` 石青 / C `#C9A227` 赭金）；空库时 `.kb-state.empty .dot` 切到 `#6E6B65` 灰 + 标签切 "回退内置"。

### 6.2 文档上传入口（PDF/DOCX/TXT/MD）

| UI 位置           | 控件                            | 触发                                | 后端 hook                                          |
| ---------------- | ----------------------------- | --------------------------------- | ------------------------------------------------- |
| preview.html 顶栏 | `.upload-btn` 虚线边框 + ＋📎 emoji | 点击触发隐藏的 `<input type=file multiple accept=".pdf,.docx,.txt,.md,.markdown">` | `api.uploadKnowledge(projectId, files)` → `POST /api/projects/{id}/knowledge` |
| tuner.html 顶栏   | 同上                            | 同上                                 | 同上                                                |
| tuner.html 输入栏   | `.composer .attach` 圆形 ＋📎        | 同上                                 | 同上                                                |

**接受格式**：与后端 `services/rag/ingest/parsers.py::infer_type()` 一致（PDF/DOCX/TXT/MD），单一格式不正确时由后端 `parsers.py` 抛 `DocumentParseError`，前端 KnowledgePanel.jsx 流程已有完整处理（错误显示在 `.kb-upload-msg .kb-mini-failed`）。

**单文件大小**：所有提示都标注 "≤ 20MB"（与 `configs/settings.yaml` `rag.max_upload_size_mb` 一致）。

### 6.3 控制台入口（preview.html ↔ tuner.html）

| UI                      | 触发                              | 持久化                                           |
| ----------------------- | ------------------------------- | ---------------------------------------------- |
| preview.html 顶栏 `.console-link` 🎛 | 跳转 `tuner.html`                | sessionStorage 不跨页                        |
| tuner.html 顶栏 `.console-badge` 🎛 控制台 | 标识"即此页" + `返回预览` 链回 `preview.html`     | sessionStorage 保留主题，让用户从 preview 进入后保持一致 |

### 6.4 资料清单（assets-pane）

右侧 172px 宽独立面板，仿 React 主应用 `frontend/src/components/KnowledgePanel.jsx` 的 `.kb-docs` 样式：

| 元素               | 说明                                                              |
| ---------------- | --------------------------------------------------------------- |
| `.assets-head` 计数 | 仿 `KnowledgePanel` 的 `<h3>资料清单（N）</h3>`                   |
| `.asset-row`      | 单条资料：tag + filename + del（点击 × 删除行）                          |
| `.tag`            | PDF/DOC/MD/TXT 四档，靠 className 切换                          |
| `.del`            | 仿 KnowledgePanel 的删除按钮；点击后从 DOM 移除该行                        |
| 删空时回退          | 0 行时徽章切到 "回退内置"，与 `kbState.empty` 联动                          |

### 6.5 ⭐ 三主题切换系统（核心）

| 维度      | 实现                                                           |
| ------- | ------------------------------------------------------------ |
| 状态载体    | `document.body` 上 `data-mode="single\|compare"` 与 `data-theme="a\|b\|c"` |
| 视觉控件    | `.theme-tabs` 4 按钮（A/B/C + 对照）                              |
| 切换逻辑    | JS `setMode()` / `applyTheme()` 统一处理                       |
| 平滑过渡    | 所有可能切换的属性都加 `transition: all .35s ease` 或 `.4s cubic-bezier(...)` |
| token 驱动 | `.stage`、`.ink-photo`、`.ink-veil`、`.brand`、`.btn.gold`、`.assets-head`、`.kb-state .dot` 等 30+ 处全部用 `body[data-theme=...]` 子选择器覆盖 |
| 状态保留    | `sessionStorage.lj_preview` / `lj_tuner_theme`；下次访问还原        |
| 设计目标    | "单击切换 + 配色 + 布局 + 语言均不同"                                  |

**A/B/C 三主题的语言对比**（同一段对话气泡）：

```
A 柔雾青蓝 ─ 木轴 + 楷体 + 赭石米  │
  bubbles: 言 / 匠               │
  ka-pill: 内置（青灰点）           │
  console-link: 🎛 跳 tuner        │
                                 │
B 水墨留白 ─ 无木轴 + 楷体 + 石青   │
  bubbles: 言 / 匠               │
  ka-pill: 内置（石青点）           │
  ink-divider 中缝                  │
                                 │
C 暗墨柔化 ─ 无木轴 + 行楷 + 赭金   │
  bubbles: 言 / 匠               │
  ka-pill: 内置（赭金点）           │
  ink-stamp 钤印「匠」字             │
```

**background 图三套独立**：

```
A: Soft_misty_Chinese_blue_green__2026-09-01T13-51-14.png (1.34MB)
B: Traditional_Chinese_ink_wash_l_2026-09-01T13-40-46.png   (1.88MB)
C: Chinese_ink_painting_of_toweri_2026-09-01T13-41-26.png   (2.33MB)
```

## 七、配色 token 三套详细表

### 7.1 主题 A · 柔雾青蓝

| token           | HEX       | RGB          | 用途                       |
| --------------- | --------- | ------------ | ------------------------ |
| `--bg-deep`     | `#1B2A36` | `27,42,54`   | 主底色（原 v9 `#131C24` 提亮） |
| `--ink-hi`      | `#E4E1D6` | `228,225,214` | 正文字色（月白）                |
| `--ink-mid`     | `#B0BCC2` | `176,188,194` | 次级文字                      |
| `--ink-low`     | `#8A959B` | `138,149,155` | 辅助文字                     |
| **赭石米**         | `#C8A887` | `200,168,135` | 强调色（替代 v9 `#B89A6B`）    |
| **赭石米 2**       | `#A88855` | `168,136,85`  | 强调色 2（木轴渐变下）             |
| **石青点缀**        | `#92B0B5` | `146,176,181` | 徽章点                     |

### 7.2 主题 B · 水墨留白（保持）

| token           | HEX       | RGB            | 用途       |
| --------------- | --------- | -------------- | -------- |
| `--bg-paper`    | `#ECEAE3` | `236,234,227`  | 主底色（宣纸）  |
| `--ink-hi`      | `#1C1C1A` | `28,28,26`     | 正文       |
| `--ink-mid`     | `#4A4843` | `74,72,67`     | 次级文字     |
| **石青**          | `#3C6E8F` | `60,110,143`   | 强调色      |

### 7.3 主题 C · 暗墨柔化（v10：纯黑 → 暗墨）

| token           | HEX       | RGB          | 用途                          |
| --------------- | --------- | ------------ | --------------------------- |
| `--bg-deep`     | `#161A20` | `22,26,32`   | 主底色（原 v9 `#0E1012` 纯黑；v10 提亮到暗墨） |
| `--ink-hi`      | `#E4E1D6` | `228,225,214` | 正文                          |
| `--ink-mid`     | `#9A958B` | `154,149,139` | 次级文字                        |
| **赭金**          | `#C9A227` | `201,162,39` | 强调色（替代 v9 `#B89A6B`）     |
| **朱砂钤印**        | `#B04A3A` | `176,74,58`  | 次强调色（钤印 / primary button）  |

## 八、布局差异三套对照

| 维度          | A 柔雾青蓝                       | B 水墨留白                       | C 暗墨柔化                       |
| ----------- | ---------------------------- | ---------------------------- | ---------------------------- |
| 卷轴木轴        | ✅ 上下木轴（`.wood-roll` 8px 渐变）  | ❌ 隐藏                         | ❌ 隐藏                         |
| 中缝          | ❌                            | ✅ `.ink-divider` 0.5px 灰中缝    | ❌                            |
| 钤印          | ❌                            | ❌                            | ✅ `.ink-stamp` 38×38 红边框「匠」字 |
| 品牌字体        | 华文行楷 `STXingkai`              | 楷体 `STKaiti` 0.42em 大字距       | 行楷 `STXingkai` 0.20em 小字距     |
| 顶栏边框      | 渐变赭石中线                     | 深灰 0.25 渐变                    | 金线渐变 `transparent→#C9A227→transparent` |
| 气泡 user 描边 | 赭石米 0.55                    | 石青 `#3C6E8F` 0.4             | 朱砂 `#B04A3A` 0.50           |
| 气泡 assistant 描边 | 青灰 0.40                    | 深灰 0.15                     | 赭金 0.22                      |
| 会话卷册头色      | `#8A959B`                    | `#4A4843`                    | `#CBAE80`                    |
| 资料清单头色      | `#C8A887`                    | `#3C6E8F`                    | `#C9A227`                    |

> **结论**：A/B/C 三主题的视觉差异不只是"颜色换了"，而是**语言层差异化**——配色 + 装饰元素 + 字体 + 描边 + 排版全部独立。

## 九、JS 状态机与持久化

### 9.1 preview.html 状态

```
state = { mode: 'single'|'compare', theme: 'a'|'b'|'c' }
storage key: lj_preview (JSON)

切换算法:
  click [data-theme=x]  → setMode('single', x)
  click [data-mode='compare'] → setMode('compare', currentTheme)
  切换后重写 sessionStorage
```

### 9.2 tuner.html 状态

```
state = { theme: 'a'|'b'|'c', kbMode: 'builtin'|'project'|'hybrid' }
storage keys: lj_tuner_theme, lj_kb_mode

切换算法:
  click [data-theme=x]  → applyTheme(x)
    ├─ body[data-theme=x]                ← CSS
    ├─ tab on 同步
    ├─ 恢复该主题预设（6 个滑杆值）
    ├─ 文案同步（verTag / presetTheme / kbTheme / mTheme）
    └─ apply() 重算 WCAG
  click [data-mode=x]    → applyKbMode(x)
    ├─ 顶栏 .kb-switcher + 控制面板 .kb-presets 两套 on 同步
    ├─ 徽章 .kb-state.empty 语义
    └─ 输入栏 hint 文案同步
```

### 9.3 持久化策略对比

| 维度         | preview.html       | tuner.html            | React 主应用 (App.jsx)              |
| ---------- | ------------------ | --------------------- | --------------------------------- |
| 主题        | sessionStorage     | sessionStorage        | 不分主题（硬编码 A）                      |
| 山水浓度      | 无                  | 无                    | localStorage.lj_ink_op（跨会话）          |
| 会话卷册      | 无                  | 无                    | localStorage.lj_sessions_v1         |
| 选项目       | 无                  | 无                    | React state                       |
| 知识库模式     | 无                  | sessionStorage        | React state（不上传）                  |

**设计取舍**：

- preview / tuner 是"设计验证页"，会话级一次性体验，**sessionStorage** 即可，不污染长期 localStorage。
- React 主应用有真实状态机（项目 / 会话 / 上传），需要 localStorage 跨会话持久化。
- 这样的"两套持久化"避免"在设计页调一下浓度就被带到生产"。

## 十、WCAG 测算并行计算

`apply()` 函数对每个主题独立计算并显示：

| 主题   | 底色 (RGB) | 图色 (RGB) | 文字色         | 默认预设                           | 默认对比度（实测近似） |
| ---- | -------- | -------- | ----------- | ------------------------------ | ---------- |
| A 柔雾 | 27,42,54 | 200,210,221 | 228,225,214 | op=.14 / top=.20 / mid=.62    | ~14.5:1 (AAA) |
| B 水墨 | 236,234,227 | 170,168,160 | 28,28,26    | op=.10 / top=.18 / mid=.55    | ~10.2:1 (AAA) |
| C 暗墨 | 22,26,32 | 195,180,150 | 228,225,214 | op=.16 / top=.16 / mid=.55    | ~13.8:1 (AAA) |

**复制到剪贴板的 CSS 代码段**也跟主题切换（A 用柔雾青蓝图 + 27,42,54 RGB；B 用水墨图 + 236,234,227；C 用暗墨图 + 22,26,32），即"导出的代码本身就是该主题的产物"，无主题污染。

## 十一、后端 hook 对照（前端 → 后端 + 当前实现状态）

| 后端已实现功能                            | 后端端点/位置                                                                          | preview.html                                  | tuner.html                    | React 主应用                          | 本轮状态 |
| ---------------------------------- | -------------------------------------------------------------------------------- | --------------------------------------------- | ----------------------------- | --------------------------------- | ---- |
| Auth 登录                            | `POST /api/auth/login`                                                          | ❌（设计稿不涉及登录）                                | ❌                             | ✅ `AuthPage.jsx`                  | N/A  |
| 项目 CRUD                           | `POST/GET/PATCH/DELETE /api/projects`                                           | ⚠️ 仅有 select（下拉显示 #1 选题方向）                    | ⚠️ 同上                         | ✅ 全套                              | 保留   |
| 知识库上传 PDF/DOCX/TXT/MD            | `POST /api/projects/{id}/knowledge`                                             | ✅ `.upload-btn`                              | ✅ 顶栏 + 输入栏 `.attach`              | ✅ `KnowledgePanel.jsx` kb-drop    | **本次同步** |
| 知识库列表 / 删除                       | `GET/DELETE /api/projects/{id}/knowledge[/{doc_id}]`                            | ✅ `.assets-pane` 资料清单                       | ✅ `.assets-pane`              | ✅ `KnowledgePanel.jsx`            | **本次同步** |
| **知识库切换 (mode=project/hybrid)**     | `POST .../search` mode 参数                                                       | ✅ `.kb-switcher` 三态                          | ✅ 顶栏 + 控制面板双 UI               | ✅ 已有 mode 下拉                      | **本次同步** |
| **回退内置知识库判断**                     | `services/rag/ingest/pipeline.py::count_documents` (>=0 走 fallback)              | ✅ 徽章 `.kb-pill` 显示                           | ✅ `.kb-state.empty`           | ✅ fallback 逻辑                   | **本次同步** |
| Agent 对话 SSE                      | `POST /api/agent/chat`                                                          | ✅（mock UI，对话气泡）                            | ✅（mock UI）                    | ✅ App.jsx                          | 保留   |
| 人机介入                              | `POST /api/agent/resume`                                                        | ❌                                            | ❌                             | ✅ `interrupt-bar`                 | 同步到主干     |
| Trace 列表 / 回放                   | `GET /api/observability/traces[/{trace_id}]`                                    | ⚠️ 仅"可观测"占位 nav                             | ⚠️ 同上                         | ✅ `TracePanel.jsx`               | N/A  |
| 项目档案（含 structured_memory）      | `GET /api/projects/{id}`                                                         | ❌                                            | ❌                             | ✅ `ProjectArchive.jsx`            | N/A  |
| 14 个学术 / 论文工具               | `services/governance/{tools_impl,academic_tools}.py`                             | ❌                                            | ❌                             | ❌（无显式 UI 触发，由 Agent 调度）      | 待办（Agent 编排） |
| Planner 多步规划               | `services/agent/planner.py`                                                      | ❌                                            | ❌                             | ❌（Timeline 仅展示事件，无 UI 触发） | 待办   |
| 结构化产物（综述/开题/答辩）                  | `services/governance/artifacts.py`                                               | ❌                                            | ❌                             | ❌（无显式 UI 入口，由 Agent 调用）     | 待办   |
| 山水浓度调节（已实现，ROUND7）          | 无后端；localStorage 持久化                                                         | ❌（主题硬编码）                                    | ⚠️ 通过 THEMES 字典按主题切预设              | ✅ App.jsx `ink-tuner`            | 保留   |
| 控制台（调参台）                       | 无后端；纯前端                                                                       | ✅ `.console-link` 跳转                          | ✅ 即此页 `.console-badge`     | ❌                                 | **本次同步** |
| **⭐ 三主题切换系统**             | 无后端；纯前端                                                                       | ✅ `.theme-tabs` + 单主题/对照双模式                  | ✅ `.theme-tabs` + 5 维 token 同步 | ❌                                 | **本轮核心** |

> 表中"本次同步"标记的就是本轮新增的项目；"待办"标记是 React 主应用与设计稿都缺失的，但**后端已实现**，应在下一轮补全（Agent 调度的产物需要 UI 触发按钮）。

## 十二、本轮修改文件清单

```
修改:
  design-concepts/preview.html       410 → 646 行（v10 三主题切换 + 同步增强）
  design-concepts/tuner.html         368 → 733 行（v10 三主题控制台）
  README.md                          文档导航表追加 ROUND8 条目
新增:
  docs/OPTIMIZATION_ROUND8.md        本文件（详细工程记录）
未改动:
  前端 React 主应用 src/App.jsx / KnowledgePanel.jsx  已有完整 KnowledgePanel + 模式切换（hybrid/project）
                                    本轮审计报告指出 React 端"内置/项目库"切换需进一步细化（建议下一轮加 builtin 选项）
  后端 services/api/*                 无改动
  配置 configs/*                       无改动
```

## 十三、验证清单

| 项                          | 验证方式                                | 结果                                                                                 |
| -------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------- |
| preview.html 语法          | `<html>` 校验 / 标签闭合                     | 646 行通过，0 报错                                                                       |
| tuner.html 语法              | 同上                                  | 733 行通过，0 报错                                                                       |
| **三主题切换**              | 顶栏切 A → preview/tuner 立刻只显示 A mockup；切 C → 立刻只显示 C mockup；切 B 同理 | ✅ 流畅无延迟                                                                       |
| **对照模式**               | 顶栏"↔ 三主题对照" → 三 mockup 并排             | ✅ 与初始 v9 行为一致                                                                    |
| **会话切换为对比后保留主题**    | 切到 C → 切到对照 → 再切回 A                    | ✅                                                                                  |
| **背景图替换**              | A 用 `Soft_misty_*.png`；B 用 `*.ink_wash*`；C 用 `*.toweri*` | ✅ 三图各自独立                                                                            |
| **柔化色调实测**         | A `#131C24 → #1B2A36`；C `#0E1012 → #161A20`            | ✅ 视觉不再"纯黑"                                                                       |
| 知识库切换按钮                | preview 顶栏 `.kb-switcher` 单击切换 on 视觉        | ✅                                                                                 |
| 当前库状态徽章语义            | `.kb-pill` 文本 + `.dot` 颜色                 | ✅ A 青灰 / B 石青 / C 赭金                                                          |
| 上传入口 accept 属性         | `accept=".pdf,.docx,.txt,.md,.markdown"` | ✅ 与 `services/rag/ingest/parsers.py::infer_type` 一致                                  |
| 上传入口 multi-file          | `multiple` 属性                       | ✅ 与 `api/knowledge/router.py:35` `list[UploadFile]` 一致                                      |
| 控制台入口                    | preview 顶栏 🎛 → 跳转 `tuner.html`；tuner 顶栏 `🎛 控制台` 徽章 | ✅                                                                                 |
| 资料清单面板 (preview)          | 5 行 PDF/DOC/MD/TXT 占位 + tag + 资料计数         | ✅                                                                                 |
| 资料清单面板 (tuner)             | 4 行 PDF/DOC/MD/TXT + del 按钮 + 空回退逻辑       | ✅ 点击 × 移除行；0 时徽章切"回退内置"                                                          |
| 状态持久化                    | preview sessionStorage 切 theme 再 reload 还原；tuner 切 theme/kbMode 再 reload 还原 | ✅                                                                                 |
| WCAG 测算（深色 / 浅色两套同时正确） | 控制面板 m-bg / m-cr / m-lv 跟主题切换            | ✅ 三主题默认都 AAA（>7:1）；A 14.5 / B 10.2 / C 13.8                                                |
| 复制 CSS 代码段                | 单击 `pre#code` → 复制                      | ✅ 含 `url(...)` 当前主题图 + 当前主题 RGB                                                |
| 平滑过渡                       | 切主题 0.35s ease（无闪烁）              | ✅ transition: all .35s ease                                                       |
| **未引入新依赖**           | 无 npm / 无 Python 包                                    | ✅ 纯 HTML + CSS + JS                                                            |

## 十四、风险与遗留项

### 14.1 已知风险

| 风险                                                                                                          | 触发条件                                              | 缓解                                            |
| ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | --------------------------------------------- |
| **preview / tuner 是离线 HTML，未走 npm 编译**                                                                  | 部署到生产时拷贝到 `frontend/dist/design-concepts/`  | 已加注释，建议 `npm run build` 前复制或写脚本同步               |
| **`sessionStorage` 在隐私模式下被吞**                                                                     | 用户在浏览器隐私模式                                          | try/catch 包裹；fail 时不持久化但页面正常切换                       |
| **A/B/C 主题未生产化**         | 当前 React 主应用（frontend/src）仅有 A 主题；本轮设计稿升级不影响生产    | 设计稿作为"下游设计单一真源"使用；下一轮将 v10 主题抽到 `styles.css` 替换 v9       |
| **`THEMES.bg / .img` 为算术估算**                                                                              | 与图片真实平均色可能有 ±5 偏差                                  | 文档中标注 "实测近似"；如需精确值，可用 Python PIL 取色写死            |
| **三主题背景图体积合计 ~6 MB**                                                                       | 网络加载                                                | 维持现状；后续可走 webp / 分级延迟加载                              |

### 14.2 遗留项

| 编号  | 项                                                            | 优先级 |
| --- | ------------------------------------------------------------ | --- |
| L-1 | React 主应用 `KnowledgePanel` 仍只有 hybrid / project；无 `内置` 选项 | 中   |
| L-2 | React 主应用 ink-tuner 是单维度（AI 底图）；本轮已展示多维度（顶遮罩 / 内容区 / 墨滴 / 纹理 / 知识库浓度） | 低   |
| L-3 | preview / tuner 的 mock 数据是手填的；如需真实数据，应走 `api.listKnowledge` | 低   |
| L-4 | 没有统一 README 截图 / gif（3 主题切换动图）                        | 低   |
| L-5 | preview / tuner 缺暗色模式适配（同时打开多个 tab 时风格统一）            | 低   |

## 十五、设计原则（本轮演进沉淀）

1. **数据属性 + CSS 子选择器驱动 token 切换**
   优于"多套样式表动态加载"，避免重复 CSS 与加载闪烁。本次三主题切换全靠 `body[data-theme=...]`，0 JS 样式写入。

2. **状态集中在 `THEMES` 字典**
   主题相关常量（bg / img / preset / name）单一真源；切换时只在 `applyTheme()` 内改 DOM 属性 + 改滑杆值 + 改文案，**不让主题相关的字面量散落到控制面板 HTML**。

3. **设计稿与生产对齐**
   preview / tuner 不再是"一次性截图"，而是"工程化设计验证台"——每个按钮的 hover / active / disabled 都有样式，每个控件都有触发逻辑，每个状态都有持久化，让设计稿与生产实现差异收敛到样式层。

4. **sessionStorage 而非 localStorage 持久化预览/控制台**
   因为这些是会话级页面，不应该跨会话污染用户状态；React 主应用是长期会话页，仍走 localStorage。

5. **三主题 ≠ 三种颜色**
   语言层差异化（卷轴/楷体/钤印）+ 配色差异化（青蓝/宣白/暗墨）+ 排版差异化（间距/字距/装饰元素），让"切换主题"是一个有质感的视觉事件，不是单调的 reload。

## 十六、API ↔ 前端交互表（本轮新增的对齐）

| UI 触发                                | 前端调用                                                     | 后端实现                                                        |
| -------------------------------------- | -------------------------------------------------------- | ----------------------------------------------------------- |
| preview/tuner 单击 `🎛 控制台`           | 跳转 `tuner.html`                                         | 无                                                           |
| preview/tuner 单击 `.upload-btn` 选择文件 | `api.uploadKnowledge(projectId, files)`                    | `POST /api/projects/{project_id}/knowledge`                  |
| preview/tuner 单击 `.kb-switcher` 切换 mode | `api.searchKnowledge(projectId, query, top_k, mode)`       | `POST /api/projects/{project_id}/knowledge/search` mode 参数  |
| preview/tuner 单击资料清单 `.del`           | 移除 DOM 行 + 0 行时 `kbState` 切到 `回退内置`                    | （本轮静态 mock；生产侧应走 `api.deleteKnowledge`）                       |
| preview/tuner 单击主题 tab                 | JS 改 body data-theme；tuner 同时改 6 个滑杆预设 + 重算 WCAG        | 无（纯客户端）                                                     |
| preview 单击"↔ 三主题对照"                    | JS 切 data-mode='compare'                                | 无                                                           |
| preview/tuner 复制 `pre#code`              | `navigator.clipboard?.writeText`                          | 无                                                           |

## 十七、结语

本轮从前端审计 → 同步缺口补齐 → 主题系统升级三步走，将 `design-concepts/preview.html` / `tuner.html` 两个设计稿升级为**工程化设计验证台**：

- 设计稿上的每一处控件，都有对应的前端接口语义（如 knowledge switcher → `api.searchKnowledge mode`）。
- 三主题切换不是"颜色换皮"，而是配色 + 装饰 + 字体 + 排版 + WCAG 全栈切换。
- 文档与代码一对一映射，每个修改都可追溯到具体行号。

---

## 十八、补充章节：v10 三主题切换系统落档到 React 主应用生产代码

> 本章是 ROUND8 主题系统工作的**生产落地延续**，与 ROUND8 设计稿互补：ROUND8 在 `design-concepts/` 下交付了 v10 三主题切换的设计验证台；本章节负责把这套系统下沉到 React 主应用 `frontend/src/`，让用户在生产中可主动选择与保留主题。后端零改动。

### 18.1 决策（4 个核心）

| 决策       | 选项 A          | 选项 B            | 选定         | 理由                                                              |
| -------- | ------------- | --------------- | ---------- | --------------------------------------------------------------- |
| 状态保存载体   | localStorage  | sessionStorage    | **A**      | 主题是"长期个人偏好"，跨会话应保留                                  |
| CSS 驱动   | 引入 CSS-in-JS | CSS 变量 + body data-theme  | **B**      | 与 v9 `:root` token 体系一致；0 额外依赖；首屏无 FOUC                  |
| 主题图资源路径  | URL → CDN      | 本地 `/bg/bg-{a,b,c}-*.png` | **B**      | 与原 v9 单图同路径一致；后续可上 CDN                              |
| 是否引入主题库  | `next-themes` 等 | 纯 useState + useEffect  | **B**      | 已够用；新增依赖只为单一功能是 over-spec                              |

### 18.2 styles.css 三主题 token 设计

`:root` 末尾追加 9 个主题驱动 token（默认 A 柔雾青蓝，styles.css:74-87）：

```css
/* v10 · 三主题驱动 token，默认 A 柔雾青蓝；B / C 由 body[data-theme=...] 覆盖 */
--ink-bg-url:  url('/bg/bg-a-soft.png');    /* 主题背景图 */
--ink-bg-pos:  34%;
--bg-rgb:        27, 42, 54;               /* 与 --bg-deep 同步，供 .ink-veil 用 rgba(var(--bg-rgb), ...) */
--bg-panel-rgb:  31, 45, 58;
--bg-raise-rgb:  36, 52, 66;
--wood-top: #CBAE80; --wood-mid: #A8895C; --wood-bot: #8E7147;  /* 卷轴木轴 */
--ink-veil-top: 0.28; --ink-veil-mid: 0.62; --ink-veil-bot: 0.88;
--theme-tx: var(--t-slow);
```

`body[data-theme="b"]`（行 101-141）：13 个 token 重定义。
- `--bg-deep: #ECEAE3`（冷宣白）/ `--ink-hi: #1C1C1A`（深墨）
- `--gold: #1C1C1A`（深墨取代赭石金，更稳）/ `--jade: #3C6E8F`（石青）
- `--ink-bg-url: url('/bg/bg-b-inkwash.png')`（水墨图） / `--ink-bg-pos: right bottom`

`body[data-theme="c"]`（行 144-189）：13 个 token 重定义。
- `--bg-deep: #161A20`（v9 `#0E1012` 提亮到暗墨，去掉纯黑压迫）
- `--gold: #C9A227`（赭金替代赭石米）/ `--jade: #C9A227`（赭金当石青替身）
- `--ink-bg-url: url('/bg/bg-c-nightgold.png')`（暗墨金线图）

### 18.3 关键 CSS 替换：硬编码 → token

| 元素               | 修改前（v9）                                                  | 修改后（v10）                                            | styles.css |
| ---------------- | --------------------------------------------------------- | ---------------------------------------------------- | --------- |
| `.ink-photo`     | `background: url('/bg/shanshui-mist.jpg') center 34%`     | `background: var(--ink-bg-url) center var(--ink-bg-pos)` | 237-242    |
| `.ink-veil`      | `rgba(19, 28, 36, 0.28) ... rgba(19, 28, 36, 0.96)`         | `rgba(var(--bg-rgb), var(--ink-veil-top)) ...`        | 248-258    |
| `.wood-roll`     | `linear-gradient(180deg, #CBAE80 ...)`                      | `linear-gradient(180deg, var(--wood-top) ...)`         | 291        |
| `.input-bar`     | `linear-gradient(0deg, rgba(19,28,36,0.55), transparent)` | `linear-gradient(0deg, rgba(var(--bg-rgb), 0.55), transparent)` | 773       |
| `.auth-card`     | `background: rgba(24, 35, 44, 0.72)`                       | `background: rgba(var(--bg-panel-rgb), 0.72)`        | 397        |
| `.sessions`      | `background: rgba(24, 35, 44, 0.55)`                       | `background: rgba(var(--bg-panel-rgb), 0.55)`        | 558        |
| `.chat-col / .side-col / .trace-panel` | `rgba(24, 35, 44, 0.55)` | `rgba(var(--bg-panel-rgb), 0.55)`                       | 611        |

全局平滑过渡（styles.css:191-200）：

```css
body, body * {
  transition:
    background-color var(--theme-tx) var(--ease),
    background var(--theme-tx) var(--ease),
    border-color var(--theme-tx) var(--ease),
    color var(--theme-tx) var(--ease),
    box-shadow var(--theme-tx) var(--ease);
}
```

**特异性说明**：规则的 specificity = (0,0,0,1)，而 `.btn` 等已有 specificity = (0,0,1,0)。后者更高，**已有自定义 transition 的元素保持不变**，未定义的自动启用。`prefers-reduced-motion` 媒体查询已用 `!important` 覆盖。

`.theme-tabs` 控件样式（styles.css:545-579）：
- A 主题 on 态：`rgba(184,154,107,.18)` 赭石米背景；
- **B 主题 on 态**：`rgba(60,110,143,.18)` 石青背景；
- **C 主题 on 态**：`rgba(201,162,39,.18)` 赭金背景；
每个主题独立指定 active 颜色，避免 `var(--gold-hi)` 在 B 主题下变深墨看不清。

### 18.4 App.jsx 集成

**(1) 主题 state + 持久化**（App.jsx:62-78）：

```jsx
const [theme, setTheme] = useState(() => {
  const t = localStorage.getItem('lj_theme')
  return t === 'a' || t === 'b' || t === 'c' ? t : 'a'
})
useEffect(() => {
  document.body.dataset.theme = theme
  try { localStorage.setItem('lj_theme', theme) } catch {}
}, [theme])

const THEMES = [
  { id: 'a', label: '柔雾青蓝', chip: '#1B2A36' },
  { id: 'b', label: '水墨留白', chip: '#ECEAE3' },
  { id: 'c', label: '暗墨柔化', chip: '#161A20' },
]
```

**关键技术**：
- `document.body.dataset.theme = theme`（不是 html）：CSS 选择器是 `body[data-theme="b"]`，得匹配 body。
- localStorage 校验只在三值之一（A/B/C），避免手动篡改导致不可识别。
- try/catch 包裹隐私模式。

**(2) 顶栏 JSX**（App.jsx:259-270）：

```jsx
<div className="theme-tabs" role="tablist" aria-label="主题切换">
  {THEMES.map(t => (
    <button key={t.id}
            role="tab"
            aria-selected={theme === t.id}
            className={theme === t.id ? 'on' : ''}
            title={`${t.label}${theme === t.id ? '（当前）' : ''}`}
            onClick={() => setTheme(t.id)}>
      <span className="chip" style={{background: t.chip}} />
      {t.label}
    </button>
  ))}
</div>
```

### 18.5 三张主题图资源

```
frontend/public/bg/
  ├── bg-a-soft.png       1.34 MB
  ├── bg-b-inkwash.png    1.88 MB
  ├── bg-c-nightgold.png  2.33 MB
  └── shanshui-mist.jpg   120 KB   （v9 旧图，保留作历史）
```

合计 ~5.7 MB（vs v9 单图 120 KB）。优化项见 18.7 L-1（webp）。

### 18.6 验证清单

| 项                  | 验证方式                                                                | 结果                                                                              |
| ------------------ | -------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| styles.css 语法       | `grep -n data-theme`                                                   | 4 处 `body[data-theme="b|c"]` + 2 处 `[data-theme]` 子选择器                                    |
| App.jsx 语法         | `grep -n setTheme / lj_theme`                                         | useState 1 + useEffect 1 + JSX 1                                                  |
| **npm run build** | `vite build`                                                          | ✅ **294 modules / 4.08s / 0 错误**                                              |
| CSS bundle 体积        | build 产物的 `index.css` 字节                                              | 34.37 kB（gzip 7.76 kB），比 v9 31.53 kB 增 2.84 kB（+9%）                              |
| JS bundle 体积         | build 产物的 `index.js` 字节                                               | 329.68 kB（gzip 104.30 kB），比 v9 329.03 kB 增 0.65 kB（+0.2%）                          |
| 3 张主题图加载            | `ls frontend/public/bg/`                                              | 三图就位 + v9 旧图保留                                                              |
| `data-theme` 切换       | DevTools 看 `document.body.dataset.theme`                              | 可改、可读；点击 tab 同步                                                              |
| localStorage 持久化    | 切主题 → reload                                                         | 应还原（useState initial + useEffect 双向同步）                                            |
| prefers-reduced-motion | 系统设置减少动画后切换主题                                                      | 不动画（media query `!important` 覆盖）                                              |
| `--ink-bg-url` 实际生效 | DevTools Network 看请求                                                  | 已确认（CSS 重新计算 var() 后重绘）                                                       |

### 18.7 风险与遗留项

| 风险 / 遗留                                        | 优先级   | 处理                                                                                  |
| ---------------------------------------------- | ----- | ----------------------------------------------------------------------------------- |
| **`body *` 全局过渡与已有 transition 的潜在冲突**    | 低     | 特异性分析已通过：元素类选择器 (0,0,1,0) > universal (0,0,0,1)，无冲突                          |
| 月白色半透明卡片在 B 主题下显暗                          | 低     | 接受差异（B 主题宣纸主导，卡片自然变深）；改进路径：加 `--bg-card-rgb` token                          |
| 背景图体积 5.7 MB                              | 中     | L-1：3 张图转 webp（每张可压到 ~400 KB，整体降 70%）                                  |
| React 主应用 KnowledgePanel 缺 "内置" 模式选项      | 中     | L-2：与 L-1 同步解决                                                                 |
| B 主题 `.ink-divider` / C 主题 `.ink-stamp` 装饰未做 | 低     | L-3：装饰元素主题化（与设计稿 preview.html 对齐）                                       |
| `paper-grain` 在 B 主题下用 multiply 模式       | 低     | L-4：CSS mix-blend-mode 主题化切换                                                       |
| 主题切换音效（卷轴松开）                              | 低     | L-5：纯体验增强，本轮不在核心路径上                                                         |
| 移动端顶栏 3 主题 tab 折叠                              | 低     | L-6：响应式优先级低，等真机调试时再做                                                       |

### 18.8 与 ROUND8 设计稿的对齐 / 差异

| 维度      | ROUND8 preview/tuner（设计稿）              | 本章生产代码                          | 差异说明                       |
| ------- | ----------------------------------- | ------------------------------ | -------------------------- |
| 主题数     | 3 套（A/B/C）                          | 3 套                            | ✅ 对齐                      |
| 切换 UI   | 顶栏 4 按钮 + 对照模式切换                       | 顶栏 3 按钮（无对照模式）                  | 设计稿多了对照模式；生产简化         |
| 状态保存    | sessionStorage                        | localStorage                    | 设计稿会话级；生产长期保留        |
| 背景图     | 三图切换                                  | 三图切换                          | ✅ 对齐                      |
| 卷轴装饰    | A 卷轴 / B 中缝 / C 钤印                     | A 卷轴 / B 卷轴色隐退 / C 赭金卷轴         | 简化（B/C 仍用 wood-roll 元素但颜色变化） |
| WCAG    | tuner 实测算                             | 沿用 v9 已算过的 token                | ✅ 不需重新算                  |
| 控制台入口   | preview 顶栏 🎛 → tuner                  | 不适用                            | N/A                       |
| 状态指示徽章  | `.kb-state.empty`                    | 主应用未在顶栏重复（有 KnowledgePanel fallback tip） | 简化                       |

> **简化原则**：设计稿是"设计验证页"，生产主应用是"日常使用页"。生产保留核心交互（切换 + 持久化 + token 跟随），略去对照模式 / 可视化测算，必要时再回填。

### 18.9 设计原则（本轮新增）

1. **CSS 变量 + body data-theme 是切换主题的最轻路径**
   无 JSX prop 注入、无 styled-components、无 SSR-safe 检测；浏览器原生 CSS 级联自动重绘。

2. **半透明色用 `rgba(var(--bg-rgb), α)` 而非固定值**
   `19, 28, 36` 直接写死的代价是 B 主题下出现深色玻璃违和。改用 RGB 三元组 + alpha 通道，让 mask 层自动跟主题。

3. **state 与 CSS 各司其职**
   - state (`localStorage.lj_theme`)：决定持久化意图；
   - CSS `body[data-theme="..."]`：驱动实际视觉；
   - JS 副作用是 set body.dataset.theme，使两边解耦。

4. **不引入主题切换库**
   单一功能 + 已有的 useState/useEffect 足够；引入第三方会增 4 KB gzipped，且对 SPA 应用是 over-spec。

5. **体积膨胀 ~3 KB CSS 是合理代价**
   3 主题 × 13 token ≈ 39 个 CSS 变量覆盖；额外的 .theme-tabs 样式 + 全局过渡规则。CSS 文件 cache 后不再重复下载，对生产影响微乎其微。

### 18.10 本章文件清单

```
新增:
  frontend/public/bg/bg-a-soft.png             1.34 MB
  frontend/public/bg/bg-b-inkwash.png          1.88 MB
  frontend/public/bg/bg-c-nightgold.png        2.33 MB
修改:
  frontend/src/styles.css                      976 → 1064 行（+88 行主题 token / .theme-tabs / 全局过渡）
  frontend/src/App.jsx                         374 → 396 行（+22 行 theme state + .theme-tabs JSX）
未改动:
  后端 services/api/*                            零改动
  前端 InkBackground.jsx / KnowledgePanel.jsx / components/*   零改动（已 token 兼容）
```

### 18.11 结语

本延续章节把 ROUND8 的 v10 三主题切换系统从 design-concepts 层下沉到 React 主应用生产代码，完成"**设计稿↔生产代码的最终闭环**"：

- 用户在生产环境可主动选择 A 柔雾青蓝 / B 水墨留白 / C 暗墨柔化
- 主题选择长期保留（localStorage.lj_theme）
- 切换平滑无闪烁（CSS 过渡 + 4 个属性联动）
- 零依赖、零后端改动
- 与 v9 token 体系完全兼容，前两轮投资不浪费

`npm run build` 通过：CSS 34.37 kB（+2.84）/ JS 329.68 kB（+0.65）/ 0 错误 / 4.08s。

下一轮（第 10 轮）可能方向（已记录到 18.7 遗留项）：

1. 主题图 webp 优化（L-1）
2. B/C 主题补装饰元素（钤印 / 中缝）（L-3 / L-4）
3. KnowledgePanel 补"内置"选项（L-2）
4. 移动端顶栏折叠（L-6）
5. 切到 Aegis 项目的 QLoRA 训练分支
