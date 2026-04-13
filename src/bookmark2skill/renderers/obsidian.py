from __future__ import annotations

import json as _json
import pathlib
import re
from typing import Any

from jinja2 import Environment, FileSystemLoader


_TEMPLATE_DIR = pathlib.Path(__file__).parent.parent / "templates"


def _tojson_utf8(value: Any) -> str:
    """JSON serialize preserving non-ASCII characters (Chinese, etc.)."""
    return _json.dumps(value, ensure_ascii=False)


def render_obsidian(data: dict[str, Any]) -> str:
    """Render structured data into an Obsidian-compatible markdown note."""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["tojson"] = _tojson_utf8
    template = env.get_template("obsidian.md.jinja")

    metadata = (data.get("layers") or {}).get("agent_metadata") or {}
    context = {
        **data,
        "tags": metadata.get("tags"),
    }
    result = template.render(**context)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip() + "\n"
