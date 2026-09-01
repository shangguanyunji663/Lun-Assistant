"""配置层单测：路径读取 / 布尔转换 / 嵌入维度解析（全部离线）。"""
import pytest

from infrastructure.config import _as_bool, get_embedding_dim, get_value


def test_get_value_reads_nested_keys():
    assert get_value("app", "name") == "lunjiang"
    assert get_value("agent", "max_hops") >= 1


def test_get_value_missing_path_returns_default():
    assert get_value("no", "such", "key", default=42) == 42
    assert get_value("no", "such", "key") is None


def test_as_bool_covers_string_forms():
    assert _as_bool("true") is True
    assert _as_bool("Yes") is True
    assert _as_bool("1") is True
    assert _as_bool("false") is False
    assert _as_bool("0") is False
    assert _as_bool("off") is False
    assert _as_bool(3) == 3  # 非字符串原样返回


def test_embedding_dim_follows_runtime_provider():
    # 当前配置 embedding_provider=ollama(1024)。若切换底座，此值必须跟随 providers.<name>.embedding_dim
    dim = get_embedding_dim()
    assert dim > 0
    assert isinstance(dim, int)


def test_embedding_dim_raises_without_valid_provider(monkeypatch):
    """嵌入底座缺有效 embedding_dim 时必须快速失败，而不是静默回退。"""
    import infrastructure.config as cfg

    def fake_get_value(*keys, default=None, cast_bool=False):
        data = {"llm": {"providers": {"fake": {"embedding_dim": 0}},
                        "embedding_provider": "fake"}}
        node = data
        for k in keys:
            if not isinstance(node, dict) or k not in node:
                return default
            node = node[k]
        return node

    monkeypatch.setattr(cfg, "get_value", fake_get_value)
    with pytest.raises(RuntimeError, match="embedding_dim"):
        cfg.get_embedding_dim()
