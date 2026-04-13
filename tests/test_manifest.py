# tests/test_manifest.py
import json
import pytest
from bookmark2skill.manifest import Manifest


def test_create_new_manifest(tmp_home):
    """Creates a new manifest file if none exists."""
    path = tmp_home / ".bookmark2skill" / "manifest.json"
    m = Manifest(path)
    assert path.is_file()
    data = json.loads(path.read_text())
    assert data["version"] == 1
    assert data["bookmarks"] == {}


def test_add_pending_bookmark(tmp_home):
    """Adding a bookmark sets status to pending."""
    path = tmp_home / ".bookmark2skill" / "manifest.json"
    m = Manifest(path)
    m.add("https://example.com/a", title="Article A", folder="tech")
    entry = m.get("https://example.com/a")
    assert entry["status"] == "pending"
    assert entry["title"] == "Article A"
    assert entry["folder"] == "tech"


def test_add_skips_existing(tmp_home):
    """Adding an already-existing URL does not overwrite it."""
    path = tmp_home / ".bookmark2skill" / "manifest.json"
    m = Manifest(path)
    m.add("https://example.com/a", title="Original", folder="tech")
    m.add("https://example.com/a", title="Overwrite Attempt", folder="misc")
    assert m.get("https://example.com/a")["title"] == "Original"


def test_mark_done(tmp_home):
    """mark_done updates status and records output paths."""
    path = tmp_home / ".bookmark2skill" / "manifest.json"
    m = Manifest(path)
    m.add("https://example.com/a", title="A", folder="tech")
    m.mark_done(
        "https://example.com/a",
        obsidian_path="/vault/a.md",
        skill_path="/skills/a.md",
    )
    entry = m.get("https://example.com/a")
    assert entry["status"] == "done"
    assert entry["outputs"]["obsidian"] == "/vault/a.md"
    assert entry["outputs"]["skill"] == "/skills/a.md"
    assert "date_processed" in entry


def test_mark_failed(tmp_home):
    """mark_failed updates status and records reason."""
    path = tmp_home / ".bookmark2skill" / "manifest.json"
    m = Manifest(path)
    m.add("https://example.com/a", title="A", folder="tech")
    m.mark_failed("https://example.com/a", reason="HTTP 404")
    entry = m.get("https://example.com/a")
    assert entry["status"] == "failed"
    assert entry["fail_reason"] == "HTTP 404"


def test_summary(tmp_home):
    """summary returns counts by status."""
    path = tmp_home / ".bookmark2skill" / "manifest.json"
    m = Manifest(path)
    m.add("https://example.com/a", title="A", folder="x")
    m.add("https://example.com/b", title="B", folder="x")
    m.add("https://example.com/c", title="C", folder="x")
    m.mark_done("https://example.com/a", obsidian_path="/a.md", skill_path="/s.md")
    m.mark_failed("https://example.com/b", reason="timeout")
    s = m.summary()
    assert s["done"] == 1
    assert s["failed"] == 1
    assert s["pending"] == 1
    assert s["total"] == 3


def test_pending_urls(tmp_home):
    """pending_urls returns only URLs with pending status."""
    path = tmp_home / ".bookmark2skill" / "manifest.json"
    m = Manifest(path)
    m.add("https://example.com/a", title="A", folder="x")
    m.add("https://example.com/b", title="B", folder="x")
    m.mark_done("https://example.com/a", obsidian_path="/a.md", skill_path="/s.md")
    pending = m.pending_urls()
    assert pending == ["https://example.com/b"]


def test_persistence(tmp_home):
    """Manifest persists to disk and reloads correctly."""
    path = tmp_home / ".bookmark2skill" / "manifest.json"
    m1 = Manifest(path)
    m1.add("https://example.com/a", title="A", folder="tech")
    m2 = Manifest(path)
    assert m2.get("https://example.com/a")["title"] == "A"
