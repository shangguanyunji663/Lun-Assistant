# 目录结构审查报告

> 日期：2026-09-01
> 范围：全项目目录结构合理性评估（只读审查，未改动任何代码）。从职责划分 / 命名规范 / 职责重叠 / 层级深浅 / 最佳实践五个维度评估，并给出问题清单与优化建议。
>
> 方法：`git ls-files` 与 `find` 生成完整目录树；grep 验证 api→services→infrastructure 依赖方向；逐个读取关键模块 docstring 核实职责；对照 README 声明的架构核查。

## 一、总体结论

结构整体健康，属典型三层架构（`api → services → infrastructure`）＋横向支撑目录，按功能域（聚合根）组织。**分层依赖纪律执行严格**：实测 services 层 0 处反向 import api，infrastructure 层 0 处 import 上层。

主要问题集中在三处（P1）：① `evals/` 职责混合且 gitignore 规则不一致；② 顶层 `design-concepts/` 与 `docs/design-concepts/` 同名并存、职责重叠；③ `data/corpus/` 语料平铺无分类。另有若干 P2/P3 命名与层级小问题。

## 二、目录树全景

```
Lun-Assistant/
├── main.py                     # FastAPI 入口（create_app）
├── api/                        # 接口层（只依赖 services/infrastructure）
│   ├── deps.py                 # 路由共享依赖（项目归属校验）
│   ├── agent/                  # /chat (SSE) /resume
│   ├── auth/                   # 注册/登录/JWT（router+schemas+security）
│   ├── knowledge/              # 项目知识库聚合根（router+schemas）
│   ├── observability/          # Trace 回放（router+schemas）
│   ├── projects/               # 论文项目 CRUD（router+schemas）
│   └── middleware/             # 审计 HTTP 中间件
├── services/                   # 业务层（不得 import api/）
│   ├── agent/                  # 主从图 + planner + conversation_service + specialists/
│   ├── rag/                    # 检索管线 + query_rewrite + reranker + retriever + ingest/
│   ├── memory/                 # 四层记忆（short/long/structured/preference）+ compressor
│   ├── governance/             # 工具治理（registry/限流/熔断/锁/重试）+ 业务工具（tools_impl/artifacts/skill）
│   ├── llm/                    # LLMProvider（统一接入）
│   ├── streaming/              # EventHub（SSE 微缓冲）
│   ├── observability/          # Trace Span
│   ├── checkpoint/             # 三级降级检查点
│   └── classifier/             # 三级意图分类
├── infrastructure/             # 基础设施（谁都得经过它）
│   ├── config.py / paths.py / db.py / redis_client.py / audit.py
│   ├── models/                 # ORM×8（user/project/knowledge/memory/trace/audit/skill/base）
│   └── rbac/                   # 权限策略
├── frontend/                   # React 18 + Vite（src/ + components/ + public/）
├── configs/                    # settings/rbac/tools.yaml + ollama/Modelfile
├── data/                       # corpus（公共语料）+ uploads/runtime（运行时数据，gitignore）
├── evals/                      # 评测代码 + datasets/ + 报告产物（混合，见问题 1）
├── scripts/                    # 初始化 + 冒烟（smoke_*）+ 压测
├── docs/                       # 学习指南 + 优化记录 ROUND1-7 + design-concepts/
├── tests/                      # 离线 pytest 骨架（48 用例）
└── design-concepts/            # 设计素材与调参台（与 docs/design-concepts 重叠，见问题 2）
```

## 三、分层依赖验证（实测）

| 检查项 | 结果 |
| --- | --- |
| services 层 import api 层 | ✅ 0 处违规 |
| infrastructure 层 import services/api | ✅ 0 处违规 |
| api 层只向下依赖 | ✅ 仅 import services/infrastructure |

## 四、分维度评估

| 维度 | 评级 | 说明 |
| --- | --- | --- |
| 职责划分清晰度 | ★★★★☆ | api 按聚合根拆（auth/projects/knowledge/agent/observability）+ deps.py + middleware/；services 按领域拆 9 子包，docstring 职责明确 |
| 命名规范统一 | ★★★★☆ | router.py/schemas.py 统一、smoke_ 前缀统一、全 snake_case；瑕疵：两个 pipeline.py、两个 audit.py 同名 |
| 职责重叠/不清 | ★★★☆☆ | design-concepts 双目录、evals 代码与产物混放、governance 混合原语与业务工具 |
| 层级深浅 | ★★★★☆ | 主栈三层＋局部二层（rag/ingest、models、specialists）；services 下 5 个单文件包略增层级 |
| 最佳实践 | ★★★★☆ | 按功能域组织 ✓、ORM 集中 ✓、配置集中 ✓、测试收敛 ✓；无 pyproject.toml 属演进空间 |

## 五、问题清单

### P1 建议尽快处理

| # | 问题 | 证据 | 影响 |
| --- | --- | --- | --- |
| 1 | `evals/` 职责混合：代码（ab/harness/regression）+ 数据（datasets/）+ 报告产物（ab_report/load_report/results_latest.json、AB_REPORT.md）同层混放 | `git ls-files evals/` 显示 3 个 json 报告入库；.gitignore 仅忽略 regression_latest.json | 报告随库提交产生噪声 diff；忽略规则不一致 |
| 2 | 顶层 `design-concepts/`（4 张 PNG 合计 ~8.5MB + tuner/preview.html）与 `docs/design-concepts/`（DESIGN_SPEC/VISUAL_DIRECTIONS）同名并存 | commit 55a760a 一次入库 ~8.5MB 二进制 | 职责边界不清；仓库膨胀 |
| 3 | `data/corpus/` 80+ 文件平铺：AI 科普（ai001-050）、论文写作、伦理等主题混排 | data/corpus/ 下 80+ txt 无子目录 | 查找维护困难 |

### P2 建议优化

| # | 问题 | 证据 |
| --- | --- | --- |
| 4 | `services/rag/pipeline.py`（检索）与 `services/rag/ingest/pipeline.py`（入库）同名不同职责 | 两文件 docstring 职责完全不同 |
| 5 | `frontend/src/InkBackground.jsx` 未进 components/，其余 7 组件均在 components/ | frontend/src/ 组件分散两处 |
| 6 | services 下 5 个单文件包：checkpoint/classifier/llm/streaming/observability | 每包仅 1 文件 |
| 7 | `infrastructure/audit.py`（写库）与 `api/middleware/audit.py`（HTTP 中间件）同名 | 职责互补不重叠，但同名易混 |
| 8 | `services/governance/` 混合治理原语（circuit_breaker/dist_lock/rate_limiter/retry/tool_registry）与业务工具（academic_tools/artifacts/tools_impl/skill） | artifacts 迁入系 ROUND6 解环的有意妥协（见 ROUND6「依赖解环」节） |

### P3 低优先级 / 演进方向

| # | 问题 | 说明 |
| --- | --- | --- |
| 9 | 配置分散：requirements.txt + pytest.ini + .gitignore 未演进 pyproject.toml | 现代 Python 最佳实践 |
| 10 | `scripts/load_test.py` 执行入口与 `evals/load_report.json` 产物归属错位 | 产物归属与执行入口不一致 |
| 11 | `api/middleware/` 仅 1 个文件 | 可并入 api/ 根 |

## 六、优化建议（分批路线）

### 第一批（低成本高收益）

1. **evals/ 内分组**：新增 `evals/reports/` 收纳 json/md 报告并 gitignore；或至少将 ab_report/load_report/results_latest 加入 .gitignore，与 regression_latest.json 对齐。
2. **合并两个 design-concepts**：素材与调参台归档 `docs/design-concepts/assets/`，或反向把规范文档移出 docs/；大 PNG 走 Git LFS 或复用压缩版。
3. **corpus 分子目录**：按主题分 ai/、paper/、ethics/ 等。

### 第二批（一致性打磨）

4. 检索管线改名：`services/rag/pipeline.py` → `retrieval.py`（ingest/pipeline.py 在子包内无需改）。
5. `InkBackground.jsx` 移入 `frontend/src/components/`。
6. 两个 audit 改名区分：`infrastructure/audit.py` → `audit_service.py`。

### 第三批（长期演进）

7. services 单文件包后续不扩展时合并；领域独立仍是更好的扩展基础，不建议现在动。
8. 引入 pyproject.toml 统一依赖/测试/工具链配置。
9. governance 业务工具增多后拆 governance/（原语）+ tools/（业务工具）两层。

## 七、审查方法说明

- 目录树：`find` + `git ls-files`（排除 node_modules/envs/__pycache__ 等）
- 依赖方向：grep 全量扫描 import 语句
- 职责核实：逐一读取关键模块 docstring 与文件头
- 忽略规则：git check-ignore 验证 data/uploads 等运行时目录未入库

> 本报告为只读审查产物；各项建议待用户决策后实施，实施前会先列改动清单。
