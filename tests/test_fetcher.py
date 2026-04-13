# tests/test_fetcher.py
import pytest
from bookmark2skill.fetcher import fetch_url, FetchError


def test_fetch_returns_markdown(httpx_mock):
    """fetch_url returns clean markdown from an HTML page."""
    httpx_mock.add_response(
        url="https://example.com/article",
        html="""
        <html><head><title>Test Article</title></head>
        <body>
            <nav>Navigation</nav>
            <article>
                <h1>Test Article</h1>
                <p>This is the main content of the article.</p>
                <p>Second paragraph with <strong>bold text</strong>.</p>
            </article>
            <footer>Footer stuff</footer>
        </body></html>
        """,
    )
    result = fetch_url("https://example.com/article")
    assert "main content" in result
    assert isinstance(result, str)


def test_fetch_error_on_404(httpx_mock):
    """fetch_url raises FetchError on HTTP errors."""
    httpx_mock.add_response(url="https://example.com/missing", status_code=404)
    with pytest.raises(FetchError, match="404"):
        fetch_url("https://example.com/missing")


def test_fetch_error_on_connection_failure(httpx_mock):
    """fetch_url raises FetchError on connection failures."""
    httpx_mock.add_exception(
        ConnectionError("Connection refused"),
        url="https://example.com/down",
    )
    with pytest.raises(FetchError):
        fetch_url("https://example.com/down")
