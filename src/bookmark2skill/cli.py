# src/bookmark2skill/cli.py
import click


@click.group()
@click.version_option(package_name="bookmark2skill")
def cli():
    """Convert Chrome bookmarks into Obsidian notes and Claude Code skills."""
    pass
