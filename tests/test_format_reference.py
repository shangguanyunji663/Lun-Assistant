"""参考文献格式化规则引擎单测（离线，P2 学术工具）。"""
from services.governance.academic_tools import format_reference


def test_gb7714_full_fields():
    out = format_reference(authors="张三,李四", title="大模型综述", journal="计算机学报",
                           year="2024", volume="47", issue="1", pages="1-20")
    assert out == "张三,李四.大模型综述[J].计算机学报,2024,47(1):1-20."


def test_gb7714_missing_fields_use_placeholder():
    out = format_reference(title="只有标题")
    assert "佚名" in out and "(未命名文献)" not in out and "佚刊" in out and "无年份" in out


def test_apa_style():
    out = format_reference(authors="Smith, J", title="LLM Survey", journal="Nature",
                           year="2023", volume="615", issue="2", pages="100-110",
                           style="apa")
    assert out == "Smith, J (2023). LLM Survey. Nature, 615(2), 100-110."


def test_apa_author_separator_normalization():
    out = format_reference(authors="Smith，Jones", title="T", style="apa")
    assert "Smith & Jones" in out


def test_unsupported_style_rejected():
    out = format_reference(style="mla")
    assert "不支持的格式" in out and "mla" in out
