import pytest
from bookmark2skill.parsers.html_export import parse_html_export


def test_parse_flat_bookmarks(html_bookmarks_file):
    """Parses top-level bookmarks."""
    results = parse_html_export(html_bookmarks_file)
    urls = [b["url"] for b in results]
    assert "https://example.com/article" in urls


def test_parse_nested_bookmarks(html_bookmarks_file):
    """Parses bookmarks inside folders with correct folder path."""
    results = parse_html_export(html_bookmarks_file)
    nested = [b for b in results if b["url"] == "https://example.com/nested"][0]
    assert "Tech" in nested["folder"]
    assert nested["title"] == "Nested Article"


def test_returns_date_added(html_bookmarks_file):
    """Each bookmark includes date_added from ADD_DATE attribute."""
    results = parse_html_export(html_bookmarks_file)
    for b in results:
        assert "date_added" in b


def test_empty_html(tmp_path):
    """Handles empty bookmark HTML gracefully."""
    f = tmp_path / "empty.html"
    f.write_text(
        '<!DOCTYPE NETSCAPE-Bookmark-file-1>\n<TITLE>Bookmarks</TITLE>\n<DL><p></DL><p>',
        encoding="utf-8",
    )
    results = parse_html_export(f)
    assert results == []


def test_same_output_format_as_chrome_parser(html_bookmarks_file):
    """Output fields match Chrome JSON parser format."""
    results = parse_html_export(html_bookmarks_file)
    for b in results:
        assert set(b.keys()) == {"url", "title", "folder", "date_added"}
