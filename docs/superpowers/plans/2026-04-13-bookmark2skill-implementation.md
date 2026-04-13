# bookmark2skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI tool that converts Chrome bookmarks into Obsidian notes and Claude Code skills, with incremental tracking and tiered scraping.

**Architecture:** Standalone CLI with atomic subcommands (`list`, `fetch`, `write-obsidian`, `write-skill`, `status`, `mark-done`, `mark-failed`). AI agents call these commands to orchestrate bookmark-to-knowledge pipelines. Tool does not call any LLM API — it handles parsing, scraping, file I/O, and state tracking only.

**Tech Stack:** Python 3.10+, click (CLI), httpx (HTTP), readability-lxml (content extraction), jinja2 (templates), tomli (TOML config)

---

## File Structure

```
bookmark2skill/
├── pyproject.toml                          # Package config, dependencies, entry point
├── CHANGELOG.md                            # (exists) Design decisions and rationale
├── src/
│   └── bookmark2skill/
│       ├── __init__.py                     # Version only
│       ├── cli.py                          # Click CLI group + all subcommands
│       ├── config.py                       # Layered config: toml → env → flags
│       ├── schema.py                       # JSON validation for structured input
│       ├── manifest.py                     # Incremental state tracking (manifest.json)
│       ├── parsers/
│       │   ├── __init__.py
│       │   ├── chrome_json.py              # Parse Chrome's local Bookmarks JSON
│       │   └── html_export.py              # Parse Netscape HTML bookmark export
│       ├── fetcher.py                      # Tiered scraping: httpx+readability → Playwright
│       ├── renderers/
│       │   ├── __init__.py
│       │   ├── obsidian.py                 # Render structured data → Obsidian note
│       │   └── skill.py                    # Render structured data → Claude Code skill
│       └── templates/
│           ├── obsidian.md.jinja           # Obsidian output template
│           └── skill.md.jinja              # Skill output template
├── tests/
│   ├── conftest.py                         # Shared fixtures (tmp dirs, sample data)
│   ├── test_config.py
│   ├── test_schema.py
│   ├── test_manifest.py
│   ├── test_chrome_json.py
│   ├── test_html_export.py
│   ├── test_fetcher.py
│   ├── test_obsidian_renderer.py
│   ├── test_skill_renderer.py
│   ├── test_cli.py                         # Integration tests for all CLI commands
│   └── fixtures/
│       ├── chrome_bookmarks.json           # Sample Chrome bookmark file
│       ├── bookmarks.html                  # Sample HTML bookmark export
│       └── sample_distilled.json           # Sample structured JSON input
├── defaults/
│   ├── config.toml                         # Default config template
│   └── taxonomy.toml                       # Default taxonomy
└── docs/
    └── agent-guide.md                      # How AI agents should use this tool
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/bookmark2skill/__init__.py`
- Create: `src/bookmark2skill/cli.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "bookmark2skill"
version = "0.1.0"
description = "Convert Chrome bookmarks into Obsidian notes and Claude Code skills"
requires-python = ">=3.10"
dependencies = [
    "click>=8.0",
    "httpx>=0.27",
    "readability-lxml>=0.8",
    "jinja2>=3.1",
    "tomli>=2.0;python_version<'3.11'",
]

[project.optional-dependencies]
browser = ["playwright>=1.40"]
dev = ["pytest>=8.0", "pytest-tmp-files>=0.0.2"]

[project.scripts]
bookmark2skill = "bookmark2skill.cli:cli"

[tool.hatch.build.targets.wheel]
packages = ["src/bookmark2skill"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create __init__.py**

```python
# src/bookmark2skill/__init__.py
__version__ = "0.1.0"
```

- [ ] **Step 3: Create minimal CLI entry point**

```python
# src/bookmark2skill/cli.py
import click


@click.group()
@click.version_option(package_name="bookmark2skill")
def cli():
    """Convert Chrome bookmarks into Obsidian notes and Claude Code skills."""
    pass
```

- [ ] **Step 4: Create test conftest with shared fixtures**

```python
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
```

- [ ] **Step 5: Install in dev mode and verify CLI works**

Run: `cd . && pip install -e ".[dev]"`

Then: `bookmark2skill --version`

Expected: `bookmark2skill, version 0.1.0`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/ tests/conftest.py
git commit -m "feat: project scaffolding with CLI entry point and test fixtures"
```

---

### Task 2: Config Module

**Files:**
- Create: `src/bookmark2skill/config.py`
- Create: `tests/test_config.py`
- Create: `defaults/config.toml`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_config.py
import os
import pytest
from bookmark2skill.config import load_config


def test_load_defaults_when_no_config_exists(tmp_home):
    """Config returns sensible defaults when no config file exists."""
    cfg = load_config(home_dir=tmp_home)
    assert cfg["vault_path"] is None
    assert cfg["skill_dir"] is None
    assert cfg["manifest_path"] == str(tmp_home / ".bookmark2skill" / "manifest.json")
    assert cfg["taxonomy_path"] == str(tmp_home / ".bookmark2skill" / "taxonomy.toml")


def test_load_from_toml(tmp_home):
    """Config reads values from config.toml."""
    config_dir = tmp_home / ".bookmark2skill"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "config.toml").write_text(
        '[paths]\nvault_path = "/my/vault"\nskill_dir = "/my/skills"\n',
        encoding="utf-8",
    )
    cfg = load_config(home_dir=tmp_home)
    assert cfg["vault_path"] == "/my/vault"
    assert cfg["skill_dir"] == "/my/skills"


def test_env_vars_override_toml(tmp_home, monkeypatch):
    """Environment variables override config.toml values."""
    config_dir = tmp_home / ".bookmark2skill"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "config.toml").write_text(
        '[paths]\nvault_path = "/from/toml"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("BOOKMARK2SKILL_VAULT_PATH", "/from/env")
    cfg = load_config(home_dir=tmp_home)
    assert cfg["vault_path"] == "/from/env"


def test_cli_overrides_take_highest_priority(tmp_home, monkeypatch):
    """CLI-provided overrides beat env vars and toml."""
    monkeypatch.setenv("BOOKMARK2SKILL_VAULT_PATH", "/from/env")
    cfg = load_config(home_dir=tmp_home, overrides={"vault_path": "/from/cli"})
    assert cfg["vault_path"] == "/from/cli"


def test_chrome_profile_auto_detect(tmp_home):
    """Chrome profile path is auto-detected for the current OS."""
    cfg = load_config(home_dir=tmp_home)
    assert cfg["chrome_profile"] is not None
    assert "Chrome" in cfg["chrome_profile"] or "chrome" in cfg["chrome_profile"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'bookmark2skill.config'`

- [ ] **Step 3: Implement config module**

```python
# src/bookmark2skill/config.py
from __future__ import annotations

import os
import platform
import pathlib
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


_DEFAULTS = {
    "vault_path": None,
    "skill_dir": None,
    "manifest_path": None,  # computed from home_dir
    "taxonomy_path": None,  # computed from home_dir
    "chrome_profile": None,  # auto-detected
}

_ENV_PREFIX = "BOOKMARK2SKILL_"


def _detect_chrome_profile() -> str:
    """Return default Chrome profile path for current OS."""
    system = platform.system()
    home = pathlib.Path.home()
    if system == "Darwin":
        return str(home / "Library/Application Support/Google/Chrome/Default")
    elif system == "Linux":
        return str(home / ".config/google-chrome/Default")
    elif system == "Windows":
        local = os.environ.get("LOCALAPPDATA", "")
        return str(pathlib.Path(local) / "Google/Chrome/User Data/Default")
    return str(home / ".config/google-chrome/Default")


def _read_toml(config_path: pathlib.Path) -> dict[str, Any]:
    """Read config.toml and flatten [paths] section to top-level keys."""
    if not config_path.is_file():
        return {}
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    flat: dict[str, Any] = {}
    for key, value in data.get("paths", {}).items():
        flat[key] = value
    return flat


def _read_env() -> dict[str, str]:
    """Read BOOKMARK2SKILL_* env vars into a flat dict."""
    result: dict[str, str] = {}
    for key, value in os.environ.items():
        if key.startswith(_ENV_PREFIX):
            config_key = key[len(_ENV_PREFIX):].lower()
            result[config_key] = value
    return result


def load_config(
    *,
    home_dir: pathlib.Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load config with layered precedence: defaults < toml < env < overrides."""
    home = pathlib.Path(home_dir) if home_dir else pathlib.Path.home()
    b2s_dir = home / ".bookmark2skill"

    # Start with defaults
    cfg = dict(_DEFAULTS)
    cfg["manifest_path"] = str(b2s_dir / "manifest.json")
    cfg["taxonomy_path"] = str(b2s_dir / "taxonomy.toml")
    cfg["chrome_profile"] = _detect_chrome_profile()

    # Layer 1: config.toml
    toml_values = _read_toml(b2s_dir / "config.toml")
    for key, value in toml_values.items():
        if key in cfg:
            cfg[key] = value

    # Layer 2: environment variables
    env_values = _read_env()
    for key, value in env_values.items():
        if key in cfg:
            cfg[key] = value

    # Layer 3: CLI overrides (highest priority)
    if overrides:
        for key, value in overrides.items():
            if key in cfg and value is not None:
                cfg[key] = value

    return cfg
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config.py -v`

Expected: all 5 tests PASS

- [ ] **Step 5: Create default config template**

```toml
# defaults/config.toml
# bookmark2skill configuration
# Copy to ~/.bookmark2skill/config.toml and edit

[paths]
# Obsidian vault path — where human-readable notes are written
# vault_path = "/path/to/your/obsidian/vault"

# Skill output directory — where AI-agent-friendly skill files are written
# skill_dir = "/path/to/your/skills"

# Chrome profile directory (auto-detected if omitted)
# chrome_profile = "~/Library/Application Support/Google/Chrome/Default"
```

- [ ] **Step 6: Commit**

```bash
git add src/bookmark2skill/config.py tests/test_config.py defaults/config.toml
git commit -m "feat: layered config module (toml → env → CLI overrides)"
```

---

### Task 3: Schema Validation

**Files:**
- Create: `src/bookmark2skill/schema.py`
- Create: `tests/test_schema.py`
- Create: `tests/fixtures/sample_distilled.json`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_schema.py
import pytest
from bookmark2skill.schema import validate, ValidationError


def test_valid_full_data(sample_distilled_data):
    """Full structured data passes validation."""
    result = validate(sample_distilled_data)
    assert result["url"] == "https://example.com/article"
    assert result["title"] == "Simplicity is the ultimate sophistication"


def test_valid_minimal_data(sample_minimal_data):
    """Minimal data (only required fields) passes validation."""
    result = validate(sample_minimal_data)
    assert result["url"] == "https://example.com/minimal"
    assert result.get("author") is None


def test_missing_url_raises():
    """Missing required field 'url' raises ValidationError."""
    with pytest.raises(ValidationError, match="url"):
        validate({"title": "Test", "date_processed": "2026-04-13T12:00:00Z"})


def test_missing_title_raises():
    """Missing required field 'title' raises ValidationError."""
    with pytest.raises(ValidationError, match="title"):
        validate({"url": "https://x.com", "date_processed": "2026-04-13T12:00:00Z"})


def test_missing_date_processed_raises():
    """Missing required field 'date_processed' raises ValidationError."""
    with pytest.raises(ValidationError, match="date_processed"):
        validate({"url": "https://x.com", "title": "Test"})


def test_empty_optional_fields_are_ok():
    """Optional fields can be null, empty arrays, or omitted."""
    data = {
        "url": "https://example.com/test",
        "title": "Test",
        "date_processed": "2026-04-13T12:00:00Z",
        "author": [],
        "layers": {
            "distillation": {
                "logic_chain": [],
                "brilliant_quotes": [],
                "counterpoints": None,
            },
            "agent_metadata": {
                "tags": [],
                "taste_signals": {
                    "aesthetic": [],
                    "intellectual": None,
                    "values": [],
                },
            },
        },
    }
    result = validate(data)
    assert result["author"] == []
    assert result["layers"]["distillation"]["counterpoints"] is None


def test_quality_score_range():
    """Quality score values must be 1-5 if provided."""
    data = {
        "url": "https://example.com/test",
        "title": "Test",
        "date_processed": "2026-04-13T12:00:00Z",
        "layers": {
            "agent_metadata": {
                "quality_score": {"depth": 6, "originality": 3}
            }
        },
    }
    with pytest.raises(ValidationError, match="quality_score"):
        validate(data)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_schema.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'bookmark2skill.schema'`

- [ ] **Step 3: Implement schema module**

```python
# src/bookmark2skill/schema.py
from __future__ import annotations

from typing import Any


class ValidationError(Exception):
    """Raised when structured data fails validation."""
    pass


_REQUIRED_FIELDS = ("url", "title", "date_processed")


def _validate_quality_score(score: dict[str, Any]) -> None:
    """Check quality_score values are in 1-5 range."""
    for key, value in score.items():
        if value is not None and not (1 <= value <= 5):
            raise ValidationError(
                f"quality_score.{key} must be 1-5, got {value}"
            )


def validate(data: dict[str, Any]) -> dict[str, Any]:
    """Validate structured JSON data against the bookmark2skill schema.

    Required fields: url, title, date_processed.
    All other fields are optional (null, empty array, or omitted).
    Returns the data unchanged if valid.
    """
    for field in _REQUIRED_FIELDS:
        if field not in data or data[field] is None:
            raise ValidationError(f"Required field missing: {field}")

    # Validate quality_score range if present
    metadata = (data.get("layers") or {}).get("agent_metadata") or {}
    quality = metadata.get("quality_score")
    if quality and isinstance(quality, dict):
        _validate_quality_score(quality)

    return data
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_schema.py -v`

Expected: all 7 tests PASS

- [ ] **Step 5: Write sample fixture file**

```json
// tests/fixtures/sample_distilled.json
// (same as sample_distilled_data fixture in conftest.py — for CLI integration tests)
```

Write `tests/fixtures/sample_distilled.json` with the content from `sample_distilled_data` fixture in conftest.py.

- [ ] **Step 6: Commit**

```bash
git add src/bookmark2skill/schema.py tests/test_schema.py tests/fixtures/
git commit -m "feat: schema validation with required fields and quality_score range check"
```

---

### Task 4: Manifest Module

**Files:**
- Create: `src/bookmark2skill/manifest.py`
- Create: `tests/test_manifest.py`

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_manifest.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'bookmark2skill.manifest'`

- [ ] **Step 3: Implement manifest module**

```python
# src/bookmark2skill/manifest.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_manifest.py -v`

Expected: all 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/bookmark2skill/manifest.py tests/test_manifest.py
git commit -m "feat: manifest module for incremental bookmark tracking"
```

---

### Task 5: Chrome JSON Parser

**Files:**
- Create: `src/bookmark2skill/parsers/__init__.py`
- Create: `src/bookmark2skill/parsers/chrome_json.py`
- Create: `tests/test_chrome_json.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_chrome_json.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_chrome_json.py -v`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement Chrome JSON parser**

```python
# src/bookmark2skill/parsers/__init__.py
```

```python
# src/bookmark2skill/parsers/chrome_json.py
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone
from typing import Any


def _chrome_timestamp_to_iso(chrome_ts: str) -> str:
    """Convert Chrome's microsecond-since-1601 timestamp to ISO 8601."""
    try:
        ts = int(chrome_ts)
        # Chrome epoch is 1601-01-01, Unix epoch is 1970-01-01
        # Difference: 11644473600 seconds
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_chrome_json.py -v`

Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/bookmark2skill/parsers/ tests/test_chrome_json.py
git commit -m "feat: Chrome JSON bookmark parser"
```

---

### Task 6: HTML Export Parser

**Files:**
- Create: `src/bookmark2skill/parsers/html_export.py`
- Create: `tests/test_html_export.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_html_export.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_html_export.py -v`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement HTML export parser**

```python
# src/bookmark2skill/parsers/html_export.py
from __future__ import annotations

import pathlib
import re
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_html_export.py -v`

Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/bookmark2skill/parsers/html_export.py tests/test_html_export.py
git commit -m "feat: Netscape HTML bookmark export parser"
```

---

### Task 7: `list` CLI Command

**Files:**
- Modify: `src/bookmark2skill/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cli.py
import json
import pytest
from click.testing import CliRunner
from bookmark2skill.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestListCommand:
    def test_list_from_chrome_json(self, runner, chrome_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        result = runner.invoke(cli, [
            "list",
            "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        urls = [b["url"] for b in data]
        assert "https://example.com/article" in urls
        assert "https://example.com/nested" in urls

    def test_list_from_html(self, runner, html_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        result = runner.invoke(cli, [
            "list",
            "--source", str(html_bookmarks_file),
            "--manifest-path", manifest_path,
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) >= 2

    def test_list_marks_new_as_pending_in_manifest(self, runner, chrome_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        runner.invoke(cli, [
            "list",
            "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
        ])
        manifest_data = json.loads(open(manifest_path).read())
        for entry in manifest_data["bookmarks"].values():
            assert entry["status"] == "pending"

    def test_list_skips_existing_urls(self, runner, chrome_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        # Run twice
        runner.invoke(cli, [
            "list", "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
        ])
        result = runner.invoke(cli, [
            "list", "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
            "--only-new",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 0  # All already in manifest
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py::TestListCommand -v`

Expected: FAIL — `no attribute 'list'` on cli group

- [ ] **Step 3: Implement list command**

```python
# src/bookmark2skill/cli.py
import json
import pathlib

import click

from bookmark2skill.config import load_config
from bookmark2skill.manifest import Manifest
from bookmark2skill.parsers.chrome_json import parse_chrome_json
from bookmark2skill.parsers.html_export import parse_html_export


@click.group()
@click.version_option(package_name="bookmark2skill")
def cli():
    """Convert Chrome bookmarks into Obsidian notes and Claude Code skills."""
    pass


def _detect_source_type(source: str) -> str:
    """Detect whether source is a Chrome JSON file or HTML export."""
    if source.lower() == "chrome":
        return "chrome"
    path = pathlib.Path(source)
    if path.suffix.lower() in (".html", ".htm"):
        return "html"
    # Try reading first bytes to detect JSON
    try:
        with open(path, "rb") as f:
            first = f.read(10).strip()
        if first.startswith(b"{"):
            return "chrome_json"
    except OSError:
        pass
    return "html"


@cli.command()
@click.option("--source", required=True, help="'chrome' for auto-detect, or path to bookmark file")
@click.option("--manifest-path", default=None, help="Override manifest file path")
@click.option("--chrome-profile", default=None, help="Override Chrome profile directory")
@click.option("--only-new", is_flag=True, help="Only output bookmarks not yet in manifest")
def list(source: str, manifest_path: str | None, chrome_profile: str | None, only_new: bool):
    """Parse bookmarks and output as JSON. Registers new bookmarks in manifest."""
    cfg = load_config(overrides={
        "manifest_path": manifest_path,
        "chrome_profile": chrome_profile,
    })
    manifest = Manifest(cfg["manifest_path"])
    existing_urls = manifest.all_urls()

    # Parse source
    source_type = _detect_source_type(source)
    if source_type == "chrome":
        chrome_dir = pathlib.Path(cfg["chrome_profile"])
        bookmarks_file = chrome_dir / "Bookmarks"
        if not bookmarks_file.is_file():
            raise click.ClickException(f"Chrome bookmarks not found at {bookmarks_file}")
        bookmarks = parse_chrome_json(bookmarks_file)
    elif source_type == "chrome_json":
        bookmarks = parse_chrome_json(source)
    else:
        bookmarks = parse_html_export(source)

    # Register in manifest and filter
    new_bookmarks = []
    for b in bookmarks:
        was_new = manifest.add(url=b["url"], title=b["title"], folder=b["folder"])
        if only_new and not was_new:
            continue
        if not only_new or was_new:
            new_bookmarks.append(b)

    output = new_bookmarks if only_new else bookmarks
    click.echo(json.dumps(output, ensure_ascii=False, indent=2))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py::TestListCommand -v`

Expected: all 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/bookmark2skill/cli.py tests/test_cli.py
git commit -m "feat: list command with Chrome JSON and HTML support + manifest integration"
```

---

### Task 8: Fetcher Module

**Files:**
- Create: `src/bookmark2skill/fetcher.py`
- Create: `tests/test_fetcher.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_fetcher.py
import pytest
from bookmark2skill.fetcher import fetch_url, FetchError


def test_fetch_returns_markdown(httpx_mock):
    """fetch_url returns clean markdown from an HTML page."""
    httpx_mock.add_response(
        url="https://example.com/article",
        html="""
        <html><head><title>Test Article</title></head>
        <body>
            <nav>Navigation</nav>
            <article>
                <h1>Test Article</h1>
                <p>This is the main content of the article.</p>
                <p>Second paragraph with <strong>bold text</strong>.</p>
            </article>
            <footer>Footer stuff</footer>
        </body></html>
        """,
    )
    result = fetch_url("https://example.com/article")
    assert "main content" in result
    assert isinstance(result, str)


def test_fetch_error_on_404(httpx_mock):
    """fetch_url raises FetchError on HTTP errors."""
    httpx_mock.add_response(url="https://example.com/missing", status_code=404)
    with pytest.raises(FetchError, match="404"):
        fetch_url("https://example.com/missing")


def test_fetch_error_on_connection_failure(httpx_mock):
    """fetch_url raises FetchError on connection failures."""
    httpx_mock.add_exception(
        ConnectionError("Connection refused"),
        url="https://example.com/down",
    )
    with pytest.raises(FetchError):
        fetch_url("https://example.com/down")
```

Note: These tests need `pytest-httpx`. Add it to dev dependencies.

- [ ] **Step 2: Update pyproject.toml to add pytest-httpx**

In `pyproject.toml`, update:
```toml
dev = ["pytest>=8.0", "pytest-httpx>=0.30"]
```

Run: `pip install -e ".[dev]"`

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_fetcher.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'bookmark2skill.fetcher'`

- [ ] **Step 4: Implement fetcher module**

```python
# src/bookmark2skill/fetcher.py
from __future__ import annotations

import httpx
from lxml.html.clean import Cleaner  # type: ignore[import-untyped]

try:
    from readability import Document  # type: ignore[import-untyped]
except ImportError:
    Document = None


class FetchError(Exception):
    """Raised when fetching a URL fails."""
    pass


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; bookmark2skill/0.1)",
}


def _html_to_markdown(html: str) -> str:
    """Convert HTML to simple markdown. Minimal conversion."""
    import re

    # Use readability to extract article content
    if Document is not None:
        doc = Document(html)
        html = doc.summary()

    # Simple HTML → Markdown conversion
    text = html
    # Headers
    text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"# \1\n", text, flags=re.DOTALL)
    text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"## \1\n", text, flags=re.DOTALL)
    text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"### \1\n", text, flags=re.DOTALL)
    # Bold / italic
    text = re.sub(r"<(?:strong|b)>(.*?)</(?:strong|b)>", r"**\1**", text, flags=re.DOTALL)
    text = re.sub(r"<(?:em|i)>(.*?)</(?:em|i)>", r"*\1*", text, flags=re.DOTALL)
    # Links
    text = re.sub(r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.DOTALL)
    # Code blocks
    text = re.sub(r"<pre[^>]*><code[^>]*>(.*?)</code></pre>", r"```\n\1\n```\n", text, flags=re.DOTALL)
    text = re.sub(r"<code>(.*?)</code>", r"`\1`", text, flags=re.DOTALL)
    # Paragraphs and line breaks
    text = re.sub(r"<p[^>]*>", "\n\n", text)
    text = re.sub(r"</p>", "", text)
    text = re.sub(r"<br\s*/?>", "\n", text)
    # Lists
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", text, flags=re.DOTALL)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch_url(url: str, *, timeout: float = 30.0) -> str:
    """Fetch a URL and return its content as clean markdown.

    Uses httpx + readability-lxml. Raises FetchError on failure.
    """
    try:
        resp = httpx.get(url, headers=_HEADERS, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise FetchError(f"HTTP {e.response.status_code} for {url}") from e
    except (httpx.RequestError, ConnectionError) as e:
        raise FetchError(f"Failed to fetch {url}: {e}") from e

    return _html_to_markdown(resp.text)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_fetcher.py -v`

Expected: all 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/bookmark2skill/fetcher.py tests/test_fetcher.py pyproject.toml
git commit -m "feat: fetcher with httpx + readability, tiered HTML-to-markdown conversion"
```

---

### Task 9: `fetch` CLI Command

**Files:**
- Modify: `src/bookmark2skill/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
# Add to tests/test_cli.py

class TestFetchCommand:
    def test_fetch_outputs_markdown(self, runner, httpx_mock):
        httpx_mock.add_response(
            url="https://example.com/article",
            html="<html><body><article><h1>Title</h1><p>Content here.</p></article></body></html>",
        )
        result = runner.invoke(cli, ["fetch", "https://example.com/article"])
        assert result.exit_code == 0
        assert "Content here" in result.output

    def test_fetch_error_shows_message(self, runner, httpx_mock):
        httpx_mock.add_response(url="https://example.com/missing", status_code=404)
        result = runner.invoke(cli, ["fetch", "https://example.com/missing"])
        assert result.exit_code != 0
        assert "404" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py::TestFetchCommand -v`

Expected: FAIL — no `fetch` command

- [ ] **Step 3: Add fetch command to cli.py**

Add to `src/bookmark2skill/cli.py`:

```python
from bookmark2skill.fetcher import fetch_url, FetchError


@cli.command()
@click.argument("url")
@click.option("--timeout", default=30.0, help="Request timeout in seconds")
def fetch(url: str, timeout: float):
    """Fetch a URL and output clean markdown to stdout."""
    try:
        markdown = fetch_url(url, timeout=timeout)
    except FetchError as e:
        raise click.ClickException(str(e))
    click.echo(markdown)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py::TestFetchCommand -v`

Expected: all 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/bookmark2skill/cli.py tests/test_cli.py
git commit -m "feat: fetch command outputs clean markdown to stdout"
```

---

### Task 10: Obsidian Renderer + Template

**Files:**
- Create: `src/bookmark2skill/renderers/__init__.py`
- Create: `src/bookmark2skill/renderers/obsidian.py`
- Create: `src/bookmark2skill/templates/obsidian.md.jinja`
- Create: `tests/test_obsidian_renderer.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_obsidian_renderer.py
import pytest
from bookmark2skill.renderers.obsidian import render_obsidian


def test_render_full_data(sample_distilled_data):
    """Renders all sections from full structured data."""
    result = render_obsidian(sample_distilled_data)
    assert "Simplicity is the ultimate sophistication" in result
    assert "https://example.com/article" in result
    assert "Complex systems fail in complex ways" in result
    assert "The best code is no code at all." in result
    assert "Netflix" in result
    assert "Hystrix" in result


def test_render_minimal_data(sample_minimal_data):
    """Renders only title and link for minimal data."""
    result = render_obsidian(sample_minimal_data)
    assert "Minimal Article" in result
    assert "https://example.com/minimal" in result
    # Should NOT contain empty section headers
    assert "## 逻辑推导链" not in result
    assert "## 精彩表达" not in result


def test_render_has_yaml_frontmatter(sample_distilled_data):
    """Output starts with YAML frontmatter."""
    result = render_obsidian(sample_distilled_data)
    assert result.startswith("---\n")
    assert "\n---\n" in result[3:]


def test_render_skips_empty_sections(sample_minimal_data):
    """Empty optional fields produce no section headers."""
    result = render_obsidian(sample_minimal_data)
    lines = result.split("\n")
    section_headers = [l for l in lines if l.startswith("## ")]
    # Minimal data should have zero or very few section headers
    assert len(section_headers) == 0


def test_render_quotes_include_why(sample_distilled_data):
    """Brilliant quotes include the 'why' annotation."""
    result = render_obsidian(sample_distilled_data)
    assert "Concise expression of YAGNI principle" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_obsidian_renderer.py -v`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create the Jinja2 template**

```jinja2
{# src/bookmark2skill/templates/obsidian.md.jinja #}
---
url: {{ url }}
{%- if original_title %}
original_title: "{{ original_title }}"
{%- endif %}
{%- if author %}
author: {{ author | tojson }}
{%- endif %}
{%- if date_published %}
date_published: {{ date_published }}
{%- endif %}
date_processed: {{ date_processed }}
{%- if tags %}
tags: {{ tags | tojson }}
{%- endif %}
---

# {{ title }}

> **原文链接:** {{ url }}
{% set d = layers.distillation if layers and layers.distillation else {} %}
{% set m = layers.agent_metadata if layers and layers.agent_metadata else {} %}
{% if d.logic_chain %}

## 逻辑推导链
{% for step in d.logic_chain %}
- {{ step }}
{% endfor %}
{% endif %}
{% if d.brilliant_quotes %}

## 精彩表达
{% for q in d.brilliant_quotes %}
> "{{ q.text }}"
> — *{{ q.why }}*
{% endfor %}
{% endif %}
{% if d.narrative_craft %}

## 叙事手法
{% for n in d.narrative_craft %}
- {{ n }}
{% endfor %}
{% endif %}
{% if d.concrete_examples %}

## 具体案例与数据
{% for ex in d.concrete_examples %}
- {{ ex }}
{% endfor %}
{% endif %}
{% if d.counterpoints %}

## 反对声音与局限性
{% for cp in d.counterpoints %}
- {{ cp }}
{% endfor %}
{% endif %}
{% if d.overlooked_details %}

## 容易忽略的细节
{% for det in d.overlooked_details %}
- {{ det }}
{% endfor %}
{% endif %}
```

- [ ] **Step 4: Implement the renderer**

```python
# src/bookmark2skill/renderers/__init__.py
```

```python
# src/bookmark2skill/renderers/obsidian.py
from __future__ import annotations

import pathlib
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

    # Flatten agent_metadata tags into top-level for frontmatter
    metadata = (data.get("layers") or {}).get("agent_metadata") or {}
    context = {
        **data,
        "tags": metadata.get("tags"),
    }
    result = template.render(**context)
    # Clean up excessive blank lines
    import re
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip() + "\n"
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_obsidian_renderer.py -v`

Expected: all 5 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/bookmark2skill/renderers/ src/bookmark2skill/templates/obsidian.md.jinja tests/test_obsidian_renderer.py
git commit -m "feat: Obsidian renderer with Jinja2 template, skips empty sections"
```

---

### Task 11: Skill Renderer + Template + Taxonomy

**Files:**
- Create: `src/bookmark2skill/renderers/skill.py`
- Create: `src/bookmark2skill/templates/skill.md.jinja`
- Create: `defaults/taxonomy.toml`
- Create: `tests/test_skill_renderer.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_skill_renderer.py
import pytest
from bookmark2skill.renderers.skill import render_skill


def test_render_full_data(sample_distilled_data):
    """Renders skill with frontmatter and concise body."""
    result = render_skill(sample_distilled_data)
    assert result.startswith("---\n")
    assert "taste_signals:" in result
    assert "reuse_contexts:" in result
    assert "engineering/system-design" in result


def test_render_minimal_data(sample_minimal_data):
    """Renders skill with only required frontmatter."""
    result = render_skill(sample_minimal_data)
    assert "Minimal Article" in result
    assert result.startswith("---\n")


def test_render_includes_key_claims(sample_distilled_data):
    """Key claims appear in frontmatter."""
    result = render_skill(sample_distilled_data)
    assert "Simplicity in system design" in result


def test_render_includes_quality_score(sample_distilled_data):
    """Quality score appears in frontmatter."""
    result = render_skill(sample_distilled_data)
    assert "depth:" in result
    assert "practicality:" in result


def test_render_includes_when_to_reference(sample_distilled_data):
    """Body includes when-to-reference section from reuse_contexts."""
    result = render_skill(sample_distilled_data)
    assert "Making architecture decisions" in result


def test_render_skips_empty_body_sections(sample_minimal_data):
    """Minimal data produces no body sections."""
    result = render_skill(sample_minimal_data)
    assert "## Key Insights" not in result
    assert "## When To Reference" not in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_skill_renderer.py -v`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create the Jinja2 template**

```jinja2
{# src/bookmark2skill/templates/skill.md.jinja #}
---
name: "{{ title }}"
description: "{{ description }}"
url: {{ url }}
{%- if category %}
category: {{ category }}
{%- endif %}
{%- if content_type %}
content_type: {{ content_type }}
{%- endif %}
{%- if tags %}
tags: {{ tags | tojson }}
{%- endif %}
{%- if key_claims %}
key_claims:
{%- for claim in key_claims %}
  - "{{ claim }}"
{%- endfor %}
{%- endif %}
{%- if taste_signals %}
taste_signals:
{%- if taste_signals.aesthetic %}
  aesthetic: {{ taste_signals.aesthetic | tojson }}
{%- endif %}
{%- if taste_signals.intellectual %}
  intellectual: {{ taste_signals.intellectual | tojson }}
{%- endif %}
{%- if taste_signals.values %}
  values: {{ taste_signals.values | tojson }}
{%- endif %}
{%- endif %}
{%- if reuse_contexts %}
reuse_contexts:
{%- for ctx in reuse_contexts %}
  - situation: "{{ ctx.situation }}"
    how: "{{ ctx.how }}"
{%- endfor %}
{%- endif %}
{%- if quality_score %}
quality_score:
{%- if quality_score.depth is not none %}
  depth: {{ quality_score.depth }}
{%- endif %}
{%- if quality_score.originality is not none %}
  originality: {{ quality_score.originality }}
{%- endif %}
{%- if quality_score.practicality is not none %}
  practicality: {{ quality_score.practicality }}
{%- endif %}
{%- if quality_score.writing is not none %}
  writing: {{ quality_score.writing }}
{%- endif %}
{%- endif %}
---
{% set d = distillation %}
{% set m = agent_metadata %}
{% if d and d.logic_chain %}

## Key Insights
{% for step in d.logic_chain %}
- {{ step }}
{% endfor %}
{% endif %}
{% if d and d.brilliant_quotes %}

## Memorable Quotes
{% for q in d.brilliant_quotes %}
> "{{ q.text }}"
{% endfor %}
{% endif %}
{% if d and d.concrete_examples %}

## Concrete Examples
{% for ex in d.concrete_examples %}
- {{ ex }}
{% endfor %}
{% endif %}
{% if m and m.reuse_contexts %}

## When To Reference
{% for ctx in m.reuse_contexts %}
- **{{ ctx.situation }}** → {{ ctx.how }}
{% endfor %}
{% endif %}
```

- [ ] **Step 4: Implement the renderer**

```python
# src/bookmark2skill/renderers/skill.py
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

    # Build description from first key_claim or title
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
```

- [ ] **Step 5: Create default taxonomy.toml**

```toml
# defaults/taxonomy.toml
# Recommended taxonomy for skill categorization
# AI agents read this as guidance, not constraint — new categories can be created freely

[engineering]
description = "Software engineering practices, architecture, implementation"
subcategories = ["system-design", "frontend", "backend", "devops", "testing", "performance", "security"]

[thinking]
description = "Mental models, reasoning frameworks, decision-making"
subcategories = ["mental-models", "decision-making", "problem-solving", "first-principles", "cognitive-biases"]

[design]
description = "Visual design, UX, interaction patterns"
subcategories = ["ui-ux", "visual", "interaction", "typography", "accessibility"]

[writing]
description = "Writing craft, communication, rhetoric"
subcategories = ["technical", "narrative", "persuasion", "clarity", "editing"]

[product]
description = "Product thinking, strategy, user research"
subcategories = ["strategy", "user-research", "growth", "metrics", "prioritization"]

[culture]
description = "Team culture, leadership, organization"
subcategories = ["leadership", "collaboration", "hiring", "remote-work"]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_skill_renderer.py -v`

Expected: all 6 tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/bookmark2skill/renderers/skill.py src/bookmark2skill/templates/skill.md.jinja defaults/taxonomy.toml tests/test_skill_renderer.py
git commit -m "feat: skill renderer with Jinja2 template + default taxonomy"
```

---

### Task 12: `write-obsidian` CLI Command

**Files:**
- Modify: `src/bookmark2skill/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
# Add to tests/test_cli.py
import pathlib


class TestWriteObsidianCommand:
    def test_write_from_structured_json(self, runner, tmp_path, sample_distilled_data):
        vault = tmp_path / "vault"
        vault.mkdir()
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_distilled_data), encoding="utf-8")

        result = runner.invoke(cli, [
            "write-obsidian",
            "--url", "https://example.com/article",
            "--data", str(data_file),
            "--vault-path", str(vault),
        ])
        assert result.exit_code == 0
        # Check file was created
        md_files = list(vault.rglob("*.md"))
        assert len(md_files) == 1
        content = md_files[0].read_text()
        assert "Simplicity is the ultimate sophistication" in content

    def test_write_raw_mode(self, runner, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        raw_file = tmp_path / "raw.md"
        raw_file.write_text("# My Raw Note\n\nContent here.", encoding="utf-8")

        result = runner.invoke(cli, [
            "write-obsidian",
            "--url", "https://example.com/raw",
            "--raw", str(raw_file),
            "--vault-path", str(vault),
        ])
        assert result.exit_code == 0
        md_files = list(vault.rglob("*.md"))
        assert len(md_files) == 1
        assert "My Raw Note" in md_files[0].read_text()

    def test_write_creates_subdirectory_from_folder(self, runner, tmp_path, sample_distilled_data):
        vault = tmp_path / "vault"
        vault.mkdir()
        sample_distilled_data["folder"] = "tech/articles"
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_distilled_data), encoding="utf-8")

        result = runner.invoke(cli, [
            "write-obsidian",
            "--url", "https://example.com/article",
            "--data", str(data_file),
            "--vault-path", str(vault),
            "--folder", "tech/articles",
        ])
        assert result.exit_code == 0
        assert (vault / "bookmark2skill" / "tech" / "articles").is_dir()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py::TestWriteObsidianCommand -v`

Expected: FAIL — no `write-obsidian` command

- [ ] **Step 3: Add write-obsidian command + slugify helper**

Add to `src/bookmark2skill/cli.py`:

```python
import re as _re
import unicodedata

from bookmark2skill.schema import validate, ValidationError
from bookmark2skill.renderers.obsidian import render_obsidian


def _slugify(text: str, max_length: int = 80) -> str:
    """Convert text to a filesystem-safe slug."""
    # Normalize unicode
    text = unicodedata.normalize("NFKC", text)
    # Replace non-alphanumeric (keeping CJK chars) with hyphens
    text = _re.sub(r"[^\w\s\u4e00-\u9fff-]", "", text)
    text = _re.sub(r"[\s_]+", "-", text).strip("-").lower()
    return text[:max_length]


@cli.command("write-obsidian")
@click.option("--url", required=True, help="Source URL of the bookmark")
@click.option("--data", "data_file", type=click.Path(exists=True), help="Structured JSON file")
@click.option("--raw", "raw_file", type=click.Path(exists=True), help="Raw markdown file")
@click.option("--vault-path", required=True, help="Obsidian vault directory")
@click.option("--folder", default="", help="Subdirectory within bookmark2skill/")
def write_obsidian(url: str, data_file: str | None, raw_file: str | None, vault_path: str, folder: str):
    """Write an Obsidian note from structured JSON or raw markdown."""
    if not data_file and not raw_file:
        raise click.ClickException("Provide either --data or --raw")

    vault = pathlib.Path(vault_path)
    if raw_file:
        content = pathlib.Path(raw_file).read_text(encoding="utf-8")
        slug = _slugify(pathlib.Path(raw_file).stem)
    else:
        data = json.loads(pathlib.Path(data_file).read_text(encoding="utf-8"))
        try:
            validate(data)
        except ValidationError as e:
            raise click.ClickException(f"Invalid data: {e}")
        content = render_obsidian(data)
        slug = _slugify(data.get("title", "untitled"))

    # Build output path
    out_dir = vault / "bookmark2skill"
    if folder:
        out_dir = out_dir / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{slug}.md"
    out_file.write_text(content, encoding="utf-8")
    click.echo(json.dumps({"path": str(out_file)}, ensure_ascii=False))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py::TestWriteObsidianCommand -v`

Expected: all 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/bookmark2skill/cli.py tests/test_cli.py
git commit -m "feat: write-obsidian command with template and raw mode"
```

---

### Task 13: `write-skill` CLI Command

**Files:**
- Modify: `src/bookmark2skill/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
# Add to tests/test_cli.py

class TestWriteSkillCommand:
    def test_write_from_structured_json(self, runner, tmp_path, sample_distilled_data):
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_distilled_data), encoding="utf-8")

        result = runner.invoke(cli, [
            "write-skill",
            "--url", "https://example.com/article",
            "--data", str(data_file),
            "--category", "engineering/system-design",
            "--skill-dir", str(skill_dir),
        ])
        assert result.exit_code == 0
        # Check file was created in category directory
        md_files = list(skill_dir.rglob("*.md"))
        assert len(md_files) == 1
        assert "engineering/system-design" in str(md_files[0])

    def test_write_raw_mode(self, runner, tmp_path):
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        raw_file = tmp_path / "raw.md"
        raw_file.write_text("---\nname: test\n---\nContent.", encoding="utf-8")

        result = runner.invoke(cli, [
            "write-skill",
            "--url", "https://example.com/raw",
            "--raw", str(raw_file),
            "--category", "thinking/mental-models",
            "--skill-dir", str(skill_dir),
        ])
        assert result.exit_code == 0
        md_files = list(skill_dir.rglob("*.md"))
        assert len(md_files) == 1

    def test_category_creates_nested_dirs(self, runner, tmp_path, sample_distilled_data):
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_distilled_data), encoding="utf-8")

        result = runner.invoke(cli, [
            "write-skill",
            "--url", "https://example.com/article",
            "--data", str(data_file),
            "--category", "engineering/system-design",
            "--skill-dir", str(skill_dir),
        ])
        assert (skill_dir / "engineering" / "system-design").is_dir()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py::TestWriteSkillCommand -v`

Expected: FAIL — no `write-skill` command

- [ ] **Step 3: Add write-skill command**

Add to `src/bookmark2skill/cli.py`:

```python
from bookmark2skill.renderers.skill import render_skill


@cli.command("write-skill")
@click.option("--url", required=True, help="Source URL of the bookmark")
@click.option("--data", "data_file", type=click.Path(exists=True), help="Structured JSON file")
@click.option("--raw", "raw_file", type=click.Path(exists=True), help="Raw markdown file")
@click.option("--category", required=True, help="Category path (e.g., engineering/system-design)")
@click.option("--skill-dir", required=True, help="Base skill output directory")
def write_skill(url: str, data_file: str | None, raw_file: str | None, category: str, skill_dir: str):
    """Write a Claude Code skill file from structured JSON or raw markdown."""
    if not data_file and not raw_file:
        raise click.ClickException("Provide either --data or --raw")

    base = pathlib.Path(skill_dir)
    if raw_file:
        content = pathlib.Path(raw_file).read_text(encoding="utf-8")
        slug = _slugify(pathlib.Path(raw_file).stem)
    else:
        data = json.loads(pathlib.Path(data_file).read_text(encoding="utf-8"))
        try:
            validate(data)
        except ValidationError as e:
            raise click.ClickException(f"Invalid data: {e}")
        content = render_skill(data)
        slug = _slugify(data.get("title", "untitled"))

    out_dir = base / category
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{slug}.md"
    out_file.write_text(content, encoding="utf-8")
    click.echo(json.dumps({"path": str(out_file)}, ensure_ascii=False))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py::TestWriteSkillCommand -v`

Expected: all 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/bookmark2skill/cli.py tests/test_cli.py
git commit -m "feat: write-skill command with category-based directory routing"
```

---

### Task 14: `status`, `mark-done`, `mark-failed` CLI Commands

**Files:**
- Modify: `src/bookmark2skill/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
# Add to tests/test_cli.py

class TestStatusCommand:
    def test_status_empty(self, runner, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        result = runner.invoke(cli, ["status", "--manifest-path", manifest_path])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total"] == 0

    def test_status_with_bookmarks(self, runner, chrome_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        runner.invoke(cli, [
            "list", "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
        ])
        result = runner.invoke(cli, ["status", "--manifest-path", manifest_path])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["pending"] == 2
        assert data["total"] == 2


class TestMarkCommands:
    def test_mark_done(self, runner, chrome_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        runner.invoke(cli, [
            "list", "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
        ])
        result = runner.invoke(cli, [
            "mark-done", "https://example.com/article",
            "--manifest-path", manifest_path,
            "--obsidian-path", "/vault/article.md",
            "--skill-path", "/skills/article.md",
        ])
        assert result.exit_code == 0
        # Verify via status
        status = runner.invoke(cli, ["status", "--manifest-path", manifest_path])
        data = json.loads(status.output)
        assert data["done"] == 1

    def test_mark_failed(self, runner, chrome_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        runner.invoke(cli, [
            "list", "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
        ])
        result = runner.invoke(cli, [
            "mark-failed", "https://example.com/article",
            "--manifest-path", manifest_path,
            "--reason", "HTTP 404",
        ])
        assert result.exit_code == 0
        status = runner.invoke(cli, ["status", "--manifest-path", manifest_path])
        data = json.loads(status.output)
        assert data["failed"] == 1

    def test_mark_unknown_url_fails(self, runner, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        result = runner.invoke(cli, [
            "mark-done", "https://example.com/unknown",
            "--manifest-path", manifest_path,
        ])
        assert result.exit_code != 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py::TestStatusCommand tests/test_cli.py::TestMarkCommands -v`

Expected: FAIL — no `status`, `mark-done`, `mark-failed` commands

- [ ] **Step 3: Add the three commands**

Add to `src/bookmark2skill/cli.py`:

```python
@cli.command()
@click.option("--manifest-path", default=None, help="Override manifest file path")
def status(manifest_path: str | None):
    """Show bookmark processing status summary."""
    cfg = load_config(overrides={"manifest_path": manifest_path})
    manifest = Manifest(cfg["manifest_path"])
    click.echo(json.dumps(manifest.summary(), ensure_ascii=False, indent=2))


@cli.command("mark-done")
@click.argument("url")
@click.option("--manifest-path", default=None, help="Override manifest file path")
@click.option("--obsidian-path", default="", help="Path to the written Obsidian note")
@click.option("--skill-path", default="", help="Path to the written skill file")
@click.option("--note", default="", help="Optional note")
def mark_done(url: str, manifest_path: str | None, obsidian_path: str, skill_path: str, note: str):
    """Mark a bookmark as successfully processed."""
    cfg = load_config(overrides={"manifest_path": manifest_path})
    manifest = Manifest(cfg["manifest_path"])
    entry = manifest.get(url)
    if entry is None:
        raise click.ClickException(f"URL not found in manifest: {url}")
    manifest.mark_done(url, obsidian_path=obsidian_path, skill_path=skill_path)
    click.echo(json.dumps({"status": "done", "url": url}, ensure_ascii=False))


@cli.command("mark-failed")
@click.argument("url")
@click.option("--manifest-path", default=None, help="Override manifest file path")
@click.option("--reason", default="", help="Failure reason")
def mark_failed(url: str, manifest_path: str | None, reason: str):
    """Mark a bookmark as failed."""
    cfg = load_config(overrides={"manifest_path": manifest_path})
    manifest = Manifest(cfg["manifest_path"])
    entry = manifest.get(url)
    if entry is None:
        raise click.ClickException(f"URL not found in manifest: {url}")
    manifest.mark_failed(url, reason=reason)
    click.echo(json.dumps({"status": "failed", "url": url}, ensure_ascii=False))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py::TestStatusCommand tests/test_cli.py::TestMarkCommands -v`

Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/bookmark2skill/cli.py tests/test_cli.py
git commit -m "feat: status, mark-done, mark-failed commands"
```

---

### Task 15: Agent Guide Documentation

**Files:**
- Create: `docs/agent-guide.md`

- [ ] **Step 1: Write the agent guide**

```markdown
# bookmark2skill Agent Guide

> This document teaches AI agents how to use bookmark2skill effectively.
> Read this before orchestrating any bookmark processing workflow.

## What This Tool Does

bookmark2skill is a CLI utility that handles:
- Parsing Chrome bookmarks (JSON or HTML export)
- Fetching and cleaning web page content
- Writing structured output (Obsidian notes + Claude Code skills)
- Tracking which bookmarks have been processed (incremental)

**You (the AI agent) are responsible for:**
- Reading fetched content and distilling it (the "thinking" part)
- Producing structured JSON with your analysis
- Deciding which category each bookmark belongs to

## Workflow

```
1. bookmark2skill list --source chrome        # Get all bookmarks
2. bookmark2skill status                      # See what's pending
3. bookmark2skill fetch <url>                 # Get page content (markdown)
4. (You distill the content into structured JSON)
5. bookmark2skill write-obsidian --url <url> --data distilled.json --vault-path /path
6. bookmark2skill write-skill --url <url> --data distilled.json --category eng/sys --skill-dir /path
7. bookmark2skill mark-done <url> --obsidian-path <path> --skill-path <path>
```

If fetch fails:
```
bookmark2skill mark-failed <url> --reason "HTTP 404"
```

## Structured JSON Format

Your distilled output should be a JSON file with this structure.
Only `url`, `title`, and `date_processed` are required. All other fields are optional.

```json
{
  "url": "https://example.com/article",
  "title": "Core claim of the article (not the original title)",
  "date_processed": "2026-04-13T12:00:00Z",
  "original_title": "The Original Article Title",
  "author": ["Author Name"],
  "language": "en",
  "category": "engineering/system-design",
  "layers": {
    "distillation": {
      "logic_chain": ["Step A", "Therefore B", "Which means C"],
      "brilliant_quotes": [
        {"text": "The exact quote", "why": "Why this quote matters"}
      ],
      "narrative_craft": ["Observation about writing technique"],
      "concrete_examples": ["Specific example with enough context"],
      "counterpoints": ["Limitations or opposing views"],
      "overlooked_details": ["Easily missed but potentially useful details"]
    },
    "agent_metadata": {
      "tags": ["relevant", "tags"],
      "content_type": "technical-article",
      "key_claims": ["Assertive statement that can be agreed or disagreed with"],
      "taste_signals": {
        "aesthetic": ["What aesthetic preferences this bookmark reflects"],
        "intellectual": ["What thinking patterns it reflects"],
        "values": ["What values it reflects"]
      },
      "reuse_contexts": [
        {"situation": "When to reference this", "how": "How to use it"}
      ],
      "quality_score": {"depth": 4, "originality": 3, "practicality": 5, "writing": 4}
    }
  }
}
```

## Distillation Guidelines

**Do NOT summarize.** Deconstruct and preserve:

1. **Logic chains:** Trace the author's reasoning step by step
2. **Brilliant quotes:** Keep the original words + annotate WHY they're brilliant
3. **Narrative craft:** Note the writing techniques, not just the content
4. **Concrete examples:** Write out the actual examples, don't say "the author gave examples"
5. **Counterpoints:** Record what the author acknowledged as limitations
6. **Overlooked details:** Tool names, config values, version numbers, links mentioned in passing

## Taxonomy Reference

Read `~/.bookmark2skill/taxonomy.toml` for the recommended category structure.
You can use existing categories or create new ones as needed.

## Tips

- Process bookmarks one at a time — fetch, distill, write, mark
- Use `--only-new` with `list` to see only unprocessed bookmarks
- The `status` command gives you a quick overview of progress
- If a page is mostly images or JavaScript, note that in the distillation
- For non-article bookmarks (tools, repos), adapt the schema — skip narrative_craft, focus on practical details
```

- [ ] **Step 2: Commit**

```bash
git add docs/agent-guide.md
git commit -m "docs: agent guide teaching AI agents how to use bookmark2skill"
```

---

### Task 16: Full Integration Test + Final Polish

**Files:**
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write end-to-end integration test**

```python
# Add to tests/test_cli.py

class TestEndToEnd:
    def test_full_workflow(self, runner, tmp_path, chrome_bookmarks_file, sample_distilled_data, httpx_mock):
        """Test the complete workflow: list → fetch → write-obsidian → write-skill → mark-done → status."""
        vault = tmp_path / "vault"
        vault.mkdir()
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        manifest_path = str(tmp_path / "manifest.json")

        # Step 1: list
        result = runner.invoke(cli, [
            "list", "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
        ])
        assert result.exit_code == 0
        bookmarks = json.loads(result.output)
        assert len(bookmarks) == 2

        # Step 2: fetch
        httpx_mock.add_response(
            url="https://example.com/article",
            html="<html><body><article><h1>Test</h1><p>Great content.</p></article></body></html>",
        )
        result = runner.invoke(cli, ["fetch", "https://example.com/article"])
        assert result.exit_code == 0

        # Step 3: write-obsidian
        data_file = tmp_path / "distilled.json"
        data_file.write_text(json.dumps(sample_distilled_data), encoding="utf-8")
        result = runner.invoke(cli, [
            "write-obsidian",
            "--url", "https://example.com/article",
            "--data", str(data_file),
            "--vault-path", str(vault),
        ])
        assert result.exit_code == 0
        obsidian_path = json.loads(result.output)["path"]

        # Step 4: write-skill
        result = runner.invoke(cli, [
            "write-skill",
            "--url", "https://example.com/article",
            "--data", str(data_file),
            "--category", "engineering/system-design",
            "--skill-dir", str(skill_dir),
        ])
        assert result.exit_code == 0
        skill_path = json.loads(result.output)["path"]

        # Step 5: mark-done
        result = runner.invoke(cli, [
            "mark-done", "https://example.com/article",
            "--manifest-path", manifest_path,
            "--obsidian-path", obsidian_path,
            "--skill-path", skill_path,
        ])
        assert result.exit_code == 0

        # Step 6: status
        result = runner.invoke(cli, ["status", "--manifest-path", manifest_path])
        assert result.exit_code == 0
        status = json.loads(result.output)
        assert status["done"] == 1
        assert status["pending"] == 1
        assert status["total"] == 2
```

- [ ] **Step 2: Run full test suite**

Run: `pytest tests/ -v`

Expected: all tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_cli.py
git commit -m "test: end-to-end integration test covering full workflow"
```

- [ ] **Step 4: Run final check**

Run: `bookmark2skill --help`

Expected output shows all 7 commands: list, fetch, write-obsidian, write-skill, status, mark-done, mark-failed

- [ ] **Step 5: Push to remote**

```bash
git push origin main
```
