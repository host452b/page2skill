import pytest
from bookmark2skill.renderers.obsidian import render_obsidian


def test_render_full_data(sample_distilled_data):
    result = render_obsidian(sample_distilled_data)
    assert "Simplicity is the ultimate sophistication" in result
    assert "https://example.com/article" in result
    assert "Complex systems fail in complex ways" in result
    assert "The best code is no code at all." in result
    assert "Netflix" in result
    assert "Hystrix" in result


def test_render_minimal_data(sample_minimal_data):
    result = render_obsidian(sample_minimal_data)
    assert "Minimal Article" in result
    assert "https://example.com/minimal" in result
    assert "## 逻辑推导链" not in result
    assert "## 精彩表达" not in result


def test_render_has_yaml_frontmatter(sample_distilled_data):
    result = render_obsidian(sample_distilled_data)
    assert result.startswith("---\n")
    assert "\n---\n" in result[3:]


def test_render_skips_empty_sections(sample_minimal_data):
    result = render_obsidian(sample_minimal_data)
    lines = result.split("\n")
    section_headers = [l for l in lines if l.startswith("## ")]
    assert len(section_headers) == 0


def test_render_quotes_include_why(sample_distilled_data):
    result = render_obsidian(sample_distilled_data)
    assert "Concise expression of YAGNI principle" in result
