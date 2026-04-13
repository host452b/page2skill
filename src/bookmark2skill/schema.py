from __future__ import annotations

from typing import Any


class ValidationError(Exception):
    """Raised when structured data fails validation."""
    pass


_REQUIRED_FIELDS = ("url", "title", "date_processed", "summary")


def _validate_quality_score(score: dict[str, Any]) -> None:
    """Check quality_score values are in 1-5 range."""
    for key, value in score.items():
        if value is not None and not (1 <= value <= 5):
            raise ValidationError(
                f"quality_score.{key} must be 1-5, got {value}"
            )


def validate(data: dict[str, Any]) -> dict[str, Any]:
    """Validate structured JSON data against the bookmark2skill schema.

    Required fields: url, title, date_processed.
    All other fields are optional (null, empty array, or omitted).
    Returns the data unchanged if valid.
    """
    for field in _REQUIRED_FIELDS:
        if field not in data or data[field] is None:
            raise ValidationError(f"Required field missing: {field}")

    metadata = (data.get("layers") or {}).get("agent_metadata") or {}
    quality = metadata.get("quality_score")
    if quality and isinstance(quality, dict):
        _validate_quality_score(quality)

    return data
