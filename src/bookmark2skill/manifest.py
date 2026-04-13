from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone
from typing import Any


class Manifest:
    """Tracks bookmark processing state in a JSON file."""

    def __init__(self, path: str | pathlib.Path) -> None:
        self._path = pathlib.Path(path)
        self._data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if self._path.is_file():
            with open(self._path, encoding="utf-8") as f:
                return json.load(f)
        data = {"version": 1, "bookmarks": {}}
        self._save(data)
        return data

    def _save(self, data: dict[str, Any] | None = None) -> None:
        if data is None:
            data = self._data
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Auto-backup before overwrite
        if self._path.is_file():
            bak = self._path.with_suffix(".json.bak")
            bak.write_bytes(self._path.read_bytes())
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def add(self, url: str, *, title: str, folder: str, source: str = "") -> bool:
        """Add a bookmark as pending. Returns False if URL already exists."""
        if url in self._data["bookmarks"]:
            return False
        self._data["bookmarks"][url] = {
            "title": title,
            "folder": folder,
            "source": source,
            "date_discovered": self._now(),
            "status": "pending",
        }
        self._save()
        return True

    def get(self, url: str) -> dict[str, Any] | None:
        return self._data["bookmarks"].get(url)

    def mark_done(
        self,
        url: str,
        *,
        obsidian_path: str = "",
        skill_path: str = "",
    ) -> None:
        entry = self._data["bookmarks"][url]
        entry["status"] = "done"
        entry["date_processed"] = self._now()
        entry["outputs"] = {
            "obsidian": obsidian_path,
            "skill": skill_path,
        }
        self._save()

    def mark_failed(self, url: str, *, reason: str = "") -> None:
        entry = self._data["bookmarks"][url]
        entry["status"] = "failed"
        entry["date_failed"] = self._now()
        entry["fail_reason"] = reason
        self._save()

    def summary(self) -> dict[str, int]:
        counts = {"pending": 0, "done": 0, "failed": 0}
        for entry in self._data["bookmarks"].values():
            status = entry["status"]
            counts[status] = counts.get(status, 0) + 1
        counts["total"] = sum(counts.values())
        return counts

    def pending_urls(self) -> list[str]:
        return [
            url
            for url, entry in self._data["bookmarks"].items()
            if entry["status"] == "pending"
        ]

    def all_urls(self) -> set[str]:
        return set(self._data["bookmarks"].keys())
