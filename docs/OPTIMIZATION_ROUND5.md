# 优化记录 · 第五轮（学术工具生态 + 并发压测 + 对话底座切换）

> 本轮 P2 阶段落地：学术工具生态（6 类）、并发压测与内存量化、agnes-2.5-flash 云上对话底座接入（对话/嵌入底座解耦）。

## 一、本轮改进总览

| 模块     | 内容                                                        | 关键文件                                                                                                                                                      |
| ------ | --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 学术工具生态 | 学术翻译 / 润色 / 研究方法推荐 / 参考文献格式化 / 摘要生成 / 术语解析                | [academic\_tools](file:///d:/PythonProject/Lun-Assistant/services/governance/academic_tools.py)                                                           |
| 治理接入   | 6 工具全部经 ToolRegistry（RBAC/限流/熔断/审计），tools.yaml 补齐配置       | [tools.yaml](file:///d:/PythonProject/Lun-Assistant/configs/tools.yaml)                                                                                   |
| 并发压测   | 知识库检索 QPS / 延迟 P50·P95 / 服务端内存采样，报告落盘                     | [load\_test](file:///d:/PythonProject/Lun-Assistant/scripts/load_test.py)                                                                                 |
| 对话底座   | 新增 agnes-2.5-flash（OpenAI 兼容）；**对话与嵌入底座解耦**，嵌入仍走本地 bge-m3 | [provider](file:///d:/PythonProject/Lun-Assistant/services/llm/provider.py)、[settings.yaml](file:///d:/PythonProject/Lun-Assistant/configs/settings.yaml) |

## 二、学术工具生态（P2-1）

| 工具                  | 类型      | 说明                           | 降级配置              |
| ------------------- | ------- | ---------------------------- | ----------------- |
| translate\_academic | LLM     | 中↔英学术翻译（术语规范译法）              | —                 |
| polish\_academic    | LLM     | 学术润色（formal/concise/plain）   | —                 |
| recommend\_method   | LLM+RAG | 研究方法推荐（证据检索 + 决策单）           | fallback question |
| format\_reference   | **规则**  | GB/T 7714 / APA 参考文献格式化，离线可用 | fallback style    |
| generate\_abstract  | LLM+RAG | 结构化摘要（目的/方法/结果/结论）           | fallback length   |
| term\_explain       | LLM+RAG | 术语两层解析（通俗 + 学术）              | —                 |

- 纯 LLM 工具限长输入（截 4000 字），防超时/OOM；

- 全部经治理栈调用：Planner 与专项 Agent 可直接编排；

- 回归 S7 校验"注册工具 ↔ tools.yaml 配置一一对应"（含历史遗漏的 `topic_analysis` 补录）。

## 三、并发压测（P2-2）

脚本：`scripts/load_test.py --concurrency 8 --total 40`（自动注册临时用户 → 建项目 → 上传样例 → 并发打 `/knowledge/search` → 采样服务进程内存）。

本机实测基线（Ollama bge-m3 本地 CPU + bge-reranker 精排，Linux 4 并发共 64 请求）：

| 指标                 | 数值                        |
| ------------------ | ------------------------- |
| 实际请求 / 成功率         | 64 / 100%                 |
| QPS                | 0.6                       |
| 延迟 P50 / P95 / Max | 4054ms / 9886ms / 16198ms |
| 服务端 RSS 内存         | 稳定 1497MB（增量为 0）          |

结论与口径：

- 检索含 bge-m3 稠密路（单次 CPU 嵌入 \~1s+）与交叉编码器精排（CPU 推理），并发下排队成为主瓶颈 → QPS 低是**本地 CPU 底座的天花板**，非代码缺陷；改造方向为 GPU 推理 / 向量缓存 / 异步队列（后续迭代）；

- 内存稳定（进程常驻、无泄漏迹象）；

- 报告自动写入 `evals/load_report.json`（并发/总数可配，便于在 GPU 或云端底座复测对比）。

## 四、agnes-2.5-flash 对话底座（配置切换）

背景：本机 Ollama 仅安装 bge-m3（嵌入手感良好），无本地对话模型；按用户授权接入云上 agnes-2.5-flash（OpenAI 兼容 `/v1/chat/completions`）。

关键设计——**对话与嵌入解耦**：

```yaml
llm:
  default_provider: agnes          # 对话底座（云端，KEY 在 .env AGNES_API_KEY）
  embedding_provider: ollama       # 嵌入底座（本地 bge-m3，离线可用）
```

- `LLMProvider` 分别解析对话与嵌入两套 client/model（`services/llm/provider.py`）；

- 嵌入维度仍取 `providers.ollama.embedding_dim=1024`，与既有 pgvector 表一致；

- 想回退纯本地：`ollama pull qwen3:4b && ollama create qwen3:4b-ctx4096 -f configs\ollama\Modelfile.qwen3-ctx4096`，再改 `default_provider: ollama`。

联通性实测：`chat_model=agnes-2.5-flash / embed_model=bge-m3`，对话与嵌入（1024 维）均正常。

> ⚠️ 安全提示：`.env` 中的 `AGNES_API_KEY` 为真实密钥，已被 `.gitignore` 排除（不会进入版本库）；团队共享时请勿复制该文件。

## 五、实施中遇到的问题与修复（经验沉淀）

| # | 问题现象                                           | 根因                                                                                   | 修复                                                                                                                                           |
| - | ---------------------------------------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | 改写/对话全部失败 `model 'qwen3:4b-ctx4096' not found` | 本机 Ollama 无本地对话模型（仅 bge-m3），旧配置指向不存在的镜像                                              | 接入 agnes-2.5-flash 云上对话底座（KEY 已填 .env），同时**对话/嵌入双底座解耦**：`default_provider=agnes` + `embedding_provider=ollama`，嵌入仍走本地 bge-m3，pgvector 维度保持一致 |
| 2 | 改写日志刷 `LLM 未返回 JSON`                           | agnes 在 json\_mode 下偶发返回非 JSON 文本                                                    | 由 rewrite\_query 的异常→规则兜底链路消化（不改主流程）；并实测验证**漂移检测**拦截了 RRF 被改写成"色谱分析"的换域误改                                                                    |
| 3 | 压测报告成功率 400%                                   | 脚本把并发×总数当成请求总数，统计分母错误                                                                | 计数实际完成请求 `done`，QPS=done/elapsed、成功率=ok/done（复测 64 请求 100%）                                                                                  |
| 4 | Windows 下 `psycopg ... ProactorEventLoop` 告警   | psycopg 异步连接池要求 Selector 事件循环；告警仅出现在部分子路径（checkpointer），主进程已在 main.py 设置 Selector 策略 | 记录为已知平台限制：checkpointer 三级降级到进程内存（开发模式可用），不影响业务主链路                                                                                            |

## 六、本轮修改文件清单

```
新增:
  services/governance/academic_tools.py    6 类学术工具
  scripts/load_test.py                     并发压测 + 内存采样 + 报告
  evals/load_report.json                   压测报告（本机基线）
修改:
  services/llm/provider.py                 对话/嵌入双底座解耦
  services/governance/tools_impl.py        注册 academic 工具
  configs/settings.yaml                    default_provider=agnes + embedding_provider
  configs/tools.yaml                       6 工具治理配置
  requirements.txt                         psutil
  .env / .env.example                      AGNES_BASE_URL / AGNES_API_KEY
```

## 七、验证清单

- [x] 6 类学术工具注册并经治理栈调用（回归 S7 PASS）

- [x] format\_reference GB/T 7714 与 APA 输出正确（纯规则、离线）

- [x] term\_explain 串联 RAG+LLM 产出完整解释

- [x] 压测 100% 成功率，P50/P95/QPS 落盘，服务内存稳定

- [x] agnes 对话 + bge-m3 嵌入双底座联通（1024 维）

- [x] Query 改写漂移保护在 agnes 底座下同样生效（RRF 换域改写被拦截回退）

