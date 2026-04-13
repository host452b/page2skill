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
