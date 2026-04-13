import pytest
from bookmark2skill.schema import validate, ValidationError


def test_valid_full_data(sample_distilled_data):
    """Full structured data passes validation."""
    result = validate(sample_distilled_data)
    assert result["url"] == "https://example.com/article"
    assert result["title"] == "Simplicity is the ultimate sophistication"


def test_valid_minimal_data(sample_minimal_data):
    """Minimal data (only required fields) passes validation."""
    result = validate(sample_minimal_data)
    assert result["url"] == "https://example.com/minimal"
    assert result.get("author") is None


def test_missing_url_raises():
    """Missing required field 'url' raises ValidationError."""
    with pytest.raises(ValidationError, match="url"):
        validate({"title": "Test", "date_processed": "2026-04-13T12:00:00Z"})


def test_missing_title_raises():
    """Missing required field 'title' raises ValidationError."""
    with pytest.raises(ValidationError, match="title"):
        validate({"url": "https://x.com", "date_processed": "2026-04-13T12:00:00Z"})


def test_missing_date_processed_raises():
    """Missing required field 'date_processed' raises ValidationError."""
    with pytest.raises(ValidationError, match="date_processed"):
        validate({"url": "https://x.com", "title": "Test"})


def test_empty_optional_fields_are_ok():
    """Optional fields can be null, empty arrays, or omitted."""
    data = {
        "url": "https://example.com/test",
        "title": "Test",
        "date_processed": "2026-04-13T12:00:00Z",
        "author": [],
        "layers": {
            "distillation": {
                "logic_chain": [],
                "brilliant_quotes": [],
                "counterpoints": None,
            },
            "agent_metadata": {
                "tags": [],
                "taste_signals": {
                    "aesthetic": [],
                    "intellectual": None,
                    "values": [],
                },
            },
        },
    }
    result = validate(data)
    assert result["author"] == []
    assert result["layers"]["distillation"]["counterpoints"] is None


def test_quality_score_range():
    """Quality score values must be 1-5 if provided."""
    data = {
        "url": "https://example.com/test",
        "title": "Test",
        "date_processed": "2026-04-13T12:00:00Z",
        "layers": {
            "agent_metadata": {
                "quality_score": {"depth": 6, "originality": 3}
            }
        },
    }
    with pytest.raises(ValidationError, match="quality_score"):
        validate(data)
