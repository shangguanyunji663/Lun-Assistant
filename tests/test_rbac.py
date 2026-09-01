"""RBAC 策略引擎单测（纯 YAML 规则，离线）。"""
from infrastructure.rbac.policy import _match, check, check_tool_permission


def test_match_patterns():
    assert _match("*", "tool:anything")
    assert _match("tool:*", "tool:search_literature")
    assert _match("tool:rewrite_query", "tool:rewrite_query")
    assert not _match("tool:rewrite_query", "tool:other")
    assert not _match("agent:run", "tool:rewrite_query")


def test_student_can_run_tools_but_not_admin_domains():
    assert check_tool_permission("student", "search_literature")
    assert check_tool_permission("student", "format_reference")
    assert check("student", "agent:run")
    assert check("student", "project:create")
    # admin 域资源对 student 不可见（rbac.yaml 未授予）
    assert not check("student", "observability:read")


def test_admin_wildcard_allows_all():
    assert check("admin", "tool:any_new_tool")
    assert check("admin", "observability:read")


def test_unknown_role_denied_by_default():
    assert not check("ghost", "tool:*")
    assert not check_tool_permission("ghost", "search_literature")
