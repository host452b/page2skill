from __future__ import annotations

import pathlib
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any


def _unix_ts_to_iso(ts_str: str) -> str:
    """Convert Unix timestamp string to ISO 8601."""
    try:
        ts = int(ts_str)
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except (ValueError, OSError):
        return ""


class _BookmarkHTMLParser(HTMLParser):
    """Parse Netscape bookmark HTML format."""

    def __init__(self) -> None:
        super().__init__()
        self.bookmarks: list[dict[str, str]] = []
        self._folder_stack: list[str] = []
        self._current_link: dict[str, str] | None = None
        self._in_h3 = False
        self._h3_text = ""
        self._expect_folder_dl = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        tag_lower = tag.lower()
        if tag_lower == "a" and "href" in attr_dict:
            self._current_link = {
                "url": attr_dict["href"] or "",
                "title": "",
                "folder": "/".join(self._folder_stack),
                "date_added": _unix_ts_to_iso(attr_dict.get("add_date", "0")),
            }
        elif tag_lower == "h3":
            self._in_h3 = True
            self._h3_text = ""
        elif tag_lower == "dl":
            if self._expect_folder_dl:
                self._expect_folder_dl = False

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower == "a" and self._current_link:
            self.bookmarks.append(self._current_link)
            self._current_link = None
        elif tag_lower == "h3":
            self._in_h3 = False
            self._folder_stack.append(self._h3_text)
            self._expect_folder_dl = True
        elif tag_lower == "dl" and self._folder_stack:
            self._folder_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._current_link is not None:
            self._current_link["title"] += data
        elif self._in_h3:
            self._h3_text += data


def parse_html_export(path: str | pathlib.Path) -> list[dict[str, str]]:
    """Parse Netscape HTML bookmark export and return flat list of bookmarks."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    parser = _BookmarkHTMLParser()
    parser.feed(text)
    return parser.bookmarks
