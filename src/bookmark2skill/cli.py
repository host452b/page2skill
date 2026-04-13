# src/bookmark2skill/cli.py
import json
import pathlib
import re as _re
import unicodedata

import click

from bookmark2skill.config import load_config
from bookmark2skill.fetcher import FetchError, fetch_url
from bookmark2skill.manifest import Manifest
from bookmark2skill.parsers.chrome_json import find_all_chrome_bookmarks, parse_chrome_json
from bookmark2skill.parsers.html_export import parse_html_export
from bookmark2skill.renderers.obsidian import render_obsidian
from bookmark2skill.renderers.skill import render_skill
from bookmark2skill.schema import ValidationError, validate


@click.group()
@click.version_option(package_name="bookmark2skill")
def cli():
    """Chrome bookmarks → Obsidian notes + Claude Code skills.

    AI agent downstream tool. Does NOT call any LLM API.
    The AI agent is the brain (distillation), this tool is the hands (parse, fetch, write, track).

    \b
    Workflow:
      1. b2k list --source chrome          Parse bookmarks, register in manifest
      2. b2k status                         Check pending/done/failed counts
      3. b2k fetch <url>                    Scrape page → clean Markdown to stdout
      4. (AI agent distills content into structured JSON)
      5. b2k write-obsidian --url <url> --data distilled.json
      6. b2k write-skill --url <url> --data distilled.json --category x/y
      7. b2k mark-done <url>                Record completion in manifest
    \b
    On failure:
      b2k mark-failed <url> --reason "HTTP 404"
    \b
    Config: ~/.bookmark2skill/config.toml
    Guide: docs/agent-guide.md
    Alias: b2k = bookmark2skill
    """
    pass


def _detect_source_type(source: str) -> str:
    """Detect whether source is a Chrome JSON file or HTML export."""
    if source.lower() == "chrome":
        return "chrome"
    path = pathlib.Path(source)
    if path.suffix.lower() in (".html", ".htm"):
        return "html"
    try:
        with open(path, "rb") as f:
            first = f.read(10).strip()
        if first.startswith(b"{"):
            return "chrome_json"
    except OSError:
        pass
    return "html"


@cli.command()
@click.option("--source", required=True, help="'chrome' to scan ALL Chrome profiles, or path to .html/.json file")
@click.option("--manifest-path", default=None, help="Override manifest.json path [default: ~/.bookmark2skill/manifest.json]")
@click.option("--chrome-dir", default=None, help="Override Chrome base directory (containing all profiles)")
@click.option("--only-new", is_flag=True, help="Output only URLs not yet in manifest (skip already-registered)")
@click.option("--exclude-folder", multiple=True, help="Exclude bookmarks whose folder path contains this string (repeatable)")
@click.option("--include-folder", multiple=True, help="Only include bookmarks whose folder path contains this string (repeatable)")
def list(source: str, manifest_path: str | None, chrome_dir: str | None, only_new: bool, exclude_folder: tuple[str, ...], include_folder: tuple[str, ...]):
    """Parse bookmark source into JSON array. Registers new URLs as 'pending' in manifest.

    \b
    Output: JSON array of {url, title, folder, date_added} to stdout.
    Side effect: new URLs added to manifest with status 'pending'.
    Idempotent: URLs already in manifest are skipped (not overwritten).
    \b
    Source types:
      --source chrome         Scan ALL Chrome profiles, merge and deduplicate bookmarks
      --source bookmarks.html Parse Netscape HTML bookmark export (any browser)
      --source Bookmarks      Directly specify a single Chrome JSON file path
    \b
    Folder filtering (substring match, repeatable):
      --include-folder "Tech"              Only process bookmarks in folders containing "Tech"
      --exclude-folder "Work" --exclude-folder "Personal"   Skip specific folders
      When both set: include first, then exclude from the included set.
    \b
    Examples:
      b2k list --source chrome
      b2k list --source chrome --only-new --exclude-folder "Work"
      b2k list --source ~/Downloads/bookmarks.html --include-folder "Learning"
    """
    cfg = load_config(overrides={
        "manifest_path": manifest_path,
        "chrome_dir": chrome_dir,
    })
    manifest = Manifest(cfg["manifest_path"])

    source_type = _detect_source_type(source)
    if source_type == "chrome":
        bookmarks = find_all_chrome_bookmarks(cfg["chrome_dir"])
        if not bookmarks:
            raise click.ClickException(f"No Chrome bookmarks found in {cfg['chrome_dir']}")
    elif source_type == "chrome_json":
        bookmarks = parse_chrome_json(source)
    else:
        bookmarks = parse_html_export(source)

    # Apply folder filters
    if include_folder:
        bookmarks = [b for b in bookmarks if any(inc in b["folder"] for inc in include_folder)]
    if exclude_folder:
        bookmarks = [b for b in bookmarks if not any(exc in b["folder"] for exc in exclude_folder)]

    new_bookmarks = []
    for b in bookmarks:
        was_new = manifest.add(url=b["url"], title=b["title"], folder=b["folder"])
        if only_new and not was_new:
            continue
        if not only_new or was_new:
            new_bookmarks.append(b)

    output = new_bookmarks if only_new else bookmarks
    click.echo(json.dumps(output, ensure_ascii=False, indent=2))


@cli.command()
@click.argument("url")
@click.option("--timeout", default=30.0, help="HTTP request timeout in seconds [default: 30.0]")
@click.option("--renderer", default="auto", type=click.Choice(["auto", "direct", "jina", "playwright"]),
              help="Fetch strategy: 'auto' tries direct→jina→playwright; or force one [default: auto]")
def fetch(url: str, timeout: float, renderer: str):
    """Fetch a single URL and output clean Markdown to stdout.

    \b
    Tiered fetch strategy (auto mode):
      Tier 1: httpx + readability-lxml    Fast, works for static pages (~80% of articles)
      Tier 2: Jina Reader API r.jina.ai   Remote browser rendering for JS-heavy pages
      Tier 3: Playwright (if installed)    Local headless Chrome, last resort
    \b
    Auto mode triggers fallback when content is < 200 chars (likely JS shell).
    Force a specific renderer with --renderer direct|jina|playwright.
    \b
    Exit codes:
      0  Success — Markdown written to stdout
      1  All tiers failed — error message to stderr
    \b
    Examples:
      b2k fetch https://example.com/article
      b2k fetch https://example.com/spa --renderer jina
      b2k fetch https://example.com/article > /tmp/raw.md
    """
    try:
        markdown = fetch_url(url, timeout=timeout, renderer=renderer)
    except FetchError as e:
        raise click.ClickException(str(e))
    click.echo(markdown)


def _slugify(text: str, max_length: int = 80) -> str:
    """Convert text to a filesystem-safe slug."""
    text = unicodedata.normalize("NFKC", text)
    text = _re.sub(r"[^\w\s\u4e00-\u9fff-]", "", text)
    text = _re.sub(r"[\s_]+", "-", text).strip("-").lower()
    result = text[:max_length]
    return result if result else "untitled"


def _safe_subpath(base: pathlib.Path, subpath: str) -> pathlib.Path:
    """Resolve subpath under base, reject path traversal attempts."""
    resolved = (base / subpath).resolve()
    if not resolved.is_relative_to(base.resolve()):
        raise click.ClickException(f"Path escapes base directory: {subpath}")
    return resolved


@cli.command("write-obsidian")
@click.option("--url", required=True, help="Source URL of the bookmark (stored in frontmatter)")
@click.option("--data", "data_file", type=click.Path(exists=True), help="Path to structured JSON file (see agent-guide.md for schema)")
@click.option("--raw", "raw_file", type=click.Path(exists=True), help="Path to raw Markdown file (bypass template, write as-is)")
@click.option("--vault-path", default=".", help="Obsidian vault root directory [default: current directory]")
@click.option("--folder", default="", help="Subdirectory under {vault-path}/bookmark2skill/ [default: root]")
def write_obsidian(url: str, data_file: str | None, raw_file: str | None, vault_path: str, folder: str):
    """Render structured JSON into Obsidian note. Writes to {vault-path}/bookmark2skill/{folder}/{slug}.md.

    \b
    Two modes (mutually exclusive):
      --data file.json   Template mode: validates JSON schema, renders via Jinja2 template
                         Produces: YAML frontmatter + 摘要 + six-dimension deconstruction
      --raw file.md      Raw mode: writes file content as-is, no template processing
    \b
    Schema required fields: url, title, summary, date_processed
    All other fields optional. See docs/agent-guide.md for full schema.
    Output: JSON {"path": "<written file path>"} to stdout.
    \b
    Examples:
      b2k write-obsidian --url https://example.com/article --data distilled.json
      b2k write-obsidian --url https://example.com/article --data d.json --folder tech/articles
      b2k write-obsidian --url https://example.com/article --raw custom.md --vault-path ~/vault
    """
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

    base_dir = vault / "bookmark2skill"
    out_dir = _safe_subpath(base_dir, folder) if folder else base_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{slug}.md"
    out_file.write_text(content, encoding="utf-8")
    click.echo(json.dumps({"path": str(out_file)}, ensure_ascii=False))


@cli.command("write-skill")
@click.option("--url", required=True, help="Source URL of the bookmark (stored in frontmatter)")
@click.option("--data", "data_file", type=click.Path(exists=True), help="Path to structured JSON file (see agent-guide.md for schema)")
@click.option("--raw", "raw_file", type=click.Path(exists=True), help="Path to raw Markdown file (bypass template, write as-is)")
@click.option("--category", required=True, help="Category path for triage, e.g. 'engineering/system-design'. See taxonomy.toml")
@click.option("--skill-dir", default=".", help="Base skill output directory root [default: current directory]")
def write_skill(url: str, data_file: str | None, raw_file: str | None, category: str, skill_dir: str):
    """Render structured JSON into Claude Code skill. Writes to {skill-dir}/{category}/{slug}.md.

    \b
    Two modes (mutually exclusive):
      --data file.json   Template mode: renders frontmatter-heavy skill file with
                         taste_signals, reuse_contexts, quality_score, key_claims
      --raw file.md      Raw mode: writes file content as-is
    \b
    Category determines subdirectory (e.g. 'engineering/system-design' → engineering/system-design/).
    Read ~/.bookmark2skill/taxonomy.toml for recommended categories, or create new ones freely.
    Output: JSON {"path": "<written file path>"} to stdout.
    \b
    Examples:
      b2k write-skill --url https://example.com/article --data d.json --category engineering/system-design
      b2k write-skill --url https://example.com/article --data d.json --category thinking/mental-models
      b2k write-skill --url https://example.com/article --raw custom.md --category design/visual
    """
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

    out_dir = _safe_subpath(base, category)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{slug}.md"
    out_file.write_text(content, encoding="utf-8")
    click.echo(json.dumps({"path": str(out_file)}, ensure_ascii=False))


@cli.command()
@click.option("--manifest-path", default=None, help="Override manifest.json path [default: ~/.bookmark2skill/manifest.json]")
def status(manifest_path: str | None):
    """Output manifest summary as JSON: {pending, done, failed, total} counts.

    \b
    Use this to check processing progress before deciding what to do next.
    Example output: {"pending": 15, "done": 42, "failed": 3, "total": 60}
    """
    cfg = load_config(overrides={"manifest_path": manifest_path})
    manifest = Manifest(cfg["manifest_path"])
    click.echo(json.dumps(manifest.summary(), ensure_ascii=False, indent=2))


@cli.command("mark-done")
@click.argument("url")
@click.option("--manifest-path", default=None, help="Override manifest.json path [default: ~/.bookmark2skill/manifest.json]")
@click.option("--obsidian-path", default="", help="File path of the written Obsidian note (recorded in manifest)")
@click.option("--skill-path", default="", help="File path of the written skill file (recorded in manifest)")
@click.option("--note", default="", help="Optional free-text note stored in manifest entry")
def mark_done(url: str, manifest_path: str | None, obsidian_path: str, skill_path: str, note: str):
    """Set URL status to 'done' in manifest. Record output file paths.

    \b
    Call this after successfully writing both Obsidian note and skill file.
    Stores the output paths in manifest for future reference.
    URL must already exist in manifest (registered via 'list' command).
    Exit code 1 if URL not found.
    \b
    Example:
      b2k mark-done https://example.com/article \\
        --obsidian-path ./bookmark2skill/article.md \\
        --skill-path ./engineering/system-design/article.md
    """
    cfg = load_config(overrides={"manifest_path": manifest_path})
    manifest = Manifest(cfg["manifest_path"])
    entry = manifest.get(url)
    if entry is None:
        raise click.ClickException(f"URL not found in manifest: {url}")
    manifest.mark_done(url, obsidian_path=obsidian_path, skill_path=skill_path)
    click.echo(json.dumps({"status": "done", "url": url}, ensure_ascii=False))


@cli.command("mark-failed")
@click.argument("url")
@click.option("--manifest-path", default=None, help="Override manifest.json path [default: ~/.bookmark2skill/manifest.json]")
@click.option("--reason", default="", help="Failure reason string stored in manifest (e.g. 'HTTP 404', 'timeout')")
def mark_failed(url: str, manifest_path: str | None, reason: str):
    """Set URL status to 'failed' in manifest. Record failure reason.

    \b
    Call this when fetch fails or content is unusable. Records the reason for later review.
    URL must already exist in manifest (registered via 'list' command).
    Exit code 1 if URL not found.
    \b
    Example:
      b2k mark-failed https://example.com/dead --reason "HTTP 404"
      b2k mark-failed https://example.com/spa --reason "JS-only, no content extracted"
    """
    cfg = load_config(overrides={"manifest_path": manifest_path})
    manifest = Manifest(cfg["manifest_path"])
    entry = manifest.get(url)
    if entry is None:
        raise click.ClickException(f"URL not found in manifest: {url}")
    manifest.mark_failed(url, reason=reason)
    click.echo(json.dumps({"status": "failed", "url": url}, ensure_ascii=False))


@cli.command()
@click.argument("query")
@click.option("--skill-dir", default=".", help="Base skill output directory to search [default: current directory]")
@click.option("--limit", "max_results", default=10, help="Max results to return [default: 10]")
def search(query: str, skill_dir: str, max_results: int):
    """Search skill files by keyword. Matches against frontmatter fields and body content.

    \b
    Scans all .md files under --skill-dir recursively.
    Weighted field matching (higher weight = more relevant):
      name: 5  |  description: 4  |  tags: 3  |  key_claims: 3  |  situation: 2  |  category: 2  |  body: 1
    \b
    Output: JSON array of {path, name, category, score, matched_fields} to stdout, ranked by score.
    Returns empty array [] when no matches found.
    \b
    Examples:
      b2k search "system design"
      b2k search "simplicity" --skill-dir ~/skills --limit 5
      b2k search "AI" --limit 20
    """
    import os

    query_lower = query.lower()
    results = []
    base = pathlib.Path(skill_dir)

    if not base.is_dir():
        raise click.ClickException(f"Skill directory not found: {skill_dir}")

    for root, _dirs, files in os.walk(base):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            fpath = pathlib.Path(root) / fname
            try:
                content = fpath.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            # Parse frontmatter and body
            score = 0
            matched = []

            # Split frontmatter from body
            parts = content.split("---", 2)
            frontmatter = parts[1] if len(parts) >= 3 else ""
            body = parts[2] if len(parts) >= 3 else content

            # Weighted field matching on frontmatter lines
            field_weights = {
                "name:": 5,
                "description:": 4,
                "tags:": 3,
                "key_claims:": 3,
                "situation:": 2,
                "category:": 2,
            }
            for line in frontmatter.split("\n"):
                line_lower = line.lower()
                if query_lower in line_lower:
                    for field, weight in field_weights.items():
                        if field in line_lower:
                            score += weight
                            matched.append(field.rstrip(":"))
                            break
                    else:
                        score += 1
                        if "frontmatter" not in matched:
                            matched.append("frontmatter")

            # Body match (summary, insights, examples, etc.)
            if query_lower in body.lower():
                score += 1
                matched.append("body")

            if score > 0:
                # Extract name from frontmatter
                name = ""
                for line in frontmatter.split("\n"):
                    if line.strip().startswith("name:"):
                        name = line.split(":", 1)[1].strip().strip('"')
                        break

                category = str(fpath.parent.relative_to(base))
                results.append({
                    "path": str(fpath),
                    "name": name,
                    "category": category,
                    "score": score,
                    "matched_fields": matched,
                })

    results.sort(key=lambda r: r["score"], reverse=True)
    results = results[:max_results]
    click.echo(json.dumps(results, ensure_ascii=False, indent=2))


_SKIP_URL_PATTERNS = [
    # Enterprise collaboration (any company)
    "atlassian.net", "confluence.", "jira.", "gitlab.", "github.com/enterprise",
    "service-now.com", "sharepoint.com", "workday.com", "slack.com/archives",
    # E-commerce / purchase pages
    "taobao.com", "jd.com", "tmall.com", "amazon.com/dp", "amazon.com/gp",
    # Cloud console / billing
    "/console", "/billing", "/buy/",
]

_SKIP_TITLE_KEYWORDS = [
    # Auth / portal (not knowledge content)
    "登录", "login", "sign in", "sign up",
    "dashboard", "控制台", "console", "admin",
    # Account / personal
    "my request", "我的订单", "account settings",
]

_SKIP_FOLDER_KEYWORDS = [
    # Portals / online tools
    "在线工具", "online tool", "门户", "portal",
    # HR / corporate
    "入职", "离职", "onboarding", "offboarding", "welfare",
    # Shopping / finance
    "购物", "shopping", "stock",
]



@cli.command()
@click.option("--source", required=True, help="'chrome' to scan all profiles, or path to bookmark file")
@click.option("--vault-path", default=".", help="Obsidian vault root [default: current directory]")
@click.option("--skill-dir", default=".", help="Skill output root [default: current directory]")
@click.option("--include-folder", multiple=True, help="Only include bookmarks in these folders (repeatable)")
@click.option("--exclude-folder", multiple=True, help="Exclude bookmarks in these folders (repeatable)")
@click.option("--chrome-dir", default=None, help="Override Chrome base directory")
def report(source: str, vault_path: str, skill_dir: str, include_folder: tuple[str, ...],
           exclude_folder: tuple[str, ...], chrome_dir: str | None):
    """Show processing status: done / skipped / pending for each bookmark.

    \b
    Cross-references bookmarks against generated files in vault and skill dirs.
    Skips company-internal URLs (Confluence, Jira, GitLab, etc.) automatically.
    Output: human-readable table to stdout (not JSON, not saved to any file).
    \b
    Examples:
      b2k report --source chrome --include-folder "Learning"
      b2k report --source chrome --vault-path ./b2k-vault --skill-dir ./b2k-skills
    """
    import os as _os

    cfg = load_config(overrides={"chrome_dir": chrome_dir})

    # Parse bookmarks
    source_type = _detect_source_type(source)
    if source_type == "chrome":
        from bookmark2skill.parsers.chrome_json import find_all_chrome_bookmarks
        bookmarks = find_all_chrome_bookmarks(cfg["chrome_dir"])
    elif source_type == "chrome_json":
        bookmarks = parse_chrome_json(source)
    else:
        bookmarks = parse_html_export(source)

    if include_folder:
        bookmarks = [b for b in bookmarks if any(inc in b["folder"] for inc in include_folder)]
    if exclude_folder:
        bookmarks = [b for b in bookmarks if not any(exc in b["folder"] for exc in exclude_folder)]

    # Index generated files by URL
    vault_base = pathlib.Path(vault_path) / "bookmark2skill"
    skill_base = pathlib.Path(skill_dir)
    vault_urls: dict[str, str] = {}
    skill_urls: dict[str, tuple[str, str]] = {}

    if vault_base.is_dir():
        for f in vault_base.rglob("*.md"):
            try:
                for line in f.read_text(encoding="utf-8").split("\n")[:10]:
                    if line.startswith("url:"):
                        url = line.split("url:", 1)[1].strip().strip('"')
                        vault_urls[url] = f.name
                        break
            except (OSError, UnicodeDecodeError):
                continue

    if skill_base.is_dir():
        for f in skill_base.rglob("*.md"):
            try:
                for line in f.read_text(encoding="utf-8").split("\n")[:10]:
                    if line.startswith("url:"):
                        url = line.split("url:", 1)[1].strip().strip('"')
                        cat = str(f.parent.relative_to(skill_base))
                        skill_urls[url] = (cat, f.name)
                        break
            except (OSError, UnicodeDecodeError):
                continue

    # Classify
    done, skipped, pending = [], [], []
    for b in bookmarks:
        url, title = b["url"], b["title"][:60]
        folder = b.get("folder", "")
        title_lower = b.get("title", "").lower()
        folder_lower = folder.lower()
        is_skip_url = any(p in url.lower() for p in _SKIP_URL_PATTERNS)
        is_skip_folder = any(kw.lower() in folder_lower for kw in _SKIP_FOLDER_KEYWORDS)
        is_skip_title = any(kw.lower() in title_lower for kw in _SKIP_TITLE_KEYWORDS)

        if url in vault_urls and url in skill_urls:
            cat = skill_urls[url][0]
            done.append({"title": title, "category": cat})
        elif is_skip_url:
            skipped.append({"title": title, "reason": "URL blacklist"})
        elif is_skip_folder:
            skipped.append({"title": title, "reason": "folder blacklist"})
        elif is_skip_title:
            skipped.append({"title": title, "reason": "title blacklist"})
        else:
            pending.append({"title": title, "url": url})

    # Print report
    click.echo(f"\n{'═' * 70}")
    click.echo(f"b2k Processing Report")
    click.echo(f"{'═' * 70}")

    if done:
        click.echo(f"\n✅ 蒸馏成功 ({len(done)})")
        for i, d in enumerate(done):
            click.echo(f"  {i+1}. [{d['category']}] {d['title']}")

    if skipped:
        click.echo(f"\n⏭️  跳过 ({len(skipped)})")
        for i, s in enumerate(skipped):
            click.echo(f"  {i+1}. ({s['reason']}) {s['title']}")

    if pending:
        click.echo(f"\n⏳ 待处理 ({len(pending)})")
        for i, p in enumerate(pending):
            click.echo(f"  {i+1}. {p['title']}")

    click.echo(f"\n{'─' * 70}")
    click.echo(f"成功: {len(done)} | 跳过: {len(skipped)} | 待处理: {len(pending)} | 总计: {len(bookmarks)}")
