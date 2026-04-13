import pytest
from bookmark2skill.parsers.chrome_json import parse_chrome_json


def test_parse_flat_bookmarks(chrome_bookmarks_file):
    """Parses top-level bookmarks from bookmark bar."""
    results = parse_chrome_json(chrome_bookmarks_file)
    urls = [b["url"] for b in results]
    assert "https://example.com/article" in urls


def test_parse_nested_bookmarks(chrome_bookmarks_file):
    """Parses bookmarks inside folders with correct folder path."""
    results = parse_chrome_json(chrome_bookmarks_file)
    nested = [b for b in results if b["url"] == "https://example.com/nested"][0]
    assert nested["folder"] == "Bookmarks bar/Tech"
    assert nested["title"] == "Nested Article"


def test_returns_date_added(chrome_bookmarks_file):
    """Each bookmark includes a parsed date_added."""
    results = parse_chrome_json(chrome_bookmarks_file)
    for b in results:
        assert "date_added" in b
        assert b["date_added"] is not None


def test_empty_bookmarks(tmp_path):
    """Handles Chrome file with no bookmarks gracefully."""
    f = tmp_path / "Bookmarks"
    f.write_text('{"roots":{"bookmark_bar":{"children":[],"type":"folder"},"other":{"children":[],"type":"folder"},"synced":{"children":[],"type":"folder"}},"version":1}')
    results = parse_chrome_json(f)
    assert results == []


def test_returns_expected_fields(chrome_bookmarks_file):
    """Each bookmark dict has url, title, folder, date_added keys."""
    results = parse_chrome_json(chrome_bookmarks_file)
    for b in results:
        assert set(b.keys()) == {"url", "title", "folder", "date_added"}
