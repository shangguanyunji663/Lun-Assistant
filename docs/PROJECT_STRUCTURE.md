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
>
> ⚠️ **变更标注（2026-10-01 · 落地页一致性修复 + 彩蛋轮）**：随前端 ROUND18（落地页双结构一致性修复 + 三枚彩蛋机关）落地，§3 frontend 结构树已补 `public/easter/`、彩蛋机关说明与 `index.html` 入口说明；工作台与后端零改动。轮次详情见 [`frontend-versions/OPTIMIZATION_ROUND18.md`](frontend-versions/OPTIMIZATION_ROUND18.md)。（注：彩蛋机关脚本在 v18 皮肤重构中已由 `src/landing.js` 迁移至 `src/landing/shared.js`。）
>
> ⚠️ **变更标注（2026-10-05 · 文档全域同步）**：§2 `tests/` 用例数 **93 → 103**（实测 `pytest tests/ -q`）；`evals/` 用途补全——新增 `eval_intent_holdout` / `eval_suites` / `eval_compression_real` 三个专项入口与 `provenance.py`（产物身份证），产物增至 3 个 `results_*.json`；§2 `.github/workflows/` 用例数同步 103。数字与术语基准见 [`CANON.md`](CANON.md)，评测口径定稿见 [`METRICS_FINAL.md`](METRICS_FINAL.md)，本次审计全过程见 [`DATA_INTEGRITY_AUDIT.md`](DATA_INTEGRITY_AUDIT.md)。
>
> ⚠️ **变更标注（2026-10-05 · 代码同步审计）**：`data/corpus/` 81 篇经复核维持一致（`tests/` 用例数当日先后为 93 → 97 → **103**，最终值见上一条标注）；订正 §1 部署描述、§2 `.github/workflows/` 职责（补 `test-backend` job）、§2 `skins/patterns/` 现状（v18 起纹样素材无引用）、§3 `frontend/scripts/` 清单。§3 另按 2026-10-04 的前端改动同步：工作台**切项目即另起新会话**（时间线随项目上下文归零）、`Timeline` 渲染 `step_event` 工具进度（进行中 / 完成+耗时 / 异常）、落地页切换器文案统一「切换皮肤」且展开 8 套、`/app.html?demo=1`（免登录预览）与 `/app.html`（登录入口）语义分离。
>
> ⚠️ **变更标注（2026-10-03 · 八套皮肤轮）**：随 ROUND20 补记（两页新语言落地为第 7/8 套皮肤）与 v18 皮肤体系定稿，§2/§3/§5 的皮肤数量、frontend 结构树与维护约定已按当前代码同步：皮肤 6 → **8 套**（新增 `g-score.css` / `h-contact.css`），落地页 6 → **8 张**（新增 `how-it-works.html` / `dossier.html`），vite 入口 7 → **9 个**；`docs/design-concepts/` 与 `frontend/design-samples/` 的实际内容亦按当前目录订正。轮次详情见 [`frontend-versions/ROUND20-ADDENDUM.md`](frontend-versions/ROUND20-ADDENDUM.md)。

---

## 1. 项目概览

**Lun-Assistant（论匠）** —— 基于 LangGraph 主从多智能体架构的论文全流程智能助手。
后端 Python（FastAPI）+ 前端 React（Vite），本地运行环境 conda（`envs/lunjiang`）+ Ollama（`envs/ollama_models`）。

- 入口：`main.py`（后端 uvicorn）/ `frontend/`（前端 npm）
- 语言：Python 3.11（`envs/lunjiang`）+ JavaScript/JSX
- 部署：`.github/workflows/deploy.yml` 两个 job——`build-deploy`（push 时自动 `vite build` 并发布 GitHub Pages）与 `test-backend`（Ubuntu 上 `ruff check .` + `pytest tests/ -q`）

---

## 2. 顶层目录用途与价值评估

| 目录 / 文件 | 用途 | 价值 | 备注 |
|------------|------|------|------|
| `main.py` | FastAPI 应用入口 | ★★★ | 启动后端 |
| `api/` | 路由层（auth/agent/projects/knowledge/observability/middleware） | ★★★ | 按模块分 Router |
| `services/` | 业务层（agent/llm/rag/memory/checkpoint/governance/classifier/observability/streaming） | ★★★ | 核心业务逻辑 |
| `infrastructure/` | 基础设施（models 模型定义 / rbac 权限） | ★★★ | 数据模型与权限 |
| `configs/` | 配置（settings.yaml / rbac.yaml / tools.yaml / ollama Modelfile） | ★★★ | 运行时配置 |
| `scripts/` | 运维/冒烟脚本（check_env / preflight / smoke_* / ingest_corpus / load_test + dev_up / dev_down 启停） | ★★ | 手动运维用 |
| `tests/` | pytest 测试（15 文件 / **103 用例**） | ★★★ | 含治理/模型/改写/API 集成/评测口径（`test_evals_scoring.py`）/记忆压缩语义（`test_memory_pure.py`）等 |
| `evals/` | 评测：`harness.py`（三指标）+ `ab.py`（A/B）+ `regression.py`（16 项回归）+ 3 个专项入口（`eval_intent_holdout` / `eval_suites` / `eval_compression_real`）+ `provenance.py`（产物身份证）+ `datasets/` | ★★★ | 含 `__init__.py` 为包；产物 `results_latest.json` / `results_intent_holdout.json` / `results_compression_real.json` |
| `data/` | 语料库（corpus 81 个 txt）+ 运行时上传目录（uploads） | ★★★ | uploads 已 gitignore |
| `docs/` | 架构 / 部署 / 学习 / 优化记录 / 格式规范 / **术语与数字单一真源 `CANON.md`** | ★★★ | 后端线 ROUND1-13 + 通用文档留在根；前端版本线文档见 `frontend-versions/` |
| `docs/frontend-versions/` | 前端版本演进文档（v8→v18 全部版本档案 + 索引 + 模板） | ★★★ | 前端文档单一真源（文档治理轮新建） |
| `docs/design-concepts/` | 前端设计基线资产（4 张山水 PNG + 1 张 JPG） | ★★ | 设计基线，非生产代码；版本线正文见 frontend-versions/ |
| `frontend/design-samples/` | 设计档案（v15 proposal-1…10 + sample-a…d + round20-pages 样张，零依赖静态 HTML） | ★★ | 设计档案，未进 vite 构建；样图→生产还原差异见 CHANGELOG-v15 / ROUND20 |
| `frontend/` | React 前端（Vite） | ★★★ | 见 §3 |
| `envs/` | 本地运行环境：`lunjiang`(venv) + `ollama_models`(模型) + `pkgs_cache`(conda 缓存) | ★★★ | **全部 gitignore**，勿提交 |
| `.github/workflows/` | CI：前端 eslint + build + GitHub Pages 发布；后端 ruff + pytest（103 离线用例） | ★★★ | 两个 job 并行，见 `docs/DEPLOY.md` §四 |
| `Dockerfile` / `.dockerignore` / `docker-compose.yml` | 容器化：后端镜像（非 root + /health）+ PG/Redis/app 编排，`--scale app=2` 起多实例 | ★★ | R13 新增 app 服务；详见 [ROUND13](OPTIMIZATION_ROUND13.md) |
| `README.md` | 项目说明 | ★★★ | 更新于 2026-10-05（评测口径与压缩缺陷修复同步） |
| `.editorconfig` / `.gitignore` / `pytest.ini` / `ruff.toml` / `pyproject.toml` / `requirements.txt` | 工程规范 | ★★★ | ruff/mypy 规则见 `pyproject.toml` + `ruff.toml` |
| `.env` / `.env.example` | 环境变量（密钥/端口） | ★★★ | `.env` 已 gitignore，勿提交 |
| `.workbuddy/` | WorkBuddy 会话记忆 | ★★ | 工具数据，勿删 memory/ |

> 说明：`services/agent/` 下已有子目录 `specialists/`；`data/uploads/` 是测试上传目录，运行时自动产生。

---

## 3. frontend/ 结构（React + Vite · v18 八套设计语言）

```
frontend/
├── src/
│   ├── main.jsx           # React 入口；样式加载顺序：base → panels → fx → skins/*（八份）→ layout
│   ├── App.jsx            # 工作台主壳（.wb-* 语义标记）：三栏 + 皮肤接入 + 会话拖拽重排 + 采纳盖章；切换项目即另起新会话（时间线随项目上下文归零，流式期间不切）
│   ├── fx.js              # 动效工具箱（粒子 / 换肤遮罩 / 成就条 / 3D 倾斜 / 磁吸 / 盖章）
│   ├── fx.css             # 动效层样式（入场编排 / 指针特效 / 氛围 / 高光时刻 / 弱动效降级）
│   ├── api.js             # REST + SSE 封装
│   ├── constants.js       # 状态枚举文案映射
│   ├── demo.js            # 仅 DEV 的演示数据：`app.html?demo=1`（生产构建不进入该分支）
│   ├── hooks/             # useChat / useProjects / useSessions / useSkin / useStickyScroll
│   ├── components/        # AuthPage / Timeline（节点事件 + step_event 工具进度）/ TracePanel / KnowledgePanel
│   │                      # ProjectArchive / ProjectDialog / SkinPicker / decor(Seal·Rule·AmbientLines·Markdown)
│   ├── skins/             # ★ 皮肤（单一真源注册 + 八套完整设计语言 + 契约文档）
│   │   ├── registry.js    #   八套皮肤注册（id / 名称 / 色点 / 落地页 / theme-color）
│   │   ├── CONTRACT.md    #   皮肤契约：令牌表 + 类名表 + 书写规范 + 自检清单
│   │   ├── patterns/      #   历史纹样素材（lotus-scroll.svg / meander.svg）；v18 起皮肤材质全走 CSS，两图当前无引用（见该目录 README）
│   │   └── a-letterpress / b-console / c-poster / d-bamboo / e-riso / f-archive / g-score / h-contact .css
│   ├── styles/            # 共享底座（与皮肤无关）
│   │   ├── base.css       #   重置 / 焦点 / 滚动条 / 弹窗骨架 / markdown 结构 / 令牌契约说明
│   │   ├── panels.css     #   共享组件层：知识库 / 档案 / 可观测 / 登录页（只吃皮肤令牌）
│   │   └── layout.css     #   工作台外壳与滚动契约（须置于 skins/*.css 之后）
│   └── landing/           # 落地页共享行为与样式（八页共用）
│       ├── shared.js      #   皮肤切换器（触发按钮文案固定「切换皮肤」，展开 8 套）/ 入场编排 / 数字滚动 / 打字机 / 彩蛋三门 / 落笔处
│       └── shared.css     #   上述共享物的样式（取色走 --lb-* 落地页令牌）
├── index.html             # 落地页 · 皮肤 A「铅字印刷」（站根；含皮肤记忆跳转）
├── landing-b…f.html       # 落地页 · 皮肤 B–F（每皮肤一页）
├── how-it-works.html      # 落地页 · 皮肤 G「编队总谱」（第 7 套，含出声音符 / 演奏全曲 / fermata 停拍）
├── dossier.html           # 落地页 · 皮肤 H「论文底片」（第 8 套，含逐条解密 / 阵风 / 打字机音效）
├── app.html               # 工作台入口（首帧前写入 <html data-skin>）；不带参数=登录入口，`?demo=1`=免登录预览入口
├── public/
│   ├── fig/              # 落地页配图（3 张黑白摄影，本地资产，不依赖外部出图接口）
│   └── easter/            # 彩蛋页：dispatch / hunt / brush（落地页三门触发的独立静态页，不进构建）
├── design-samples/        # 设计档案（v15 proposal-1…10 + sample-a…d + round20-pages，零依赖静态 HTML，不参与构建）
├── scripts/
│   ├── shot-app.mjs / shot-audit.mjs / shot-before-after.mjs   # 主应用与皮肤截图回归
│   └── verify-{chat-layout,interrupt-mobile,responsive,state,upload-msg}.mjs  # 布局 / 状态 / 上传验证
├── vite.config.js         # base=/Lun-Assistant/（GitHub Pages）+ 九入口（站根 / 工作台 / 8 张落地页）
├── package.json / package-lock.json
└── node_modules/          # gitignore，勿提交
```

### frontend 关键文件用途

| 文件 | 价值 |
|------|------|
| `src/skins/CONTRACT.md` | ★★★ **皮肤契约单一真源**：令牌表 / 类名表 / 书写规范 / 自检清单 |
| `src/skins/registry.js` | ★★★ 皮肤注册单一真源（八套：id / 名称 / 色点 / 落地页 / theme-color） |
| `src/skins/*.css` | ★★★ 八套设计语言的完整实现（铅字印刷 / 夜航仪表 / 学术海报 / 木牍竖排 / 孔版双色 / 索引档案 / 编队总谱 / 论文底片） |
| `src/styles/base.css` + `panels.css` + `layout.css` | ★★★ 共享底座与次级面板（只吃皮肤令牌，八套皮肤自动适配） |
| `src/fx.css` + `src/fx.js` | ★★★ 动效层：入场编排 / 指针特效 / 氛围 / 高光时刻，JS 工具箱与样式分家 |
| `src/landing/shared.{js,css}` | ★★★ 八张落地页的共享行为与样式（切换器 / 彩蛋三门 / 落笔处）；切换器触发按钮文案统一「切换皮肤」，条目由 `registry.js` 动态渲染 8 套 |
| `index.html` + `landing-{b…f}.html` + `how-it-works.html` + `dossier.html` | ★★★ 八张落地页（每套皮肤一张，vite 九入口构建）；G/H 两页与六张旧页之间的内容互链已拆除，仅由切换器提供 8 套导航 |
| `src/demo.js` | ★★ 开发预览数据：`npm run dev` 后访问 `app.html?demo=1` 可无后端逐套核对皮肤；**不带 `?demo=1` 的 `/app.html` 是登录入口**（两者语义不同，落地页链接已按锚文本分开） |
| `design-samples/` | ★ v15/v18 设计档案（历史参照，不参与构建） |
| `scripts/shot-app.mjs` | ★ 回归脚本 |

> **改皮肤时要同步的位置**：① `src/skins/<皮肤>.css`（观感）② `src/skins/registry.js`（名称 / 色点 / 落地页）
> ③ 对应的落地页 HTML（`index.html` / `landing-*.html` / `how-it-works.html` / `dossier.html`）④ 落地页里的 `--lb-*` 令牌。
> 新增皮肤还需扩 `vite.config.js` 的入口、`src/main.jsx` 的样式引入，并在 `CONTRACT.md` 记录。

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
2. **v18 起的皮肤不使用背景图**：材质一律由 CSS（渐变 / 重复纹理 / 噪点 data-uri / 硬阴影）承担，
   `public/bg/` 与配套的图片转换脚本已随主题体系一并删除。新增皮肤不需要任何图片资产。
3. **改 / 增皮肤需同步四处**：① `src/skins/<皮肤>.css`（观感）② `src/skins/registry.js`（名称 / 色点 / 落地页路径）
   ③ 对应的落地页 HTML（`index.html` 或 `landing-*.html`）④ 落地页 `<style>` 里的 `--lb-*` 令牌。
   新增皮肤还要扩 `vite.config.js` 的入口与 `src/main.jsx` 的样式引入，并在 `src/skins/CONTRACT.md` 留下记录。
4. **皮肤回归验证**：`npm run dev` 后跑 `node scripts/shot-app.mjs`；
   另一个更轻的办法是访问 `app.html?demo=1`（仅 DEV 生效的演示数据），
   不起后端即可逐套核对八套设计语言（登录路径是不带参数的 `/app.html`）。
5. `npm run lint` + `npm run build` 必须通过（CI 会执行，见 `.github/workflows/deploy.yml`）——
   产物含九个入口（站根落地页 / 工作台 / 8 张皮肤落地页），改 `vite.config.js` 的 `input` 时注意同步。

---

_归档时间：2026-09-02 · 配套：前端版本线文档统一归档于 `docs/frontend-versions/`（v11 生产侧改造 = `CHANGELOG-v11-frontend.md`；v11 设计稿 = `CHANGELOG-v11-design.md`）_