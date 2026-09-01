# 部署指南 · GitHub Pages 自动部署

> 这是 ROUND10 末尾扩展（求职作品集 R-4 + R-5 落地）的部署说明。改 `frontend/vite.config.js` 加 `base` 切换 + 写 `.github/workflows/deploy.yml` 实现 `main` 分支 push → 自动 build → 部署到 GitHub Pages。

## 一、最终访问 URL

推送 `main` 分支后 ~2-3 分钟生效：

```
https://shangguanyunji663.github.io/Lun-Assistant/
```

> 公网预览仅展示**前端视觉**（主题切换 UI / 装饰元素 / 配色 / 排版）。
> **不包含后端功能**（登录 / 对话 / 知识库检索需要本地启 FastAPI）。

## 二、首次启用 GitHub Pages（仓库管理员操作）

### 步骤 1：仓库 Settings → Pages

1. 打开 `https://github.com/shangguanyunji663/Lun-Assistant/settings/pages`
2. **Source**：选 `GitHub Actions`（不是 `Deploy from a branch`）
3. 保存

### 步骤 2：第一次 push 触发 workflow

```bash
cd /d/PythonProject/Lun-Assistant
git add frontend/vite.config.js .github/workflows/deploy.yml docs/DEPLOY.md
git commit -m "feat(deploy): R-4/R-5 GitHub Pages 自动部署 + vite base 切换"
git push origin main
```

### 步骤 3：等 ~3 分钟看 Actions

打开 `https://github.com/shangguanyunji663/Lun-Assistant/actions`：
- ✅ `Build & Deploy to GitHub Pages` 跑过 → 部署成功
- ❌ 失败 → 看 Actions 日志（通常是 Node 版本或 npm install 失败）

## 三、本地验证 build

push 前先本地验证 base 切换生效：

```bash
cd frontend
npm run build                                    # NODE_ENV=production, base='/Lun-Assistant/'
cat dist/index.html | head -20                    # 看 base href 和资源路径
```

预期输出片段：
```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>论匠 · LunJiang</title>
    <script type="module" crossorigin src="/Lun-Assistant/assets/index-CHkXvQaz.js"></script>
    <link rel="stylesheet" crossorigin href="/Lun-Assistant/assets/index-BtZ8KRsv.css">
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
```

所有资源路径都有 `/Lun-Assistant/` 前缀 → 在 GitHub Pages 上能正常解析。

## 四、工作流详解（`.github/workflows/deploy.yml`）

### 触发
- push 到 main 分支
- 或 Actions UI 手动 `workflow_dispatch`

### 步骤链
1. **Checkout** —— 拉 main 分支代码
2. **Setup Node 22** —— 装 Node.js v22 + cache npm
3. **Install deps** —— `npm ci` 装 frontend 依赖
4. **Build** —— `npm run build`（vite 自动用 `NODE_ENV=production` 切 base 到 `/Lun-Assistant/`）
5. **Setup Pages** —— GitHub 提供的 Pages 初始化
6. **Upload artifact** —— 把 `frontend/dist/` 上传为 Pages artifact
7. **Deploy** —— 部署 artifact 到 GitHub Pages

### 关键设计
- **不用 gh-pages 分支 / actions-gh-pages**：直接用官方 `actions/deploy-pages@v4` + `actions/upload-pages-artifact@v3`，更安全（OIDC token，无 write 权限泄露）
- **concurrency 控制**：`group: 'pages'` + `cancel-in-progress: true` —— 多次 push 时只跑最新的那次
- **环境**：`environment: github-pages` —— 在仓库 Settings → Environments 里能看到每次部署

## 五、dev server 不受影响

`vite.config.js` 的 base 切换只在 `NODE_ENV=production` 触发：

```js
base: process.env.NODE_ENV === 'production' ? `/${REPO_NAME}/` : '/',
```

- `npm run dev` —— `NODE_ENV=development`，base=`/`，路径与本地一致
- `npm run build` —— `NODE_ENV=production`，base=`/Lun-Assistant/`，适配 GitHub Pages

## 六、若仓库名变更（如改成 `lun-jiang`）

只需改 `frontend/vite.config.js` 的 `REPO_NAME` 常量：

```js
const REPO_NAME = 'lun-jiang'  // 改这里
```

不需要改 workflow。

## 七、未来扩展（可选）

| 方向                  | 价值                          | 工作量  |
| ------------------- | --------------------------- | ---- |
| GitHub Actions 跑截图脚本 | CI 自动验证 3 主题（节省手动截图）     | 中    |
| 加自定义域名             | `shangguanyunji663.github.io/Lun-Assistant` → `lun-jiang.shangguanyunji663.com` | 低    |
| Vercel / Netlify 部署   | 比 GitHub Pages 更快（CDN + Edge）+ 自动 preview PR | 中    |

## 八、注意事项

1. **后端不部署**：dist 是纯静态，登录后所有 API 调用都会失败。
   - 若要给面试官演示完整功能，本地 `npm run dev` + 启后端（`uvicorn main:app --port 8000`）即可。
   - 公网预览**只展示视觉**，作为简历"作品截图"。
2. **dist 体积**：当前 36 KB CSS + 105 KB JS gzip 后总体积非常小，GitHub Pages 100 GB 月流量额度绰绰有余。
3. **HTTPS 自动**：GitHub Pages 默认提供 Let's Encrypt 证书。

## 九、部署成功的标志

push 后：
1. `https://github.com/shangguanyunji663/Lun-Assistant/actions` 显示 ✅
2. `https://shangguanyunji663.github.io/Lun-Assistant/` 可访问
3. 主题切换 UI（顶部"柔雾青蓝 / 水墨留白 / 暗墨柔化"三按钮）可见
4. 单击切换能看到配色、卷轴/中缝/钤印变化

完成！🎉
