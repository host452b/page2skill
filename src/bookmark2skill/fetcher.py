from __future__ import annotations

import re

import httpx

try:
    from readability import Document
except ImportError:
    Document = None

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


class FetchError(Exception):
    """Raised when fetching a URL fails."""
    pass


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; bookmark2skill/0.1)",
}

_JINA_PREFIX = "https://r.jina.ai/"

# Content shorter than this (chars) triggers Jina fallback
_MIN_CONTENT_LENGTH = 200


def _html_to_markdown(html: str) -> str:
    """Convert HTML to simple markdown."""
    if Document is not None:
        doc = Document(html)
        html = doc.summary()

    text = html
    text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"# \1\n", text, flags=re.DOTALL)
    text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"## \1\n", text, flags=re.DOTALL)
    text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"### \1\n", text, flags=re.DOTALL)
    text = re.sub(r"<(?:strong|b)>(.*?)</(?:strong|b)>", r"**\1**", text, flags=re.DOTALL)
    text = re.sub(r"<(?:em|i)>(.*?)</(?:em|i)>", r"*\1*", text, flags=re.DOTALL)
    text = re.sub(r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.DOTALL)
    text = re.sub(r"<pre[^>]*><code[^>]*>(.*?)</code></pre>", r"```\n\1\n```\n", text, flags=re.DOTALL)
    text = re.sub(r"<code>(.*?)</code>", r"`\1`", text, flags=re.DOTALL)
    text = re.sub(r"<p[^>]*>", "\n\n", text)
    text = re.sub(r"</p>", "", text)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _fetch_direct(url: str, *, timeout: float = 30.0) -> str:
    """Tier 1: Direct fetch with httpx + readability."""
    resp = httpx.get(url, headers=_HEADERS, timeout=timeout, follow_redirects=True)
    resp.raise_for_status()
    return _html_to_markdown(resp.text)


def _fetch_jina(url: str, *, timeout: float = 60.0) -> str:
    """Tier 2: Jina Reader API — remote browser rendering, returns markdown."""
    jina_url = f"{_JINA_PREFIX}{url}"
    resp = httpx.get(
        jina_url,
        headers={"Accept": "text/markdown", **_HEADERS},
        timeout=timeout,
        follow_redirects=True,
    )
    resp.raise_for_status()
    return resp.text.strip()


def _fetch_playwright(url: str, *, timeout: float = 30.0) -> str:
    """Tier 3: Local Playwright browser rendering."""
    if sync_playwright is None:
        raise FetchError(
            "Playwright not installed. Install with: pip install 'bookmark2skill[browser]'"
        )
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=int(timeout * 1000))
        html = page.content()
        browser.close()
    return _html_to_markdown(html)


def fetch_url(url: str, *, timeout: float = 30.0, renderer: str = "auto") -> str:
    """Fetch a URL and return its content as clean markdown.

    Renderer modes:
      'auto'       — Tier 1 (direct) → Tier 2 (jina) → Tier 3 (playwright)
      'direct'     — httpx + readability only
      'jina'       — Jina Reader API only
      'playwright' — Local Playwright browser only
    """
    if renderer == "direct":
        try:
            return _fetch_direct(url, timeout=timeout)
        except (httpx.HTTPStatusError, httpx.RequestError, ConnectionError) as e:
            raise FetchError(f"Direct fetch failed for {url}: {e}") from e

    if renderer == "jina":
        try:
            return _fetch_jina(url, timeout=timeout)
        except (httpx.HTTPStatusError, httpx.RequestError, ConnectionError) as e:
            raise FetchError(f"Jina fetch failed for {url}: {e}") from e

    if renderer == "playwright":
        return _fetch_playwright(url, timeout=timeout)

    # auto mode: tiered fallback
    # Tier 1: direct
    try:
        content = _fetch_direct(url, timeout=timeout)
        if len(content) >= _MIN_CONTENT_LENGTH:
            return content
        # Content too short — likely JS-rendered page
    except (httpx.HTTPStatusError, httpx.RequestError, ConnectionError):
        content = ""

    # Tier 2: Jina Reader API
    try:
        jina_content = _fetch_jina(url, timeout=60.0)
        if len(jina_content) >= _MIN_CONTENT_LENGTH:
            return jina_content
    except (httpx.HTTPStatusError, httpx.RequestError, ConnectionError):
        pass

    # Tier 3: Playwright (if installed)
    if sync_playwright is not None:
        try:
            return _fetch_playwright(url, timeout=timeout)
        except Exception:
            pass

    # Return whatever we got, or raise
    if content:
        return content
    raise FetchError(f"All fetch tiers failed for {url}")
