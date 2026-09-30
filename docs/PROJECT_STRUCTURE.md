# Lun-Assistant · 项目结构与文件用途说明

> 文档域：general
> 文档类型：操作手册 / 指南
> 主题版本：—
> 轮次：—
> 日期：2026-09-02
> 状态：已落地

> 2026-09-02 全面整理后的归档文档。目的：让项目结构一目了然、新人/未来会话能快速定位每个目录与关键文件的用途与价值。
> 本文档只做说明，不改变任何代码逻辑。
>
> ⚠️ **变更标注（2026-09-30 · v14/v15 同步轮）**：随前端 v14（顶栏修复/落地页 mock 化）与 v15（现代艺术四主题/落地页编辑部双结构）落地，§2/§3/§5 的主题数量、frontend 结构树与维护约定已按当前代码同步更新；§4 清理记录为 2026-09-02 历史快照，保持原样。

---

## 1. 项目概览

**Lun-Assistant（论匠）** —— 基于 LangGraph 主从多智能体架构的论文全流程智能助手。
后端 Python（FastAPI）+ 前端 React（Vite），本地运行环境 conda（`envs/lunjiang`）+ Ollama（`envs/ollama_models`）。

- 入口：`main.py`（后端 uvicorn）/ `frontend/`（前端 npm）
- 语言：Python 3.11（`envs/lunjiang`）+ JavaScript/JSX
- 部署：`.github/workflows/deploy.yml`（GitHub Pages，push 时 CI 自动 `vite build`）

---

## 2. 顶层目录用途与价值评估

| 目录 / 文件 | 用途 | 价值 | 备注 |
|------------|------|------|------|
| `main.py` | FastAPI 应用入口 | ★★★ | 启动后端 |
| `api/` | 路由层（auth/agent/projects/knowledge/observability/middleware） | ★★★ | 按模块分 Router |
| `services/` | 业务层（agent/llm/rag/memory/checkpoint/governance/classifier/observability/streaming） | ★★★ | 核心业务逻辑 |
| `infrastructure/` | 基础设施（models 模型定义 / rbac 权限） | ★★★ | 数据模型与权限 |
| `configs/` | 配置（settings.yaml / rbac.yaml / tools.yaml / ollama Modelfile） | ★★★ | 运行时配置 |
| `scripts/` | 运维/冒烟脚本（check_env / smoke_* / ingest_corpus / load_test） | ★★ | 手动运维用 |
| `tests/` | pytest 测试（89 用例） | ★★★ | 新增 `test_audit_sanitize.py`（R13）；含治理/模型/改写/API 集成/评测口径等 |
| `evals/` | 评测（harness / ab / regression + datasets + 报告） | ★★ | 含 `__init__.py` 为包 |
| `data/` | 语料库（corpus 81 个 txt）+ 运行时上传目录（uploads） | ★★★ | uploads 已 gitignore |
| `docs/` | 架构 / 部署 / 学习 / 优化记录 / 格式规范 | ★★★ | 后端线 ROUND1-13 + 通用文档留在根；前端版本线文档见 `frontend-versions/` |
| `docs/frontend-versions/` | 前端版本演进文档（v8→v15 全部版本档案 + 索引 + 模板） | ★★★ | 前端文档单一真源（文档治理轮新建） |
| `docs/design-concepts/` | 前端设计基线资产（preview.html / tuner.html / 4 张山水 PNG + JPG） | ★★ | 设计基线，非生产代码；版本线正文见 frontend-versions/ |
| `frontend/design-samples/` | v15 四方向设计样图（A 墨格编辑部 / B 新构成主义 / C 夜航诗意 / D 拓印套色，零依赖静态 HTML） | ★★ | 设计档案，未进 vite 构建；样图→生产还原差异见 CHANGELOG-v15 |
| `frontend/` | React 前端（Vite） | ★★★ | 见 §3 |
| `envs/` | 本地运行环境：`lunjiang`(venv) + `ollama_models`(模型) + `pkgs_cache`(conda 缓存) | ★★★ | **全部 gitignore**，勿提交 |
| `.github/workflows/` | GitHub Pages CI | ★★★ | 自动构建部署 |
| `Dockerfile` / `.dockerignore` / `docker-compose.yml` | 容器化：后端镜像（非 root + /health）+ PG/Redis/app 编排，`--scale app=2` 起多实例 | ★★ | R13 新增 app 服务；详见 [ROUND13](OPTIMIZATION_ROUND13.md) |
| `README.md` | 项目说明 | ★★★ | 更新于 2026-09-02 |
| `.editorconfig` / `.gitignore` / `pytest.ini` / `ruff.toml` / `pyproject.toml` / `requirements.txt` | 工程规范 | ★★★ | ruff/mypy 规则见 `pyproject.toml` + `ruff.toml` |
| `.env` / `.env.example` | 环境变量（密钥/端口） | ★★★ | `.env` 已 gitignore，勿提交 |
| `.workbuddy/` | WorkBuddy 会话记忆 | ★★ | 工具数据，勿删 memory/ |

> 说明：`services/agent/` 下已有子目录 `specialists/`；`data/uploads/` 是测试上传目录，运行时自动产生。

---

## 3. frontend/ 结构（React + Vite）

```
frontend/
├── src/
│   ├── main.jsx           # React 入口
│   ├── App.jsx            # 主界面：会话/对话/项目/右侧 tab + 11 主题切换器（A-K）
│   ├── styles.css         # 全局样式 + 十一主题 design tokens（:root = A；§13 v13 / §19-20 v14 / §21 v15 追加段）
│   ├── landing.css        # 落地页样式（双主题令牌 + 排印 + §12 mock + §13 编辑部双结构六主题）
│   ├── landing.js         # 落地页交互（六主题循环切换 / 入场 reveal / 数字滚动，<2KB 零依赖）
│   ├── InkBackground.jsx  # 山水背景分层（photo/veil/wash/grain/divider/stamp）
│   ├── api.js             # REST + SSE 封装
│   ├── constants.js
│   ├── hooks/             # useChat / useProjects / useSessions / useTheme（THEMES 注册单一真源）
│   └── components/        # AuthPage / Timeline / TracePanel / KnowledgePanel
│                          # ProjectArchive / ProjectDialog / decor(Seal·Markdown·WoodRoll)
├── public/
│   ├── bg/                # 主题背景图：bg-{a,c,d}-*.webp（B/E/F/G/H-K 为无图实色主题；v14 已清 b/mist）
│   └── console/tuner.html # 调参台（A-K 十一主题透明度/WCAG 测算，经 localStorage 与主应用联动）
├── design-samples/        # v15 四方向设计样图（零依赖静态 HTML，未进构建）
├── scripts/
│   ├── compress-bg-to-webp.py   # 主题图 PNG→WebP 转换（保留）
│   ├── shot-app.mjs             # 主应用主题回归（mock 登录 + token 探针 + 截图）
│   ├── shot-themes.mjs          # 调参台主题回归截图
│   └── verify-upload-msg.mjs    # 上传提示验证
├── index.html             # 落地页（双结构：#ln-site 经典六段 light/dark + #ed-site 编辑部版式 h/i/j/k）+ app.html 工作台双入口
├── vite.config.js         # base=/Lun-Assistant/（GitHub Pages）+ 双入口
├── package.json / package-lock.json
└── node_modules/          # gitignore，勿提交
```

### frontend 关键文件用途

| 文件 | 价值 |
|------|------|
| `src/hooks/useTheme.js` | ★★★ 主题注册单一真源（THEMES 11 项 A-K + localStorage 联动 + 切换音效） |
| `src/styles.css` | ★★★ 十一主题 token（A 柔雾青绿 / B 黑白瑞士 / C 暗墨夜山 / D 青绿金碧 / E-G v13 / H-K v15 现代艺术） |
| `src/landing.css` + `src/landing.js` | ★★★ 落地页双结构与六主题（#ln-site 经典 / #ed-site 编辑部） |
| `src/InkBackground.jsx` | ★★★ 背景分层骨架（图层与主题装饰开关） |
| `index.html` / `app.html` | ★★★ 落地页 / 工作台双入口（vite 双入口构建） |
| `public/console/tuner.html` | ★★ 调参台（A-K 十一主题透明度/WCAG 测算） |
| `design-samples/` | ★★ v15 四方向设计样图档案 |
| `scripts/shot-app.mjs` | ★★ 回归脚本，改主题后重跑即可出全套截图 |

---

## 4. 本次清理记录（2026-09-02）

### 已删除
| 对象 | 原因 |
|------|------|
| `.workbuddy/edge-screenshot-profile/`（230 文件） | Edge 测试浏览器残留 profile |
| `.pytest_cache/` | 测试缓存 |
| 21 处源码 `__pycache__/`（81 pyc） | 字节码缓存 |
| `frontend/dist/` | build 产物（CI 重建） |
| `frontend/public/console/tuner.html.bak` | 编辑备份残留 |
| `frontend/_backup-assets/`（3 PNG） | 与 design-concepts 重复（md5 相同），零引用 |
| `frontend/scripts/diag-tuner.py` / `diag-tuner2.py` / `capture-theme-screenshots.py` | 一次性诊断/旧截图脚本 |
| `data/uploads/` 5 重复样本 + 8 空目录 | 上传测试残留 |

### 已归档
- `frontend/_theme-shots/` 8 张 v11 截图 → `docs/frontend-versions/v11-screenshots/`

### 待处理（由人工决定）
- `envs/pkgs_cache/` 残留 9 个 conda 解压目录（约 130MB，`bzip2/libffi/libzlib/openssl/python-3.11.16/sqlite/vc14_runtime/xz`）
  —— 因安全删除回收站机制拦截且用户未授权继续删除，保留现状；可手动删除 `envs/pkgs_cache` 整个文件夹，或运行 `conda clean --all`（对 conda 管理的环境）。

### 体积变化
- 整理前 **8.8GB** → 整理后 **7.7GB**（回收约 1.1GB）
- 剩余大头为运行环境：`envs/ollama_models` 6.0GB（LLM 模型）+ `envs/lunjiang` 1.6GB（Python venv）—— 均属必需，勿删。

---

## 5. 维护注意事项（约定）

1. **不要提交** `envs/`、`frontend/dist/`、`frontend/node_modules/`、`.env`、`.workbuddy/`（均已 gitignore）。
2. 新增主题背景图：PNG 源图放 `design-concepts/`（正本），用 `frontend/scripts/compress-bg-to-webp.py` 转 WebP 到 `frontend/public/bg/`（仅适用于有背景图的主题；v13 起的 E-K 均为无图实色主题）。
3. 改/增主题需同步四处：`src/styles.css` 的对应 `body[data-theme]` token 块（现 11 个）+ `src/hooks/useTheme.js` THEMES/VALID_THEMES + `public/console/tuner.html`（THEMES 表/tab/CSS 覆盖）+ 落地页（landing.css 令牌映射；涉及时）。
4. 主题截图验证：`npm run dev` 后跑 `node scripts/shot-app.mjs`，输出到 `_theme-shots/`（用后归档或删除）；亦可用 Playwright（`channel=msedge` + mock `/api/**`）按主题截全页。
5. 前端改动后需同步 `public/console/tuner.html`（它是主应用 1:1 预览）。

---

_归档时间：2026-09-02 · 配套：前端版本线文档统一归档于 `docs/frontend-versions/`（v11 生产侧改造 = `CHANGELOG-v11-frontend.md`；v11 设计稿 = `CHANGELOG-v11-design.md`）_