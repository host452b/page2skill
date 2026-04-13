# tests/test_fetcher.py
import pytest
from bookmark2skill.fetcher import fetch_url, FetchError


def test_fetch_direct_returns_markdown(httpx_mock):
    """Direct fetch returns clean markdown from an HTML page."""
    httpx_mock.add_response(
        url="https://example.com/article",
        html="""
        <html><head><title>Test Article</title></head>
        <body>
            <nav>Navigation</nav>
            <article>
                <h1>Test Article</h1>
                <p>This is the main content of the article. It has enough text to pass
                the minimum content length threshold so it won't trigger fallback to
                Jina Reader API. We need at least 200 characters of meaningful content
                here to make the auto mode happy.</p>
                <p>Second paragraph with <strong>bold text</strong>.</p>
            </article>
            <footer>Footer stuff</footer>
        </body></html>
        """,
    )
    result = fetch_url("https://example.com/article", renderer="direct")
    assert "main content" in result
    assert isinstance(result, str)


def test_fetch_error_on_404(httpx_mock):
    """fetch_url raises FetchError on HTTP errors."""
    httpx_mock.add_response(url="https://example.com/missing", status_code=404)
    with pytest.raises(FetchError, match="404"):
        fetch_url("https://example.com/missing", renderer="direct")


def test_fetch_error_on_connection_failure(httpx_mock):
    """fetch_url raises FetchError on connection failures."""
    httpx_mock.add_exception(
        ConnectionError("Connection refused"),
        url="https://example.com/down",
    )
    with pytest.raises(FetchError):
        fetch_url("https://example.com/down", renderer="direct")


def test_fetch_jina_returns_markdown(httpx_mock):
    """Jina Reader API returns markdown content."""
    httpx_mock.add_response(
        url="https://r.jina.ai/https://example.com/js-page",
        text="# JS Page Title\n\nThis is the full rendered content from Jina Reader API.",
    )
    result = fetch_url("https://example.com/js-page", renderer="jina")
    assert "JS Page Title" in result
    assert "full rendered content" in result


def test_auto_mode_falls_back_to_jina(httpx_mock):
    """Auto mode falls back to Jina when direct fetch returns too little content."""
    # Tier 1: direct returns tiny content (JS shell)
    httpx_mock.add_response(
        url="https://example.com/js-app",
        html="<html><body>Please wait...</body></html>",
    )
    # Tier 2: Jina returns full content
    httpx_mock.add_response(
        url="https://r.jina.ai/https://example.com/js-app",
        text="# Full Article\n\nThis is the complete article rendered by Jina. " * 5,
    )
    result = fetch_url("https://example.com/js-app", renderer="auto")
    assert "Full Article" in result
    assert len(result) > 200


def test_auto_mode_skips_jina_when_direct_is_sufficient(httpx_mock):
    """Auto mode does NOT call Jina when direct fetch has enough content."""
    long_content = "This is substantial article content. " * 20
    httpx_mock.add_response(
        url="https://example.com/static-page",
        html=f"<html><body><article><p>{long_content}</p></article></body></html>",
    )
    # No Jina mock — if it tries to call Jina, httpx_mock will raise
    result = fetch_url("https://example.com/static-page", renderer="auto")
    assert "substantial article content" in result


def test_renderer_direct_does_not_fall_back(httpx_mock):
    """renderer='direct' does not fall back to Jina even on short content."""
    httpx_mock.add_response(
        url="https://example.com/short",
        html="<html><body>Short.</body></html>",
    )
    result = fetch_url("https://example.com/short", renderer="direct")
    assert "Short" in result
