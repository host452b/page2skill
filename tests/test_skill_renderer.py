import pytest
from bookmark2skill.renderers.skill import render_skill


def test_render_full_data(sample_distilled_data):
    result = render_skill(sample_distilled_data)
    assert result.startswith("---\n")
    assert "taste_signals:" in result
    assert "reuse_contexts:" in result
    assert "engineering/system-design" in result


def test_render_minimal_data(sample_minimal_data):
    result = render_skill(sample_minimal_data)
    assert "Minimal Article" in result
    assert result.startswith("---\n")


def test_render_includes_key_claims(sample_distilled_data):
    result = render_skill(sample_distilled_data)
    assert "Simplicity in system design" in result


def test_render_includes_quality_score(sample_distilled_data):
    result = render_skill(sample_distilled_data)
    assert "depth:" in result
    assert "practicality:" in result


def test_render_includes_when_to_reference(sample_distilled_data):
    result = render_skill(sample_distilled_data)
    assert "Making architecture decisions" in result


def test_render_skips_empty_body_sections(sample_minimal_data):
    result = render_skill(sample_minimal_data)
    assert "## Key Insights" not in result
    assert "## When To Reference" not in result
