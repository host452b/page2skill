from __future__ import annotations

import pathlib
import re
from typing import Any

from jinja2 import Environment, FileSystemLoader


_TEMPLATE_DIR = pathlib.Path(__file__).parent.parent / "templates"


def render_skill(data: dict[str, Any]) -> str:
    """Render structured data into a Claude Code skill markdown file."""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("skill.md.jinja")

    metadata = (data.get("layers") or {}).get("agent_metadata") or {}
    distillation = (data.get("layers") or {}).get("distillation") or {}

    claims = metadata.get("key_claims") or []
    description = claims[0] if claims else data.get("title", "")

    context = {
        "title": data.get("title", ""),
        "description": description,
        "url": data.get("url", ""),
        "category": data.get("category"),
        "content_type": metadata.get("content_type"),
        "tags": metadata.get("tags"),
        "key_claims": metadata.get("key_claims"),
        "taste_signals": metadata.get("taste_signals"),
        "reuse_contexts": metadata.get("reuse_contexts"),
        "quality_score": metadata.get("quality_score"),
        "distillation": distillation,
        "agent_metadata": metadata,
    }

    result = template.render(**context)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip() + "\n"
