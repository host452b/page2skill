# tests/conftest.py
import json
import pathlib
import pytest


@pytest.fixture
def tmp_home(tmp_path):
    """Temporary home directory with .bookmark2skill/ structure."""
    b2s_dir = tmp_path / ".bookmark2skill"
    b2s_dir.mkdir()
    return tmp_path


@pytest.fixture
def sample_chrome_bookmarks():
    """Minimal Chrome bookmark JSON structure."""
    return {
        "checksum": "abc123",
        "roots": {
            "bookmark_bar": {
                "children": [
                    {
                        "date_added": "13350000000000000",
                        "date_last_used": "0",
                        "guid": "00000000-0000-0000-0000-000000000001",
                        "name": "Example Article",
                        "type": "url",
                        "url": "https://example.com/article"
                    },
                    {
                        "children": [
                            {
                                "date_added": "13350000000000000",
                                "date_last_used": "0",
                                "guid": "00000000-0000-0000-0000-000000000002",
                                "name": "Nested Article",
                                "type": "url",
                                "url": "https://example.com/nested"
                            }
                        ],
                        "date_added": "13350000000000000",
                        "date_modified": "13350000000000000",
                        "guid": "00000000-0000-0000-0000-000000000003",
                        "name": "Tech",
                        "type": "folder"
                    }
                ],
                "date_added": "13350000000000000",
                "date_modified": "13350000000000000",
                "guid": "00000000-0000-0000-0000-000000000004",
                "name": "Bookmarks bar",
                "type": "folder"
            },
            "other": {
                "children": [],
                "date_added": "13350000000000000",
                "date_modified": "0",
                "guid": "00000000-0000-0000-0000-000000000005",
                "name": "Other bookmarks",
                "type": "folder"
            },
            "synced": {
                "children": [],
                "date_added": "13350000000000000",
                "date_modified": "0",
                "guid": "00000000-0000-0000-0000-000000000006",
                "name": "Mobile bookmarks",
                "type": "folder"
            }
        },
        "version": 1
    }


@pytest.fixture
def sample_distilled_data():
    """Sample structured JSON that an AI agent would produce."""
    return {
        "url": "https://example.com/article",
        "title": "Simplicity is the ultimate sophistication",
        "date_processed": "2026-04-13T12:00:00Z",
        "original_title": "On System Design",
        "author": ["Jane Doe"],
        "language": "en",
        "category": "engineering/system-design",
        "layers": {
            "distillation": {
                "logic_chain": [
                    "Complex systems fail in complex ways",
                    "Therefore, reduce moving parts",
                    "Simplicity is a feature, not a compromise"
                ],
                "brilliant_quotes": [
                    {
                        "text": "The best code is no code at all.",
                        "why": "Concise expression of YAGNI principle"
                    }
                ],
                "narrative_craft": ["Uses concrete war stories to build credibility"],
                "concrete_examples": [
                    "Netflix's circuit breaker pattern reduced cascading failures by 70%"
                ],
                "counterpoints": [
                    "Author acknowledges simplicity can be premature in exploratory phases"
                ],
                "overlooked_details": ["Mentions Hystrix library v1.5 configuration"]
            },
            "agent_metadata": {
                "tags": ["system-design", "simplicity", "reliability"],
                "content_type": "technical-article",
                "key_claims": [
                    "Simplicity in system design directly correlates with reliability",
                    "Most system failures come from unnecessary complexity"
                ],
                "taste_signals": {
                    "aesthetic": ["minimalism", "clarity"],
                    "intellectual": ["first-principles", "empiricism"],
                    "values": ["anti-complexity", "pragmatism"]
                },
                "reuse_contexts": [
                    {
                        "situation": "Making architecture decisions",
                        "how": "Use as argument for simpler approach"
                    }
                ],
                "related_concepts": ["YAGNI", "KISS", "circuit-breaker"],
                "quality_score": {
                    "depth": 4,
                    "originality": 3,
                    "practicality": 5,
                    "writing": 4
                }
            }
        }
    }


@pytest.fixture
def sample_minimal_data():
    """Minimal valid structured JSON — only required fields."""
    return {
        "url": "https://example.com/minimal",
        "title": "Minimal Article",
        "date_processed": "2026-04-13T12:00:00Z"
    }


@pytest.fixture
def chrome_bookmarks_file(tmp_path, sample_chrome_bookmarks):
    """Write sample Chrome bookmarks to a temp file."""
    f = tmp_path / "Bookmarks"
    f.write_text(json.dumps(sample_chrome_bookmarks), encoding="utf-8")
    return f


@pytest.fixture
def html_bookmarks_file(tmp_path):
    """Write sample Netscape HTML bookmarks to a temp file."""
    html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3 ADD_DATE="1713000000" LAST_MODIFIED="1713000000">Bookmarks bar</H3>
    <DL><p>
        <DT><A HREF="https://example.com/article" ADD_DATE="1713000000">Example Article</A>
        <DT><H3 ADD_DATE="1713000000" LAST_MODIFIED="1713000000">Tech</H3>
        <DL><p>
            <DT><A HREF="https://example.com/nested" ADD_DATE="1713000000">Nested Article</A>
        </DL><p>
    </DL><p>
</DL><p>"""
    f = tmp_path / "bookmarks.html"
    f.write_text(html, encoding="utf-8")
    return f
