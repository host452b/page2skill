# bookmark2skill

## What This Is

A Python CLI tool that converts Chrome bookmarks into Obsidian notes (human-readable) and Claude Code skills (AI-agent-friendly). This tool does NOT call any LLM API — it handles parsing, scraping, file I/O, and state tracking. The AI agent calling this tool is responsible for the "thinking" (content distillation).

## Quick Start for AI Agents

Read `docs/agent-guide.md` for the full workflow and structured JSON schema.

```bash
bookmark2skill list --source chrome --only-new   # discover new bookmarks
bookmark2skill fetch <url>                        # scrape page → markdown
bookmark2skill write-obsidian --url <url> --data distilled.json --vault-path /path
bookmark2skill write-skill --url <url> --data distilled.json --category eng/sys --skill-dir /path
bookmark2skill mark-done <url> --obsidian-path <p> --skill-path <p>
```

Run `bookmark2skill <command> --help` for precise parameter descriptions.

## Development

```bash
pip install -e ".[dev]"          # install with dev dependencies
pytest tests/ -v                  # run all tests (62 tests)
bookmark2skill --version          # verify CLI works
```

## Project Structure

```
src/bookmark2skill/
├── cli.py              # Click CLI — all 7 subcommands
├── config.py           # Layered config: toml → env → CLI flags
├── schema.py           # JSON validation for structured input
├── manifest.py         # Incremental state tracking (manifest.json)
├── fetcher.py          # httpx + readability HTML-to-markdown
├── parsers/
│   ├── chrome_json.py  # Chrome's local Bookmarks JSON parser
│   └── html_export.py  # Netscape HTML bookmark export parser
├── renderers/
│   ├── obsidian.py     # Structured data → Obsidian note
│   └── skill.py        # Structured data → Claude Code skill
└── templates/
    ├── obsidian.md.jinja
    └── skill.md.jinja
```

## Key Design Decisions

- **Tool is the hands, AI agent is the brain** — no LLM API calls inside the tool
- **Not bound to any specific AI agent** — works with Claude Code, Codex, or any CLI
- **"Deconstruct, don't summarize"** — six-dimensional knowledge distillation
- **Flexible schema** — only url/title/date_processed required, everything else optional
- **Category-based skill triage** — skills stored in taxonomy subdirectories for precise retrieval
- **Hybrid mode** — template rendering by default, raw mode as escape hatch

See `CHANGELOG.md` for full rationale behind each decision.

## Configuration

- Config file: `~/.bookmark2skill/config.toml`
- Taxonomy: `~/.bookmark2skill/taxonomy.toml`
- Manifest: `~/.bookmark2skill/manifest.json`
- Defaults template: `defaults/config.toml`, `defaults/taxonomy.toml`
