"""复合任务 Planner 节点：Plan → Execute → Replan。

设计（对应企业 RAG 助手"多步规划"能力）：
1. 复杂度判定 is_complex_task()：由 supervisor 决定是否进入本节点
   （多动作词 / 目标词命中 / 长输入 + 文献或写作意图）；
2. Plan：LLM 生成 JSON 计划 {"goal", "steps":[{action, params, note}]}，
   steps 上限 5，action 限定为已注册治理工具或 "answer"（纯 LLM 子任务）；
3. Execute：逐步经 tool_registry.call() 执行（自动获得 RBAC/限流/熔断/审计），
   前序步骤产出累积为 evidence，注入后续 LLM 步骤；
4. Replan：步骤失败 → 自动带"简化要求"重试一次 → 仍失败则记录错误继续，
   保证部分成功结果不丢失；
5. 汇总：按步骤输出 Markdown 产物。

工具注册时机：AgentEngine.get_graph()（单例锁内幂等注册），本节点不再重复注册。
"""
import json
import logging

from services.governance.tool_registry import tool_registry
from services.llm.provider import LLMProvider
from services.observability.trace import span
from services.streaming.hub import current_hub

logger = logging.getLogger("lunjiang.graph")

_MAX_STEPS = 5
_ACTION_VERBS = ("分析", "检索", "搜索", "撰写", "写", "生成", "规划", "整理", "总结",
                 "设计", "查重", "降重", "校验", "检测", "翻译", "润色")
# 目标词：与 _ACTION_VERBS 中的动名词保持一致（如"规划"同时是动作与目标），
# 避免同一词在动词表命中、在目标词表缺失导致的漏判
_GOAL_WORDS = ("综述", "开题", "报告", "大纲", "方案", "计划", "规划", "路线", "完整流程")


def is_complex_task(user_input: str, intent: str = "") -> bool:
    """复杂性启发式：多动作词 / 目标词 / 长输入 + 文献或写作意图。"""
    text = user_input or ""
    hits = sum(1 for v in _ACTION_VERBS if v in text)
    if len(text) >= 60 and hits >= 2:
        return True
    if hits >= 3:
        return True
    if any(g in text for g in _GOAL_WORDS):
        return True
    if intent in ("literature_search", "writing") and len(text) > 100:
        return True
    return False


_PLAN_SYSTEM = (
    "你是论文助手的任务规划器。把用户请求拆解为可顺序执行的工具调用步骤。"
    "输出JSON: {\"goal\": \"任务目标\", "
    "\"steps\": [{\"action\": \"工具名\", \"params\": {参数名: 参数值}, "
    "\"note\": \"这一步做什么\"}]}。"
    "可用工具: search_literature(检索文献, params: query, top_k), "
    "topic_analysis(params: major, interest, requirement), "
    "generate_section(params: section, outline, references), "
    "generate_artifact(params: kind[review_draft|proposal_report|defense_outline], topic, requirement), "
    "check_format(params: text), check_plagiarism(params: text), "
    "answer(直接回答, params: prompt)。"
    "要求: 步骤 2-4 个，先检索后生成，参数必须是字符串。"
)


def _coerce_params(params: dict) -> dict:
    """参数规范化：数值型参数转 int（防切片/分页 TypeError），其余字符串化。"""
    num_keys = {"top_k", "length", "max_tokens", "window", "k"}
    out = {}
    for k, v in (params or {}).items():
        if isinstance(v, (dict, list)):
            out[k] = json.dumps(v, ensure_ascii=False)[:800]
        elif k in num_keys:
            try:
                out[k] = int(str(v))
            except (TypeError, ValueError):
                out[k] = v
        elif v is not None:
            out[k] = str(v)
    return out


def _parse_plan(text: str, allowed: set[str]) -> dict | None:
    """解析 LLM 计划 JSON，过滤非法 action。"""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None
    steps = []
    for s in (data.get("steps") or [])[:_MAX_STEPS]:
        action = str(s.get("action") or "").strip()
        if action not in allowed:
            continue
        steps.append({
            "action": action,
            "params": _coerce_params(s.get("params")),
            "note": str(s.get("note") or "")[:120],
        })
    if not steps:
        return None
    return {"goal": str(data.get("goal") or "")[:200], "steps": steps}


async def _llm_plan(user_input: str, context: str, allowed: set[str]) -> dict | None:
    provider = LLMProvider()
    try:
        data = await provider.chat(
            [{"role": "system", "content": _PLAN_SYSTEM},
             {"role": "user",
              "content": f"用户请求: {user_input}\n相关背景: {context or '(无)'}"}],
            json_mode=True, temperature=0.1, max_tokens=800)
        text = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
        return _parse_plan(text, allowed)
    except Exception as e:
        logger.warning("规划 LLM 失败: %s", e)
        return None


async def planner_node(state: dict) -> dict:
    """LangGraph 节点：Plan-Execute-Replan，产出 final_output。"""
    hub = current_hub()
    user_input = state.get("user_input", "")
    visited = list(state.get("visited_agents", []))

    with span("agent.planner", "agent_node",
              input_data={"len": len(user_input)}, user_id=state.get("user_id")) as sp:
        await hub.emit("node_start", {"agent": "planner", "title": "任务规划Agent"},
                       node="planner")

        allowed = set(tool_registry.tools) | {"answer"}
        context = state.get("memory_brief", "") or ""

        # ---- 1. Plan ----
        plan = await _llm_plan(user_input, context, allowed)
        if plan is None:
            # 规划失败降级：单步文献检索 + 汇总
            plan = {"goal": user_input, "steps": [
                {"action": "search_literature", "params": {"query": user_input, "top_k": "5"},
                 "note": "检索相关文献"},
            ]}
        await hub.emit("plan", {"goal": plan["goal"], "steps": plan["steps"]},
                       node="planner")
        sp.set_io(output={"steps": len(plan["steps"])})

        # ---- 2. Execute（带 evidence 累积）----
        evidence, report = [], []
        all_ok = True
        for i, step in enumerate(plan["steps"], 1):
            action, params = step["action"], dict(step["params"])
            status, body = await _execute_step(
                state, action, params, evidence, hub, node_label=f"步骤{i}:{step['note'] or action}", plan=plan)
            if status != "ok":
                all_ok = False
            report.append({"step": i, "action": action,
                           "note": step["note"], "status": status})
            evidence.append(body[:800])
            await hub.emit("step_event", {"step": i, "total": len(plan["steps"]),
                                          "action": action, "status": status},
                           node="planner")

        # ---- 3. 汇总 Markdown ----
        output = _assemble(user_input, plan, report, evidence)
        sp.set_io(output={"ok": all_ok, "steps_ok": sum(1 for r in report if r["status"] == "ok")})
        await hub.emit("node_end", {"agent": "planner",
                                    "output_preview": output[:200],
                                    "ok": all_ok}, node="planner")
        return {"final_output": output, "next_agent": "supervisor",
                "stop_reason": "done", "visited_agents": [*visited, "planner"]}


async def _execute_step(state, action: str, params: dict, evidence: list[str],
                        hub, node_label: str, plan: dict) -> tuple[str, str]:
    """执行单步；失败带简化要求重试一次（Replan）；返回 (status, body)。"""
    for attempt in (1, 2):
        try:
            if action == "answer":
                prompt = params.get("prompt", params.get("query", ""))
                evidence_txt = "\n".join(f"- {e[:300]}" for e in evidence[-3:]) if evidence else "(无)"
                body = await LLMProvider().chat([
                    {"role": "system",
                     "content": "你是论匠论文助手，基于已收集的证据回答问题，证据不足时明确说明。"},
                    {"role": "user", "content": f"{prompt}\n\n[已收集证据]\n{evidence_txt}"}],
                    max_tokens=800)
            else:
                body = await tool_registry.call(
                    action, user_id=state.get("user_id"), user_role=state.get("user_role", "student"),
                    call_context={"agent": "planner"}, **params)
            return "ok", _stringify(body)
        except PermissionError as e:
            return "error", f"RBAC拒绝: {e}"
        except Exception as e:
            logger.warning("Planner步骤失败(attempt=%d) %s: %s", attempt, node_label, e)
            if attempt == 1:
                params = dict(params)
                params["requirement"] = params.get("requirement", "") + "；请输出更简短的版本"
            else:
                return "error", f"执行失败: {str(e)[:200]}"
    return "error", "unreachable"


def _assemble(user_input: str, plan: dict, report: list[dict], evidence: list[str]) -> str:
    lines = ["# 任务执行报告", ""]
    lines.append(f"**目标**：{plan['goal'] or user_input}")
    lines.append(f"**执行状态**：" +
                 ("✅ 全部步骤成功" if all(r["status"] == "ok" for r in report) else "⚠️ 部分步骤未完成"))
    lines += ["", "## 执行步骤"]
    for r in report:
        mark = "✅" if r["status"] == "ok" else "❌"
        lines.append(f"{mark} **{r['step']}. {r['note'] or r['action']}** ({r['action']})")
    lines += ["", "## 产出摘要"]
    for i, e in enumerate(evidence[:5], 1):
        lines.append(f"### 步骤{i} 产出")
        lines.append(e.strip() if e.strip() else "(无内容)")
        lines.append("")
    return "\n".join(lines)


def _stringify(body) -> str:
    if isinstance(body, str):
        return body
    try:
        return json.dumps(body, ensure_ascii=False, default=str)
    except Exception:
        return str(body)
