"""Tests for the core pipeline with mocked fetch layer."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from stealthfetch._core import (
    FetchResult,
    afetch_markdown,
    afetch_result,
    fetch_markdown,
    fetch_result,
)
from stealthfetch._errors import FetchError

FIXTURES_DIR = Path(__file__).parent / "fixtures"
_ARTICLE_HTML = (FIXTURES_DIR / "article.html").read_text()


def _mock_http_ok(url: str, **kwargs: object) -> tuple[str, int, str]:
    """Return article fixture as a successful HTTP response."""
    return _ARTICLE_HTML, 200, "text/html"


def _mock_http_blocked(url: str, **kwargs: object) -> tuple[str, int, str]:
    """Return cloudflare block page."""
    html = (FIXTURES_DIR / "cloudflare_block.html").read_text()
    return html, 403, "text/html"


def _mock_http_fail(url: str, **kwargs: object) -> tuple[str, int, str]:
    raise ConnectionError("Connection refused")


async def _amock_http_ok(url: str, **kwargs: object) -> tuple[str, int, str]:
    return _ARTICLE_HTML, 200, "text/html"


class TestFetchResultPipeline:
    @patch("stealthfetch._core._fetch_http", side_effect=_mock_http_ok)
    def test_returns_fetch_result_instance(self, mock_fetch: object) -> None:
        result = fetch_result("https://example.com/article", method="http")
        assert isinstance(result, FetchResult)

    @patch("stealthfetch._core._fetch_http", side_effect=_mock_http_ok)
    def test_markdown_field_contains_content(self, mock_fetch: object) -> None:
        result = fetch_result("https://example.com/article", method="http")
        assert "jellyfish" in result.markdown
        assert "Mariana Trench" in result.markdown
        assert "<html>" not in result.markdown

    @patch("stealthfetch._core._fetch_http", side_effect=_mock_http_ok)
    def test_title_field_extracted(self, mock_fetch: object) -> None:
        result = fetch_result("https://example.com/article", method="http")
        assert result.title is not None
        assert isinstance(result.title, str)

    @patch("stealthfetch._core._fetch_http", side_effect=_mock_http_ok)
    def test_metadata_fields_are_str_or_none(self, mock_fetch: object) -> None:
        result = fetch_result("https://example.com/article", method="http")
        for field in ("title", "author", "date", "description", "url", "hostname", "sitename"):
            value = getattr(result, field)
            assert value is None or isinstance(value, str), f"{field} has unexpected type"

    @pytest.mark.asyncio
    @patch("stealthfetch._core._afetch_http", new_callable=AsyncMock)
    async def test_afetch_result_returns_fetch_result(self, mock_fetch: AsyncMock) -> None:
        mock_fetch.return_value = (_ARTICLE_HTML, 200, "text/html")
        result = await afetch_result("https://example.com/article", method="http")
        assert isinstance(result, FetchResult)
        assert "jellyfish" in result.markdown

    @pytest.mark.asyncio
    @patch("stealthfetch._core._afetch_http", new_callable=AsyncMock)
    async def test_afetch_result_metadata_fields(self, mock_fetch: AsyncMock) -> None:
        mock_fetch.return_value = (_ARTICLE_HTML, 200, "text/html")
        result = await afetch_result("https://example.com/article", method="http")
        assert result.title is not None
        assert isinstance(result.title, str)


class TestFetchMarkdownPipeline:
    @patch("stealthfetch._core._fetch_http", side_effect=_mock_http_ok)
    def test_successful_fetch(self, mock_fetch: object) -> None:
        result = fetch_markdown("https://example.com/article", method="http")
        assert "jellyfish" in result
        assert "Mariana Trench" in result
        assert "<html>" not in result


class TestAsyncPath:
    @pytest.mark.asyncio
    @patch("stealthfetch._core._afetch_http", new_callable=AsyncMock)
    async def test_afetch_markdown(self, mock_fetch: AsyncMock) -> None:
        mock_fetch.return_value = (_ARTICLE_HTML, 200, "text/html")
        result = await afetch_markdown(
            "https://example.com/article", method="http"
        )
        assert "jellyfish" in result
        assert isinstance(result, str)


class TestAutoEscalation:
    @patch("stealthfetch._core._has_any_browser", return_value=False)
    @patch("stealthfetch._core._fetch_http", side_effect=_mock_http_blocked)
    def test_blocked_without_browser_returns_result(
        self, mock_fetch: object, mock_browser: object
    ) -> None:
        """When blocked but no browser, still attempts extraction."""
        result = fetch_markdown("https://example.com", method="auto")
        assert isinstance(result, str)

    @patch("stealthfetch._core._has_any_browser", return_value=False)
    @patch("stealthfetch._core._fetch_http", side_effect=_mock_http_fail)
    def test_http_failure_without_browser_raises(
        self, mock_fetch: object, mock_browser: object
    ) -> None:
        with pytest.raises(FetchError, match="Connection refused"):
            fetch_markdown("https://example.com", method="auto")

    @patch("stealthfetch._core._has_any_browser", return_value=True)
    @patch(
        "stealthfetch._browsers.fetch_browser",
        return_value=_ARTICLE_HTML,
    )
    @patch("stealthfetch._core._fetch_http", side_effect=_mock_http_blocked)
    def test_blocked_with_browser_escalates(
        self, mock_http: object, mock_bfetch: object, mock_has: object
    ) -> None:
        result = fetch_markdown("https://example.com", method="auto")
        assert "jellyfish" in result

    @patch("stealthfetch._core._has_any_browser", return_value=True)
    @patch(
        "stealthfetch._browsers.fetch_browser",
        return_value=_ARTICLE_HTML,
    )
    @patch("stealthfetch._core._fetch_http", side_effect=_mock_http_fail)
    def test_http_error_with_browser_escalates(
        self, mock_http: object, mock_bfetch: object, mock_has: object
    ) -> None:
        result = fetch_markdown("https://example.com", method="auto")
        assert "jellyfish" in result

    @patch("stealthfetch._core._fetch_http", side_effect=_mock_http_blocked)
    def test_403_in_http_mode_raises_fetch_error(self, mock_fetch: object) -> None:
        """method='http' with a 403 should raise FetchError, not silently return."""
        with pytest.raises(FetchError, match="HTTP 403"):
            fetch_markdown("https://example.com", method="http")


class TestMethodForcing:
    @patch("stealthfetch._core._fetch_http", side_effect=_mock_http_ok)
    def test_force_http(self, mock_fetch: object) -> None:
        result = fetch_markdown("https://example.com", method="http")
        assert isinstance(result, str)

    @patch(
        "stealthfetch._browsers.fetch_browser",
        return_value=_ARTICLE_HTML,
    )
    def test_force_browser(self, mock_fetch: object) -> None:
        result = fetch_markdown("https://example.com", method="browser")
        assert "jellyfish" in result


class TestParameterValidation:
    @pytest.mark.parametrize(
        ("kwargs", "match"),
        [
            ({"method": "curl"}, "Invalid method"),
            ({"browser_backend": "selenium"}, "Invalid browser_backend"),
        ],
        ids=["bad-method", "bad-backend"],
    )
    def test_invalid_option_raises(self, kwargs: dict, match: str) -> None:
        with pytest.raises(ValueError, match=match):
            fetch_markdown("https://example.com", **kwargs)

    @pytest.mark.parametrize(
        ("url", "match"),
        [
            ("file:///etc/passwd", "not allowed"),
            ("http://127.0.0.1/secret", "private"),
            ("http://169.254.169.254/latest/meta-data/", "private"),
            ("", "empty"),
        ],
        ids=["file-scheme", "loopback", "aws-metadata", "empty-url"],
    )
    def test_bad_url_rejected(self, url: str, match: str) -> None:
        with pytest.raises(ValueError, match=match):
            fetch_markdown(url)

    def test_proxy_without_server_rejected(self) -> None:
        with pytest.raises(ValueError, match="server"):
            fetch_markdown(
                "https://example.com",
                proxy={"username": "u", "password": "p"},
            )

    @patch("stealthfetch._core._fetch_http", side_effect=_mock_http_ok)
    def test_valid_proxy_accepted(self, mock_fetch: object) -> None:
        result = fetch_markdown(
            "https://example.com",
            method="http",
            proxy={"server": "http://proxy:8080"},
        )
        assert isinstance(result, str)
