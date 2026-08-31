"""YAML 驱动的 RBAC 策略引擎。

- 全局接口权限：configs/rbac.yaml 中 roles.<role>.allowed / denied，支持 * 通配。
- 工具级权限：governance 工具注册中心在调度前调用 check_tool_permission。
"""
from functools import lru_cache
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@lru_cache
def load_policy() -> dict:
    with open(PROJECT_ROOT / "configs" / "rbac.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _match(pattern: str, resource: str) -> bool:
    """支持 `*` 全匹配与 `prefix:*` 前缀通配。"""
    if pattern == "*":
        return True
    if pattern.endswith(":*"):
        return resource.startswith(pattern[:-1])
    return pattern == resource


def check(role: str, resource: str) -> bool:
    """校验角色对资源是否有权。规则: 先看 denied 再看 allowed。"""
    policy = load_policy().get("roles", {})
    if role not in policy:
        return False
    rules = policy[role]
    if any(_match(p, resource) for p in rules.get("denied", [])):
        return False
    return any(_match(p, resource) for p in rules.get("allowed", []))


def check_tool_permission(role: str, tool_name: str) -> bool:
    return check(role, f"tool:{tool_name}")
