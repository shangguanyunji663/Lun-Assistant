"""统一配置加载：configs/settings.yaml + .env 环境变量插值。

- `${VAR}` 形式的占位符从环境变量（含 .env 文件）取值，缺失即报错，避免静默错误配置。
- 全局单例，业务代码统一通过 get_settings() 获取。
"""
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_VAR_PATTERN = re.compile(r"\$\{([^}^{]+)\}")


def _load_env_file(path: Path) -> None:
    """极简 .env 解析：KEY=VALUE，不覆盖已存在的环境变量。

    回退策略：目标 .env 不存在时，加载同目录 .env.example 的占位默认值，
    保证首次 clone（无 .env）与 CI 也能加载配置跑测试；生产密钥仍需在 .env 覆盖。
    真正需要强校验的键（如 SECRET_KEY）仍按缺失即报错处理，不静默降级。
    """
    if not path.exists():
        example = path.with_name(".env.example")
        if example.exists():
            path = example
        else:
            return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _interpolate(node: Any) -> Any:
    if isinstance(node, dict):
        return {k: _interpolate(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_interpolate(v) for v in node]
    if isinstance(node, str):
        def _repl(m: re.Match) -> str:
            key = m.group(1).strip()
            val = os.environ.get(key)
            if val is None:
                raise RuntimeError(f"配置所需环境变量缺失: {key}（请在 .env 中配置）")
            return val

        return _VAR_PATTERN.sub(_repl, node)
    return node


@lru_cache
def get_settings() -> dict:
    _load_env_file(PROJECT_ROOT / ".env")
    with open(PROJECT_ROOT / "configs" / "settings.yaml", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return _interpolate(raw)


def _as_bool(value: Any) -> Any:
    """把字符串形式的布尔（'true'/'false'/'yes'/'no'/'0'/'1'）转成真正的 bool。"""
    if not isinstance(value, str):
        return value
    v = value.strip().lower()
    if v in ("true", "yes", "1", "on"):
        return True
    if v in ("false", "no", "0", "off", ""):
        return False
    return value


def get_value(*keys: str, default: Any = None, cast_bool: bool = False) -> Any:
    """按路径取配置，如 get_value("llm", "default_provider")。

    cast_bool=True 时，字符串布尔会转成真正的 bool（避免 bool("false")==True 的坑）。
    """
    node: Any = get_settings()
    for k in keys:
        if not isinstance(node, dict) or k not in node:
            return _as_bool(default) if cast_bool else default
        node = node[k]
    return _as_bool(node) if cast_bool else node


def get_embedding_dim() -> int:
    """嵌入向量维度：跟随运行时 llm.embedding_provider（缺省回退对话底座）。

    该值决定 pgvector 向量列的 DDL；切换嵌入底座导致维度变化时，
    需重建表或迁移数据（当前未引入 Alembic，见 README「已知限制」）。
    """
    providers = get_value("llm", "providers") or {}
    name = get_value("llm", "embedding_provider") or get_value("llm", "default_provider")
    dim = int((providers.get(name) or {}).get("embedding_dim") or 0)
    if dim <= 0:
        raise RuntimeError(
            f"嵌入底座 {name!r} 未配置有效 embedding_dim，无法确定 pgvector 向量列维度"
            "（检查 configs/settings.yaml → llm.providers）")
    return dim
