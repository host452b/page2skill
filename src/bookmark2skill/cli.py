# src/bookmark2skill/cli.py
import json
import pathlib
import re as _re
import unicodedata

import click

from bookmark2skill.config import load_config
from bookmark2skill.fetcher import FetchError, fetch_url
from bookmark2skill.manifest import Manifest
from bookmark2skill.parsers.chrome_json import parse_chrome_json
from bookmark2skill.parsers.html_export import parse_html_export
from bookmark2skill.renderers.obsidian import render_obsidian
from bookmark2skill.renderers.skill import render_skill
from bookmark2skill.schema import ValidationError, validate


@click.group()
@click.version_option(package_name="bookmark2skill")
def cli():
    """Chrome bookmarks → Obsidian notes + Claude Code skills.

    AI agent downstream tool. Does NOT call any LLM API.
    Agent orchestrates: list → fetch → (distill) → write → mark.
    See docs/agent-guide.md for full workflow.
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
@click.option("--source", required=True, help="'chrome' to auto-detect local Chrome Bookmarks JSON, or path to .html/.json file")
@click.option("--manifest-path", default=None, help="Override manifest.json path [default: ~/.bookmark2skill/manifest.json]")
@click.option("--chrome-profile", default=None, help="Override Chrome profile directory for --source=chrome")
@click.option("--only-new", is_flag=True, help="Output only URLs not yet in manifest (skip already-registered)")
@click.option("--exclude-folder", multiple=True, help="Exclude bookmarks whose folder path contains this string (repeatable)")
@click.option("--include-folder", multiple=True, help="Only include bookmarks whose folder path contains this string (repeatable)")
def list(source: str, manifest_path: str | None, chrome_profile: str | None, only_new: bool, exclude_folder: tuple[str, ...], include_folder: tuple[str, ...]):
    """Parse bookmark source into JSON array. Registers new URLs as 'pending' in manifest.

    Output: JSON array of {url, title, folder, date_added} to stdout.
    Side effect: new URLs are added to manifest with status 'pending'.
    Filtering: --exclude-folder and --include-folder apply substring match on folder path.
    Both are optional and repeatable. When both are set, exclude is applied after include.
    """
    cfg = load_config(overrides={
        "manifest_path": manifest_path,
        "chrome_profile": chrome_profile,
    })
    manifest = Manifest(cfg["manifest_path"])

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
def fetch(url: str, timeout: float):
    """Fetch a single URL via httpx+readability, output clean Markdown to stdout.

    Strips navigation, ads, footers. Keeps article body only.
    Exit code 1 on HTTP error or connection failure (error message to stderr).
    """
    try:
        markdown = fetch_url(url, timeout=timeout)
    except FetchError as e:
        raise click.ClickException(str(e))
    click.echo(markdown)


def _slugify(text: str, max_length: int = 80) -> str:
    """Convert text to a filesystem-safe slug."""
    text = unicodedata.normalize("NFKC", text)
    text = _re.sub(r"[^\w\s\u4e00-\u9fff-]", "", text)
    text = _re.sub(r"[\s_]+", "-", text).strip("-").lower()
    return text[:max_length]


@cli.command("write-obsidian")
@click.option("--url", required=True, help="Source URL of the bookmark (stored in frontmatter)")
@click.option("--data", "data_file", type=click.Path(exists=True), help="Path to structured JSON file (see agent-guide.md for schema)")
@click.option("--raw", "raw_file", type=click.Path(exists=True), help="Path to raw Markdown file (bypass template, write as-is)")
@click.option("--vault-path", required=True, help="Obsidian vault root directory")
@click.option("--folder", default="", help="Subdirectory under {vault-path}/bookmark2skill/ [default: root]")
def write_obsidian(url: str, data_file: str | None, raw_file: str | None, vault_path: str, folder: str):
    """Render structured JSON into Obsidian note. Writes to {vault-path}/bookmark2skill/{folder}/{slug}.md.

    Provide --data for template rendering or --raw for direct write (mutually exclusive).
    Output: JSON {"path": "<written file path>"} to stdout.
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

    out_dir = vault / "bookmark2skill"
    if folder:
        out_dir = out_dir / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{slug}.md"
    out_file.write_text(content, encoding="utf-8")
    click.echo(json.dumps({"path": str(out_file)}, ensure_ascii=False))


@cli.command("write-skill")
@click.option("--url", required=True, help="Source URL of the bookmark (stored in frontmatter)")
@click.option("--data", "data_file", type=click.Path(exists=True), help="Path to structured JSON file (see agent-guide.md for schema)")
@click.option("--raw", "raw_file", type=click.Path(exists=True), help="Path to raw Markdown file (bypass template, write as-is)")
@click.option("--category", required=True, help="Category path for triage, e.g. 'engineering/system-design'. See taxonomy.toml")
@click.option("--skill-dir", required=True, help="Base skill output directory root")
def write_skill(url: str, data_file: str | None, raw_file: str | None, category: str, skill_dir: str):
    """Render structured JSON into Claude Code skill. Writes to {skill-dir}/{category}/{slug}.md.

    Provide --data for template rendering or --raw for direct write (mutually exclusive).
    Category determines subdirectory. Consult ~/.bookmark2skill/taxonomy.toml for categories.
    Output: JSON {"path": "<written file path>"} to stdout.
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

    out_dir = base / category
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{slug}.md"
    out_file.write_text(content, encoding="utf-8")
    click.echo(json.dumps({"path": str(out_file)}, ensure_ascii=False))


@cli.command()
@click.option("--manifest-path", default=None, help="Override manifest.json path [default: ~/.bookmark2skill/manifest.json]")
def status(manifest_path: str | None):
    """Output manifest summary as JSON: {pending, done, failed, total} counts."""
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

    URL must already exist in manifest (registered via 'list' command).
    Exit code 1 if URL not found.
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

    URL must already exist in manifest (registered via 'list' command).
    Exit code 1 if URL not found.
    """
    cfg = load_config(overrides={"manifest_path": manifest_path})
    manifest = Manifest(cfg["manifest_path"])
    entry = manifest.get(url)
    if entry is None:
        raise click.ClickException(f"URL not found in manifest: {url}")
    manifest.mark_failed(url, reason=reason)
    click.echo(json.dumps({"status": "failed", "url": url}, ensure_ascii=False))
