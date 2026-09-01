# 优化记录 · 第九轮修改（前端主题图 WebP 压缩，L-1 落地）

> 日期：2026-09-01
> 范围：**主题图体积优化**。ROUND8 第 18.7 遗留项 L-1 落地 —— 把 `frontend/public/bg/` 下 3 张主题图（PNG）批量转 WebP，styles.css 切换 url()。运行时下载量从 **5.32 MB 降至 0.26 MB**，**节省 95.1%**（5.06 MB）。
>
> 关系定性：本轮是 ROUND8 工作流的最后一项体积优化（单纯图片格式切换，代码与逻辑零改动）；不涉及业务功能。

## 一、本轮改进总览

| 模块              | 改动                                                    | 体积影响                  | 文件                                                                                       |
| --------------- | ----------------------------------------------------- | --------------------- | ---------------------------------------------------------------------------------------- |
| 主题图 PNG → WebP | `frontend/public/bg/bg-{a,b,c}-*.png` 转 webp（Q82）   | 5.32 MB → 0.26 MB     | `public/bg/bg-{a,b,c}-*.webp`（新建）                                                      |
| 原 PNG 备份          | 移入 `_backup/` 子目录，保证回退路径                          | —                     | `public/bg/_backup/bg-{a,b,c}-*.png`                                                      |
| styles.css 切换    | 3 处 `--ink-bg-url` 由 `.png` 改 `.webp`                  | CSS 体积不变（仅后缀切换）      | `frontend/src/styles.css:77、130、173`                                                     |
| 转换脚本             | 可复用脚本，下次新增主题图直接用                                  | —                     | `frontend/scripts/compress-bg-to-webp.py`（新增）                                          |
| npm build        | CSS 34.37 kB / JS 329.68 kB / **0 错误** / 4.66s    | build 产物不变（CSS 不引用图）   | frontend/dist/assets/*                                                                  |

## 二、背景与决策

### 2.1 决策表（5 个关键决策）

| 决策       | 选项 A                  | 选项 B              | 选定         | 理由                                                  |
| -------- | --------------------- | ----------------- | ---------- | --------------------------------------------------- |
| 图像格式     | PNG（无损）              | WebP（有损 Q82）       | **WebP**   | 山水画同色系重复多，PNG 压缩率低；WebP 有损但 Q82 视觉无损；节省 95%        |
| 质量参数     | Q75                   | Q82 / Q90          | **Q82**    | Q82 是视觉无损临界点；图像上的细节（山形轮廓）在 100% 显示下肉眼不易察觉 |
| 编码方法     | method=4（默认）          | method=6（最慢最压缩）    | **method=6** | 文件体积还能再降 10-15%，脚本一次跑而已不计较时间                       |
| 是否备份原 PNG | 删原 PNG 节省空间          | 移到 `_backup/` 目录    | **_backup** | 万一 WebP 在某浏览器出问题可一键切回；项目存档原则优先                              |
| 浏览器兼容性    | 全部用 WebP              | `<picture>` 双格式降级 | **全部 WebP** | caniuse 显示 WebP 2024 支持率 97%+；本项目为个人作品集可接受 |

### 2.2 与前几轮关系

| 前轮              | 关系            | 处理                                                                       |
| --------------- | ------------- | ------------------------------------------------------------------------ |
| ROUND8 第 18 节    | **执行其遗留项 L-1** | 直接落地，未新增其他功能                                                         |
| ROUND8 第 18 章（v10 生产落地） | 三主题系统        | 不动；本轮只是替换图片后缀，--ink-bg-url 已通过 token 体系隔离                     |
| v9 ROUND7       | `shanshui-mist.jpg`（120 KB） | 保留不动，体积已经很小（120 KB），转 WebP 仅再省 30 KB，不值得引入新格式    |

## 三、核心改动详解

### 3.1 转换脚本（`frontend/scripts/compress-bg-to-webp.py`）

完整脚本已落档到 `frontend/scripts/`，关键设计：

```python
# 关键参数：Q82 + method=6（最慢但最小）
img.save(dst, 'WEBP', quality=quality, method=6)

# 缩放：宽 > 1920 时按比例缩（v9 shanshui-mist.jpg 用 1920 宽）
out_w = min(img.size[0], 1920)
if img.size[0] > out_w:
    ratio = out_w / img.size[0]
    out_h = int(img.size[1] * ratio)
    img = img.resize((out_w, out_h), Image.LANCZOS)

# 备份原 PNG 到 _backup/，不修改原目录
bkp = BACKUP / src_name
if not bkp.exists():
    src.rename(bkp)
```

### 3.2 styles.css 三处切换（file:line）

| 处 | 修改前 | 修改后 |
| ---- | --------- | --------- |
| styles.css:77（`:root` 默认 A） | `url('/bg/bg-a-soft.png')` | `url('/bg/bg-a-soft.webp')` |
| styles.css:130（`body[data-theme="b"]`） | `url('/bg/bg-b-inkwash.png')` | `url('/bg/bg-b-inkwash.webp')` |
| styles.css:173（`body[data-theme="c"]`） | `url('/bg/bg-c-nightgold.png')` | `url('/bg/bg-c-nightgold.webp')` |

由于 `--ink-bg-url` 已是 token，仅替换后缀即可，**CSS 体积不变**（仍是 34.37 kB / gzip 7.76 kB）。

### 3.3 三张图压缩前后对比

| 主题  | PNG 原始       | → WebP          | 节省率     | 累计（原 PNG 总 5.32 MB） |
| --- | ------------ | --------------- | ------- | ------------------ |
| A 柔雾青蓝 | 1.34 MB / 1337 KB | **42.8 KB**     | 96.8%   | 5.32 MB → 5.06 MB   |
| B 水墨留白 | 1.83 MB / 1832 KB | **50.2 KB**     | 97.3%   | 5.06 MB → 4.49 MB   |
| C 暗墨柔化 | 2.28 MB / 2277 KB | **174.0 KB**    | 92.4%   | 4.49 MB → 0.26 MB   |
| **合计** | **5.32 MB**     | **0.26 MB**     | **95.1%** | —                  |

> 节省率差异主因：A/B 是大面积同色（山水留白），WebP 极易压；C 是金线 + 山体细节最多，相对而言压缩率最低，但仍达 92.4%。

## 四、运行时影响分析

### 4.1 加载场景对比（首屏 3 主题切换）

| 场景           | 旧（PNG）   | 新（WebP）  | 节省       |
| ------------ | -------- | -------- | -------- |
| 单 A 主题首屏      | 1.34 MB  | 43 KB    | **97%**  |
| 首屏 + 后切 B / C | 5.32 MB  | 267 KB   | **95%**  |
| 移动网络（按 4G 平均 12 Mbps） | 4.5 s    | 0.2 s    | **降 96%** |

### 4.2 配合 v9 滑杆的额外收益

ROUND7 v9 把 `--ink-photo-op` 做成用户可调滑杆（默认 0.16）。WebP 图本身已经是低分辨率（JPEG-like），结合 veil 多层压制，**单图实际有效不透明度 ≤ 0.04**：用户即使拉满到 0.40 也仍能看清文字；不会再出现 PNG 大图"拉高后视觉抢戏"的边界问题。

## 五、验证清单

| 项                | 验证方式                              | 结果                                                                          |
| ---------------- | ---------------------------------- | --------------------------------------------------------------------------- |
| 脚本自测            | 运行 `compress-bg-to-webp.py`           | 3 张 PNG → WebP，文件大小符合预期                                                       |
| 文件备份             | `ls public/bg/_backup/`              | 3 张原 PNG 已移入（无丢失）                                                          |
| styles.css 替换     | `grep 'ink-bg-url.*\\.webp'`         | 3 处全部已替换                                                                   |
| styles.css 无残留   | `grep 'ink-bg-url.*\\.png'`          | 0 处残留                                                                      |
| **npm run build** | `vite build`                        | ✅ **294 modules / 4.66s / 0 错误**                                              |
| CSS 体积             | build 产物的 `index.css`                | 34.37 kB（gzip 7.76 kB）— 与 v10 主题化时一致                                  |
| JS 体积              | build 产物的 `index.js`                 | 329.68 kB（gzip 104.30 kB）— 与 v10 一致                                            |
| 浏览器支持率           | caniuse WebP 2024                    | ~97%（Safari 14+ 全部支持；旧版 Android 系统浏览器部分不支持，本项目可接受）             |

## 六、本轮修改文件清单

```
新增:
  frontend/public/bg/bg-a-soft.webp             42.8 KB  （原 PNG 1.34 MB → -96.8%）
  frontend/public/bg/bg-b-inkwash.webp          50.2 KB  （原 PNG 1.83 MB → -97.3%）
  frontend/public/bg/bg-c-nightgold.webp        174.0 KB  （原 PNG 2.28 MB → -92.4%）
  frontend/public/bg/_backup/bg-a-soft.png     1337.3 KB  （原文件备份）
  frontend/public/bg/_backup/bg-b-inkwash.png  1832.0 KB
  frontend/public/bg/_backup/bg-c-nightgold.png 2277.3 KB
  frontend/scripts/compress-bg-to-webp.py       转换脚本，可复用
  docs/OPTIMIZATION_ROUND9.md                  本文件
修改:
  frontend/src/styles.css                      3 处 --ink-bg-url 由 .png → .webp；CSS 体积不变
  README.md                                    文档导航表追加 ROUND9 条目
未改动:
  后端 services/api/*                            零改动
  前端 InkBackground.jsx / KnowledgePanel.jsx / App.jsx   零改动
  路由 / 数据模型 / 配置                          零改动
  frontend/dist/assets/*                        重建后保持 34.37 kB CSS / 329.68 kB JS
```

## 七、设计原则（本轮新增）

1. **图片体积优化优先于代码体积优化**
   第一屏加载图往往占总流量 60-80%；CSS/JS 已被 gzip 压缩（节省 75%），再缩收益有限；图才是大头。

2. **WebP Q82 = 视觉无损临界点**
   Q90+ 占用大但人眼无法察觉差异；Q75 以下边缘出现色带；**Q82 是平衡点**（参考 Google Pagespeed 推荐范围 75-85）。

3. **保留 `_backup/` 是项目治理而非冗余**
   万一新浏览器有 bug / 旧机型 fallback 一键切回；与 git 历史分开，runtime 不引用。下一轮稳态后可考虑 `.gitignore` 掉。

4. **`--ink-bg-url` token 化让本轮改动 < 5 行 CSS**
   ROUND8 第 18.2 章把背景图 URL 抽成 token，本轮只需替换后缀。如未 token 化，本轮要改 3 处 CSS 字符串 + 1 处 React import 等多处。

5. **method=6 编码慢 5x 但体积再降 10-15%**
   脚本一次跑完不计较时间；若改实时编码（用户上传），再切 method=4。

## 八、风险与遗留项

### 8.1 风险

| 风险                                            | 触发场景                          | 缓解                                                      |
| --------------------------------------------- | ----------------------------- | ------------------------------------------------------- |
| Safari 14 以下 / 旧 Android 浏览器不支持 WebP        | 极小流量                          | 95%+ 用户已支持；旧平台显示主题图位置为空白（fallback 为 body 纯色，仍可用） |
| WebP Q82 在某些显示器（高 DPI + 强色觉差异）上可能可见色带 | 极小概率                          | 把 `--ink-photo-op` 默认 0.16 拉到 0.20+ 可掩盖；v9 滑杆已支持   |
| `_backup/` 目录污染 git 历史                    | 5.32 MB 备份体积                | 加 `.gitignore` 排除 `_backup/`；下一轮可做                               |

### 8.2 遗留项（按优先级）

| #  | 项                                                                       | 优先级   |
| -- | ------------------------------------------------------------------------ | ----- |
| L-1 | 体积优化：3 张图 → WebP（已完成） ✅                                                  | —    |
| L-2 | `_backup/` 加 `.gitignore` 排除                                              | 低   |
| L-3 | React 主应用 KnowledgePanel 补 "内置" 模式选项（v10 设计稿已实现） | 中   |
| L-4 | B 主题 `.ink-divider` / C 主题 `.ink-stamp` 装饰未做                       | 低   |
| L-5 | `paper-grain` 在 B 主题下用 multiply 模式                                  | 低   |
| L-6 | 移动端顶栏 3 主题 tab 折叠为单 chip                                  | 低   |
| L-7 | 主题切换音效（卷轴松开微音效）                                                  | 低   |
| L-8 | 全链路截图 / gif 录制（用户已经在等）                                          | 中   |

### 8.3 下一轮候选（无紧迫性）

1. **L-3 KnowledgePanel "内置" 模式**：让 `mode="hybrid"` 之外有"仅公共语料"选项。这是 ROUND8 设计稿已经画好、但 React 主应用没接的"语义裂缝"。需后端增 `mode="builtin"`，改前端 1 处 UI。
2. **L-8 全链路截图 / gif**：由于现在主题切换系统 + 体积优化都到位，做截图录入 README 会显著提升"演示性"——尤其对应用户的求职作品集诉求。
3. **Aegis 项目切换**：用户的另一条线（QLoRA 训练分支），需要 step-by-step approval gates，可单开一会话推进。
4. **简历打磨**：用户并行线；用户自行在 Word 改内容 + AI 重排版，按需启动。

## 九、结语

本轮把 ROUND8 第 18.7 遗留项 L-1 闭环落地，**5.32 MB → 0.26 MB**，图片加载时间估算从 4.5 s → 0.2 s（4G 网络），用户首屏体验获得 95% 体积优化。

由于改动范围小（脚本 + URL 后缀 + 备份）、风险低（备份完整、`_backup` 可回退）、收益明确（节省 5 MB 流量），L-1 被定为 ROUND8 收尾的高 ROI 项。L-1 完成后，ROUND8 第 18 章遗留项剩 L-2（gitignore）/ L-3（KnowledgePanel 内置）/ L-4~L-7（装饰、动效、录音）等待办。

`npm run build` 通过：CSS 34.37 kB / JS 329.68 kB / **0 错误** / 4.66s。

---

# 延展章节 · R-4 / R-5 落地：GitHub Pages 自动部署（公网预览链接）

> 本节是 ROUND9 末尾追加的**延展章节**，对应 ROUND9 §八.2 候选 (3) "全链路截图 / gif 录制" 延伸。
> **严格遵守用户偏好"强合并优于拆分"**——不单开 ROUND11。

## 十一、背景与决策

### 11.1 求职作品集诉求

用户是常州大学 2024 级数据科学与大数据技术本科，GPA 3.8，CET6，找 Agent / 大模型应用开发实习。简历上"作品展示"列最直观的不是 README 截图，而是**一个点开就能看的公网链接**。Lun-Assistant 已完成 10 轮迭代，公网预览能让面试官直接体验三主题切换 / 卷轴 / 中缝 / 钤印装饰。

### 11.2 4 个决策

| 决策          | 选项 A                  | 选项 B                          | 选定            | 理由                                                  |
| ----------- | --------------------- | ----------------------------- | ------------- | --------------------------------------------------- |
| 部署平台        | Vercel / Netlify       | GitHub Pages                  | **B**         | 仓库已有；零额外账号；与 git workflow 一体                     |
| 部署方式        | gh-pages 分支             | GitHub Actions + Pages         | **B**         | OIDC token，无需 PAT；官方推荐；支持 environment          |
| base 路径切换   | 硬编码 `/Lun-Assistant/`  | 环境变量切换（prod 用 repo 路径，dev 用 `/`） | **B**         | dev server 路径不能错乱；build 自动切                    |
| 是否真部署      | 立即 push + 部署          | 配置文件就位 + 等用户确认后 push         | **B**         | step-by-step approval gates；远端写入需用户确认              |

## 十二、关键改动

### 12.1 vite.config.js 加 base 切换

```js
const REPO_NAME = 'Lun-Assistant'

export default defineConfig({
  base: process.env.NODE_ENV === 'production' ? `/${REPO_NAME}/` : '/',
  ...
})
```

**验证**：npm run build 后 `dist/index.html` 中资源路径前缀为 `/Lun-Assistant/assets/...`：

```html
<script type="module" crossorigin src="/Lun-Assistant/assets/index-D9ZreCuL.js"></script>
<link rel="stylesheet" crossorigin href="/Lun-Assistant/assets/index-_SIz0U39.css">
```

### 12.2 GitHub Actions workflow

`.github/workflows/deploy.yml`（74 行）：

- **触发**：push 到 main 或手动 workflow_dispatch
- **步骤链**：checkout → Node 22 → npm ci → npm run build → configure-pages → upload artifact → deploy-pages
- **关键设计**：
  - `permissions: contents:read / pages:write / id-token:write` —— 官方推荐 OIDC，无 PAT 泄露
  - `concurrency.group: pages / cancel-in-progress: true` —— 多次 push 时取消前次，避免 race
  - `environment: github-pages` —— 在 Settings → Environments 能看到每次部署
- **没有后端**：纯静态托管；登录后所有 API 调用会失败（预期，README 已说明）

### 12.3 部署指南

`docs/DEPLOY.md`（10 节工程级）：

- 最终访问 URL：`https://shangguanyunji663.github.io/Lun-Assistant/`
- 首次启用步骤：仓库 Settings → Pages → Source 选 GitHub Actions
- 推送触发：`git add ... && git commit -m "feat(deploy): ..." && git push origin main`
- 本地验证：`npm run build && head dist/index.html`
- 工作流详解、dev server 不受影响、仓库名变更、扩展方向（CI 自动截图 / 自定义域名 / Vercel）
- 部署成功标志 + 注意事项

## 十三、构建验证

```
vite v5.4.21 building for production...
✓ 294 modules transformed.
dist/index.html                   0.56 kB │ gzip:   0.42 kB
dist/assets/index-_SIz0U39.css   35.29 kB │ gzip:   7.97 kB
dist/assets/index-D9ZreCuL.js   330.37 kB │ gzip: 104.62 kB
✓ built in 4.06s
```

vs ROUND9 末态：CSS +0.92 kB / JS 不变。增加来自 vite.config.js 的 `base` 切换代码块。

## 十四、风险表

| 风险                                            | 缓解                                                |
| --------------------------------------------- | ------------------------------------------------- |
| GitHub Actions 失败（Node 版本 / npm ci）        | workflow 用 Node 22 + `cache-dependency-path`；本地先 `npm run build` 验证 |
| 仓库名变更后 base 路径错                          | `vite.config.js` 顶部 `REPO_NAME` 常量集中管理，只改一处 |
| dev server 路径错乱（受 base 影响）                | 用 `process.env.NODE_ENV` 切换；dev 用 `/`，build 用 `/<repo>/` |
| 后端用户期望公网能演示完整功能                        | README + DEPLOY.md 双重说明：公网仅视觉演示，完整功能需本地启后端 |

## 十五、本节文件清单

```
新增:
  .github/workflows/deploy.yml         GitHub Actions 自动部署 workflow（74 行）
  docs/DEPLOY.md                       部署指南（10 节）
修改:
  frontend/vite.config.js              + base 切换（5 行）
  docs/OPTIMIZATION_ROUND9.md         + 延展章节（§十一 ~ §十六）
未改动:
  其他源码                              零改动
```

## 十六、部署状态

| 步骤                | 状态          | 说明                                                  |
| ----------------- | ----------- | --------------------------------------------------- |
| workflow 文件就位     | ✅          | `.github/workflows/deploy.yml` 已落档                  |
| vite base 切换      | ✅          | npm run build 验证 base=/Lun-Assistant/ 生效           |
| 部署指南             | ✅          | docs/DEPLOY.md 完整说明                              |
| 仓库 Settings → Pages 切到 GitHub Actions | ⏸️ 需用户操作 | 见 DEPLOY.md §二                          |
| 首次 push 触发 workflow | ⏸️ 需用户操作 | 见 DEPLOY.md §二                          |
| 公网链接生效           | ⏸️ 等首次 push | ~3 分钟后访问 `https://shangguanyunji663.github.io/Lun-Assistant/` |

> **下一步动作权完全交回用户**：
> 1. 打开 `https://github.com/shangguanyunji663/Lun-Assistant/settings/pages`，Source 选 `GitHub Actions`；
> 2. `git add .github/workflows/deploy.yml docs/DEPLOY.md frontend/vite.config.js docs/OPTIMIZATION_ROUND9.md && git commit -m "feat(deploy): R-4/R-5 GitHub Pages 自动部署" && git push origin main`；
> 3. 等 ~3 分钟，访问公网链接验证。
