# src/bookmark2skill/cli.py
import json
import pathlib

import click

from bookmark2skill.config import load_config
from bookmark2skill.fetcher import FetchError, fetch_url
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
@click.option("--timeout", default=30.0, help="Request timeout in seconds")
def fetch(url: str, timeout: float):
    """Fetch a URL and output clean markdown to stdout."""
    try:
        markdown = fetch_url(url, timeout=timeout)
    except FetchError as e:
        raise click.ClickException(str(e))
    click.echo(markdown)
