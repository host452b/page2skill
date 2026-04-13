# bookmark2skill

Chrome bookmarks → Obsidian notes + Claude Code skill files.

[中文文档](README.zh-CN.md)

**This is not an AI application.** It's a downstream utility tool for AI agents (Claude Code, Codex, etc.) — the AI agent is the brain, bookmark2skill is the hands. The tool itself does NOT call any LLM API.

## Why

1. **Prevent link rot** — bookmarks go dead anytime, local archive is the only reliable backup
2. **Deconstruct, don't summarize** — extract logic chains, brilliant quotes, narrative craft, counterpoints, overlooked details — preserve the original texture
3. **Let AI agents understand your taste** — `taste_signals` model your aesthetic preferences, thinking patterns, and values
4. **AI summary** — every piece must include a 2-4 sentence summary as a quick-access entry point
5. **Incremental processing** — manifest tracks which bookmarks are processed, pending, or failed

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

Priority: `config.toml` < `BOOKMARK2SKILL_*` env vars < CLI flags

## Workflow

AI agent orchestrates the following (humans can run manually too). `b2k` is a shorthand alias for `bookmark2skill`:

```bash
# 1. Parse bookmarks, register new URLs in manifest
b2k list --source chrome

# 2. Check processing status
b2k status

# 3. Fetch a single page
b2k fetch https://example.com/article > /tmp/raw.md

# 4. AI agent reads raw.md, produces structured JSON (see docs/agent-guide.md)

# 5. Write Obsidian note
b2k write-obsidian \
  --url https://example.com/article \
  --data /tmp/distilled.json

# 6. Write skill file (categorized by taxonomy)
b2k write-skill \
  --url https://example.com/article \
  --data /tmp/distilled.json \
  --category engineering/system-design

# 7. Mark as done
b2k mark-done https://example.com/article \
  --obsidian-path ./bookmark2skill/article.md \
  --skill-path ./engineering/system-design/article.md
```

On fetch failure:

```bash
b2k mark-failed https://example.com/dead --reason "HTTP 404"
```

## Commands

| Command | Purpose | Output |
|---|---|---|
| `list` | Parse bookmark source, register new URLs | JSON array → stdout |
| `fetch` | Fetch and clean a single page (auto/direct/jina/playwright) | Markdown → stdout |
| `write-obsidian` | Render structured JSON into Obsidian note | Writes file, path → stdout |
| `write-skill` | Render structured JSON into skill file | Writes file, path → stdout |
| `status` | Query manifest processing status | JSON counts → stdout |
| `mark-done` | Set URL status to 'done' in manifest | Updates manifest |
| `mark-failed` | Set URL status to 'failed' in manifest | Updates manifest |
| `search` | Search skill files by keyword | JSON results → stdout |

Run `b2k <command> --help` for detailed parameter descriptions.

## Bookmark Sources

- **Chrome local JSON** — `--source chrome`, auto-detects `~/Library/Application Support/Google/Chrome/Default/Bookmarks`
- **HTML export** — `--source bookmarks.html`, supports Netscape format from any browser
- **Folder filters** — `--include-folder "Tech" --exclude-folder "Work"` for selective processing

## Output Formats

### Obsidian Note (human-readable)

Writes to `{vault-path}/bookmark2skill/{folder}/{slug}.md`:
- YAML frontmatter (url, author, tags, dates)
- Summary (2-4 sentences)
- Six-dimension deconstruction: logic chains, brilliant quotes, narrative craft, concrete examples, counterpoints, overlooked details
- Empty sections auto-skipped

### Claude Code Skill (AI-agent-friendly)

Writes to `{skill-dir}/{category}/{slug}.md`:
- Heavy frontmatter: taste_signals, reuse_contexts, quality_score, key_claims
- Light body: key insights, quotes, examples, when-to-reference
- Categorized by taxonomy for precise retrieval

## Tiered Fetch

```
Tier 1: httpx + readability (fast, static pages)
  ↓ content too short
Tier 2: Jina Reader API r.jina.ai (JS-rendered pages, zero local deps)
  ↓ Jina fails
Tier 3: Playwright (local browser, optional dependency)
```

Override with `--renderer direct|jina|playwright`.

## Taxonomy

Default categories in `~/.bookmark2skill/taxonomy.toml`:

- `engineering/` — system-design, frontend, backend, devops
- `thinking/` — mental-models, decision-making, problem-solving
- `design/` — ui-ux, visual, interaction
- `writing/` — technical, narrative, persuasion
- `product/` — strategy, user-research, growth

AI agents can follow existing categories or create new ones freely.

## For AI Agents

See [`docs/agent-guide.md`](docs/agent-guide.md) for:
- Full workflow orchestration guide
- Structured JSON Schema (all fields documented)
- Distillation guidelines (summary + six-dimension deconstruction)
- Skill consumption best practices

## Tech Stack

- Python 3.10+
- click (CLI), httpx (HTTP), readability-lxml (content extraction), jinja2 (templates), tomli (TOML config)
- Playwright (optional, JS-heavy pages)
- Jina Reader API (remote browser rendering, zero local deps)
