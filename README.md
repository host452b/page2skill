# bookmark2skill (b2k)

> Chrome bookmarks → Obsidian notes + Claude Code skill files.

[中文文档](README.zh-CN.md)

**This is not an AI application.** It's a downstream utility tool for AI agents (Claude Code, Codex, etc.) — the AI agent is the brain, bookmark2skill is the hands. The tool itself does NOT call any LLM API.

```
[AI Agent CLI] ←→ [bookmark2skill CLI] ←→ [Chrome Bookmarks / Web / Local Files]
     ↓ (brain: distill, classify)    ↓ (hands: parse, fetch, write, track)
```

## Why

| Problem | How bookmark2skill solves it |
|---|---|
| **Links die** | Fetch + local archive. Your bookmarks survive even when sites don't. |
| **Summaries lose texture** | "Deconstruct, don't summarize" — preserves logic chains, brilliant quotes, narrative craft, concrete examples, counterpoints, and overlooked details. |
| **AI doesn't know your taste** | `taste_signals` model your aesthetic preferences, thinking patterns, and values across your entire knowledge base. |
| **Can't find what you saved** | `b2k search` does weighted keyword matching across all skill files. Category-based triage narrows the scope. |
| **Processing is tedious** | Incremental manifest — never re-process a bookmark. Resume anytime. |

## Quick Start

```bash
# 1. Install
./build.sh develop

# 2. Configure
mkdir -p ~/.bookmark2skill
cp defaults/config.toml ~/.bookmark2skill/config.toml
cp defaults/taxonomy.toml ~/.bookmark2skill/taxonomy.toml

# 3. List your bookmarks
b2k list --source chrome

# 4. Fetch a page
b2k fetch https://example.com/article

# 5. That's it — an AI agent takes over from here
#    (reads content, distills, writes notes + skills, marks done)
```

## Install

```bash
./build.sh develop    # editable install with dev deps
# or
pip install .         # production install
```

Optional: Playwright for JS-heavy pages:

```bash
pip install ".[browser]"
```

### Build Commands

```bash
./build.sh develop    # editable install with dev deps
./build.sh install    # production install
./build.sh test       # run 74 tests
./build.sh dist       # build sdist + wheel
./build.sh check      # compile check + tests
./build.sh clean      # remove build artifacts
```

## Configuration

```bash
mkdir -p ~/.bookmark2skill
cp defaults/config.toml ~/.bookmark2skill/config.toml
cp defaults/taxonomy.toml ~/.bookmark2skill/taxonomy.toml
```

Edit `~/.bookmark2skill/config.toml`:

```toml
[paths]
vault_path = "/path/to/your/obsidian/vault"
skill_dir = "/path/to/your/skills"
```

**Config priority:** `config.toml` < `BOOKMARK2SKILL_*` env vars < CLI flags

**Files:**

| File | Location | Purpose |
|---|---|---|
| `config.toml` | `~/.bookmark2skill/` | Paths and settings |
| `taxonomy.toml` | `~/.bookmark2skill/` | Recommended skill categories |
| `manifest.json` | `~/.bookmark2skill/` | Processing state (auto-created) |
| `manifest.json.bak` | `~/.bookmark2skill/` | Auto-backup before each write |

## Workflow

AI agent orchestrates the following pipeline. `b2k` is a shorthand alias for `bookmark2skill`:

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐
│  b2k list   │ →  │  b2k fetch  │ →  │  AI agent    │ →  │  b2k write-  │ →  │ b2k mark-  │
│  --source   │    │  <url>      │    │  distills    │    │  obsidian +  │    │ done <url> │
│  chrome     │    │             │    │  content     │    │  write-skill │    │            │
└─────────────┘    └─────────────┘    └──────────────┘    └──────────────┘    └────────────┘
   parse &            scrape &           produces            render to           update
   register           clean page         structured JSON     local files         manifest
```

### Step by step

```bash
# 1. Parse bookmarks, register new URLs in manifest
b2k list --source chrome

# 2. Check processing status
b2k status
# → {"pending": 15, "done": 42, "failed": 3, "total": 60}

# 3. Fetch a single page (auto-detects best method)
b2k fetch https://example.com/article > /tmp/raw.md

# 4. AI agent reads raw.md, produces structured JSON
#    (see docs/agent-guide.md for schema and distillation guidelines)

# 5. Write Obsidian note (human-readable)
b2k write-obsidian \
  --url https://example.com/article \
  --data /tmp/distilled.json
# → {"path": "./bookmark2skill/article-title.md"}

# 6. Write skill file (AI-agent-friendly, categorized)
b2k write-skill \
  --url https://example.com/article \
  --data /tmp/distilled.json \
  --category engineering/system-design
# → {"path": "./engineering/system-design/article-title.md"}

# 7. Mark as done
b2k mark-done https://example.com/article \
  --obsidian-path ./bookmark2skill/article-title.md \
  --skill-path ./engineering/system-design/article-title.md
```

On fetch failure:

```bash
b2k mark-failed https://example.com/dead --reason "HTTP 404"
```

### Filtering bookmarks

```bash
# Only process bookmarks in specific folders
b2k list --source chrome --include-folder "Learning"

# Skip certain folders
b2k list --source chrome --exclude-folder "Work" --exclude-folder "Personal"

# Combine: include first, then exclude from included set
b2k list --source chrome --include-folder "Tech" --exclude-folder "Archive"

# Only show new (unprocessed) bookmarks
b2k list --source chrome --only-new
```

### Searching skills

```bash
# Search across all generated skill files
b2k search "system design" --skill-dir ./skills

# Weighted matching: name(5) > description(4) > tags(3) = key_claims(3) > body(1)
b2k search "simplicity" --limit 5
```

## Commands

| Command | Purpose | Input | Output |
|---|---|---|---|
| `list` | Parse bookmark source, register new URLs | `--source chrome` or `.html` file | JSON array → stdout |
| `fetch` | Fetch and clean a single page | URL | Markdown → stdout |
| `write-obsidian` | Render structured JSON into Obsidian note | `--data` JSON or `--raw` MD | Writes file, path → stdout |
| `write-skill` | Render structured JSON into skill file | `--data` JSON + `--category` | Writes file, path → stdout |
| `status` | Query manifest processing status | — | JSON counts → stdout |
| `mark-done` | Set URL status to 'done' in manifest | URL + output paths | Updates manifest |
| `mark-failed` | Set URL status to 'failed' in manifest | URL + reason | Updates manifest |
| `search` | Search skill files by keyword | query string | JSON results → stdout |

Run `b2k <command> --help` for detailed parameter descriptions with examples.

## Bookmark Sources

| Source | Usage | Notes |
|---|---|---|
| Chrome (all profiles) | `--source chrome` | Scans ALL Chrome profiles, merges and deduplicates bookmarks |
| HTML export | `--source bookmarks.html` | Netscape format, works with any browser |
| Chrome JSON file | `--source /path/to/Bookmarks` | Direct path to Chrome's JSON file |

## Output Formats

### Obsidian Note (human-readable)

Writes to `{vault-path}/bookmark2skill/{folder}/{slug}.md`:

```yaml
---
url: "https://example.com/article"
original_title: "Original Article Title"
author: ["Author Name"]
date_processed: 2026-04-13T12:00:00Z
tags: ["system-design", "simplicity"]
---

# Distilled Title (core claim, not original title)

## 摘要
2-4 sentence summary...

## 逻辑推导链
- Step A → Step B → Conclusion

## 精彩表达
> "Original quote" — *why it's brilliant*

## 叙事手法  /  具体案例与数据  /  反对声音与局限性  /  容易忽略的细节
(empty sections auto-skipped)
```

### Claude Code Skill (AI-agent-friendly)

Writes to `{skill-dir}/{category}/{slug}.md`:

```yaml
---
name: "Distilled Title"
description: "One-line description for AI agent relevance matching"
url: "https://example.com/article"
category: "engineering/system-design"
tags: ["system-design", "simplicity"]
key_claims:
  - "Assertive statement that can be agreed or disagreed with"
taste_signals:
  aesthetic: ["minimalism", "clarity"]
  intellectual: ["first-principles", "empiricism"]
  values: ["anti-complexity", "pragmatism"]
reuse_contexts:
  - situation: "When making architecture decisions"
    how: "Use as argument for simpler approach"
quality_score:
  depth: 4
  originality: 3
  practicality: 5
  writing: 4
---

## Summary  /  Key Insights  /  Memorable Quotes  /  Concrete Examples  /  When To Reference
```

## Tiered Fetch

```
Tier 1: httpx + readability       Fast, static pages (~80% of articles)
  ↓ content < 200 chars
Tier 2: Jina Reader API           JS-rendered pages, zero local deps
  ↓ Jina fails
Tier 3: Playwright                Local headless Chrome (optional dep)
```

Override: `b2k fetch <url> --renderer direct|jina|playwright`

## Taxonomy

Default categories in `~/.bookmark2skill/taxonomy.toml`:

| Category | Subcategories |
|---|---|
| `engineering/` | system-design, frontend, backend, devops, testing, performance, security |
| `thinking/` | mental-models, decision-making, problem-solving, first-principles, cognitive-biases |
| `design/` | ui-ux, visual, interaction, typography, accessibility |
| `writing/` | technical, narrative, persuasion, clarity, editing |
| `product/` | strategy, user-research, growth, metrics, prioritization |
| `culture/` | leadership, collaboration, hiring, remote-work |

AI agents can follow existing categories or create new ones freely. The taxonomy is guidance, not constraint.

## Structured JSON Schema

The AI agent produces this JSON after distilling fetched content. Required fields: `url`, `title`, `summary`, `date_processed`. Everything else is optional.

```json
{
  "url": "https://example.com/article",
  "title": "Core claim (not original title)",
  "summary": "2-4 sentences: what, evidence, why it matters.",
  "date_processed": "2026-04-13T12:00:00Z",
  "category": "engineering/system-design",
  "layers": {
    "distillation": {
      "logic_chain": ["A → B", "B → C"],
      "brilliant_quotes": [{"text": "quote", "why": "why brilliant"}],
      "narrative_craft": ["technique observation"],
      "concrete_examples": ["specific example"],
      "counterpoints": ["limitation or opposing view"],
      "overlooked_details": ["tool name, config value, version number"]
    },
    "agent_metadata": {
      "tags": ["tag1", "tag2"],
      "key_claims": ["assertive statement"],
      "taste_signals": {
        "aesthetic": ["minimalism"],
        "intellectual": ["first-principles"],
        "values": ["pragmatism"]
      },
      "reuse_contexts": [{"situation": "when", "how": "how to use"}],
      "quality_score": {"depth": 4, "originality": 3, "practicality": 5, "writing": 4}
    }
  }
}
```

Full schema documentation: [`docs/agent-guide.md`](docs/agent-guide.md)

## Security

- **Path traversal protection** — `--folder` and `--category` reject `../` escape attempts
- **YAML injection protection** — all user data escaped via `tojson` filter
- **SSRF protection** — only `http://` and `https://` URLs accepted
- **Manifest auto-backup** — `.json.bak` written before every save
- **No secrets in repo** — `.gitignore` covers manifest, .env, IDE files

## For AI Agents

See [`docs/agent-guide.md`](docs/agent-guide.md) for:
- Full workflow orchestration guide
- Structured JSON Schema (all fields documented)
- Distillation guidelines: summary (required) + six-dimension deconstruction
- Skill consumption best practices: discovery, relevance matching, taste aggregation
- Batch processing strategy and error recovery

## Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| CLI framework | click | Subcommands, options, help text |
| HTTP client | httpx | Tiered web scraping |
| Content extraction | readability-lxml | HTML → article body |
| JS rendering | Jina Reader API | Remote browser rendering (Tier 2) |
| JS rendering | Playwright (optional) | Local headless Chrome (Tier 3) |
| Templates | Jinja2 | Obsidian + skill output rendering |
| Config | tomli | TOML config parsing |
| Language | Python 3.10+ | — |

## License

MIT
