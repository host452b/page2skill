from __future__ import annotations

import re

import httpx

try:
    from readability import Document
except ImportError:
    Document = None


class FetchError(Exception):
    """Raised when fetching a URL fails."""
    pass


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; bookmark2skill/0.1)",
}


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


def fetch_url(url: str, *, timeout: float = 30.0) -> str:
    """Fetch a URL and return its content as clean markdown."""
    try:
        resp = httpx.get(url, headers=_HEADERS, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise FetchError(f"HTTP {e.response.status_code} for {url}") from e
    except (httpx.RequestError, ConnectionError) as e:
        raise FetchError(f"Failed to fetch {url}: {e}") from e

    return _html_to_markdown(resp.text)
