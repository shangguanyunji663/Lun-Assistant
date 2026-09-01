"""Planner 纯逻辑单测：复杂度判定 / 计划解析 / 参数规范化（离线）。"""
from services.agent.planner import _coerce_params, _parse_plan, is_complex_task


def test_complex_task_by_goal_words():
    assert is_complex_task("帮我写一份完整的开题报告")
    assert is_complex_task("给方向做个规划")


def test_complex_task_by_multiple_action_verbs():
    assert is_complex_task("检索文献，然后分析研究现状，最后撰写综述，并总结要点" * 2)


def test_simple_question_not_complex():
    assert not is_complex_task("什么是注意力机制")
    assert not is_complex_task("")


def test_parse_plan_filters_invalid_actions():
    plan = _parse_plan(
        '{"goal": "g", "steps": ['
        '{"action": "search_literature", "params": {"query": "LLM", "top_k": "5"}, "note": "n1"},'
        '{"action": "hack_tool", "params": {}, "note": "bad"}'
        "]}",
        allowed={"search_literature"})
    assert plan is not None
    assert len(plan["steps"]) == 1
    assert plan["steps"][0]["params"]["top_k"] == 5  # 数值参数被规范化为 int


def test_parse_plan_invalid_json_returns_none():
    assert _parse_plan("没有 JSON", {"search_literature"}) is None


def test_coerce_params_serializes_nested():
    out = _coerce_params({"a": {"x": 1}, "top_k": "7", "b": None})
    assert isinstance(out["a"], str) and '"x"' in out["a"]
    assert out["top_k"] == 7
    assert "b" not in out
