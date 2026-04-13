from __future__ import annotations

import pathlib
import re
from typing import Any

from jinja2 import Environment, FileSystemLoader


_TEMPLATE_DIR = pathlib.Path(__file__).parent.parent / "templates"


def render_obsidian(data: dict[str, Any]) -> str:
    """Render structured data into an Obsidian-compatible markdown note."""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("obsidian.md.jinja")

    metadata = (data.get("layers") or {}).get("agent_metadata") or {}
    context = {
        **data,
        "tags": metadata.get("tags"),
    }
    result = template.render(**context)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip() + "\n"
