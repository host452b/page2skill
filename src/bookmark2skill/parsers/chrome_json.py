from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone
from typing import Any


def _chrome_timestamp_to_iso(chrome_ts: str) -> str:
    """Convert Chrome's microsecond-since-1601 timestamp to ISO 8601."""
    try:
        ts = int(chrome_ts)
        unix_ts = (ts / 1_000_000) - 11644473600
        return datetime.fromtimestamp(unix_ts, tz=timezone.utc).isoformat()
    except (ValueError, OSError):
        return ""


def _walk(node: dict[str, Any], folder_path: str) -> list[dict[str, str]]:
    """Recursively walk bookmark tree, collecting URL entries."""
    results: list[dict[str, str]] = []
    if node.get("type") == "url":
        results.append({
            "url": node["url"],
            "title": node.get("name", ""),
            "folder": folder_path,
            "date_added": _chrome_timestamp_to_iso(node.get("date_added", "0")),
        })
    elif node.get("type") == "folder":
        child_path = f"{folder_path}/{node['name']}" if folder_path else node.get("name", "")
        for child in node.get("children", []):
            results.extend(_walk(child, child_path))
    return results


def parse_chrome_json(path: str | pathlib.Path) -> list[dict[str, str]]:
    """Parse Chrome's Bookmarks JSON file and return flat list of bookmarks."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    results: list[dict[str, str]] = []
    for root_name, root_node in data.get("roots", {}).items():
        if isinstance(root_node, dict) and root_node.get("type") == "folder":
            results.extend(_walk(root_node, ""))
    return results
