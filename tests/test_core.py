"""Tests for the core pipeline with mocked fetch layer."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from stealthfetch._core import (
    FetchResult,
    _build_curl_proxies,
    afetch_markdown,
    afetch_result,
    fetch_markdown,
    fetch_result,
)
from stealthfetch._errors import FetchError

FIXTURES_DIR = Path(__file__).parent / "fixtures"
_ARTICLE_HTML = (FIXTURES_DIR / "article.html").read_text()
_BLOCKED_HTML = (FIXTURES_DIR / "cloudflare_block.html").read_text()


def _make_afetch_ok() -> AsyncMock:
    mock = AsyncMock(return_value=(_ARTICLE_HTML, 200, "text/html"))
    return mock


def _make_afetch_blocked() -> AsyncMock:
    mock = AsyncMock(return_value=(_BLOCKED_HTML, 403, "text/html"))
    return mock


def _make_afetch_fail() -> AsyncMock:
    mock = AsyncMock(side_effect=ConnectionError("Connection refused"))
    return mock


class TestFetchResultPipeline:
    @patch("stealthfetch._core._afetch_http", new_callable=_make_afetch_ok)
    def test_returns_fetch_result_instance(self, mock_fetch: AsyncMock) -> None:
        result = fetch_result("https://example.com/article", method="http")
        assert isinstance(result, FetchResult)

    @patch("stealthfetch._core._afetch_http", new_callable=_make_afetch_ok)
    def test_markdown_field_contains_content(self, mock_fetch: AsyncMock) -> None:
        result = fetch_result("https://example.com/article", method="http")
        assert "jellyfish" in result.markdown
        assert "Mariana Trench" in result.markdown
        assert "<html>" not in result.markdown

    @patch("stealthfetch._core._afetch_http", new_callable=_make_afetch_ok)
    def test_title_field_extracted(self, mock_fetch: AsyncMock) -> None:
        result = fetch_result("https://example.com/article", method="http")
        assert result.title is not None
        assert isinstance(result.title, str)

    @patch("stealthfetch._core._afetch_http", new_callable=_make_afetch_ok)
    def test_metadata_fields_are_str_or_none(self, mock_fetch: AsyncMock) -> None:
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
    @patch("stealthfetch._core._afetch_http", new_callable=_make_afetch_ok)
    def test_successful_fetch(self, mock_fetch: AsyncMock) -> None:
        result = fetch_markdown("https://example.com/article", method="http")
        assert "jellyfish" in result
        assert "Mariana Trench" in result
        assert "<html>" not in result


class TestAsyncPath:
    @pytest.mark.asyncio
    @patch("stealthfetch._core._afetch_http", new_callable=AsyncMock)
    async def test_afetch_markdown(self, mock_fetch: AsyncMock) -> None:
        mock_fetch.return_value = (_ARTICLE_HTML, 200, "text/html")
        result = await afetch_markdown("https://example.com/article", method="http")
        assert "jellyfish" in result
        assert isinstance(result, str)


class TestAutoEscalation:
    @patch("stealthfetch._core._has_any_browser", return_value=False)
    @patch("stealthfetch._core._afetch_http", new_callable=_make_afetch_blocked)
    def test_blocked_without_browser_returns_result(
        self, mock_fetch: AsyncMock, mock_browser: object
    ) -> None:
        """When blocked but no browser, still attempts extraction."""
        result = fetch_markdown("https://example.com", method="auto")
        assert isinstance(result, str)

    @patch("stealthfetch._core._has_any_browser", return_value=False)
    @patch("stealthfetch._core._afetch_http", new_callable=_make_afetch_fail)
    def test_http_failure_without_browser_raises(
        self, mock_fetch: AsyncMock, mock_browser: object
    ) -> None:
        with pytest.raises(FetchError, match="Connection refused"):
            fetch_markdown("https://example.com", method="auto")

    @patch("stealthfetch._core._has_any_browser", return_value=True)
    @patch("stealthfetch._browsers.afetch_browser", new_callable=AsyncMock)
    @patch("stealthfetch._core._afetch_http", new_callable=_make_afetch_blocked)
    def test_blocked_with_browser_escalates(
        self, mock_http: AsyncMock, mock_bfetch: AsyncMock, mock_has: object
    ) -> None:
        mock_bfetch.return_value = _ARTICLE_HTML
        result = fetch_markdown("https://example.com", method="auto")
        assert "jellyfish" in result

    @patch("stealthfetch._core._has_any_browser", return_value=True)
    @patch("stealthfetch._browsers.afetch_browser", new_callable=AsyncMock)
    @patch("stealthfetch._core._afetch_http", new_callable=_make_afetch_fail)
    def test_http_error_with_browser_escalates(
        self, mock_http: AsyncMock, mock_bfetch: AsyncMock, mock_has: object
    ) -> None:
        mock_bfetch.return_value = _ARTICLE_HTML
        result = fetch_markdown("https://example.com", method="auto")
        assert "jellyfish" in result

    @patch("stealthfetch._core._afetch_http", new_callable=_make_afetch_blocked)
    def test_403_in_http_mode_raises_fetch_error(self, mock_fetch: AsyncMock) -> None:
        """method='http' with a 403 should raise FetchError, not silently return."""
        with pytest.raises(FetchError, match="HTTP 403"):
            fetch_markdown("https://example.com", method="http")


class TestMethodForcing:
    @patch("stealthfetch._core._afetch_http", new_callable=_make_afetch_ok)
    def test_force_http(self, mock_fetch: AsyncMock) -> None:
        result = fetch_markdown("https://example.com", method="http")
        assert isinstance(result, str)

    @patch("stealthfetch._browsers.afetch_browser", new_callable=AsyncMock)
    def test_force_browser(self, mock_fetch: AsyncMock) -> None:
        mock_fetch.return_value = _ARTICLE_HTML
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

    @patch("stealthfetch._core._afetch_http", new_callable=_make_afetch_ok)
    def test_valid_proxy_accepted(self, mock_fetch: AsyncMock) -> None:
        result = fetch_markdown(
            "https://example.com",
            method="http",
            proxy={"server": "http://proxy:8080"},
        )
        assert isinstance(result, str)


class TestBuildCurlProxies:
    def test_no_proxy_returns_none(self) -> None:
        assert _build_curl_proxies(None) is None

    def test_server_only(self) -> None:
        result = _build_curl_proxies({"server": "http://proxy:8080"})
        assert result == {"https": "http://proxy:8080", "http": "http://proxy:8080"}

    def test_preserves_auth_credentials(self) -> None:
        result = _build_curl_proxies(
            {"server": "http://proxy:8080", "username": "user", "password": "pass"}
        )
        assert result is not None
        assert "user:pass@" in result["https"]
        assert "user:pass@" in result["http"]
        assert result["https"] == "http://user:pass@proxy:8080"

    def test_username_only_no_password(self) -> None:
        result = _build_curl_proxies({"server": "http://proxy:8080", "username": "user"})
        assert result is not None
        assert "user@proxy" in result["https"]
        assert ":pass" not in result["https"]


class TestAsyncSessionLifecycle:
    """Verify response data is extracted while the async session is alive."""

    @pytest.mark.asyncio
    async def test_response_data_read_inside_session(self) -> None:
        """Verify response attributes are accessed inside the async with block."""
        from stealthfetch._core import _afetch_http

        access_log: list[str] = []

        class MockResponse:
            url = "https://example.com"
            content = b"<html>OK</html>"

            @property
            def headers(self) -> dict[str, str]:
                access_log.append("headers")
                return {"content-type": "text/html"}

            @property
            def text(self) -> str:
                access_log.append("text")
                return "<html>OK</html>"

            @property
            def status_code(self) -> int:
                access_log.append("status_code")
                return 200

        mock_session = AsyncMock()
        mock_session.get.return_value = MockResponse()

        mock_async_session_cls = MagicMock()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_session
        mock_ctx.__aexit__.return_value = False
        mock_async_session_cls.return_value = mock_ctx

        with patch("curl_cffi.requests.AsyncSession", mock_async_session_cls):
            text, status_code, content_type = await _afetch_http("https://example.com")

        assert text == "<html>OK</html>"
        assert status_code == 200
        assert content_type == "text/html"
        assert "headers" in access_log
        assert "text" in access_log
        assert "status_code" in access_log


class TestBrowserEscalationPassesHeaders:
    @patch("stealthfetch._core._has_any_browser", return_value=True)
    @patch("stealthfetch._browsers.afetch_browser", new_callable=AsyncMock)
    @patch("stealthfetch._core._afetch_http", new_callable=_make_afetch_blocked)
    def test_escalation_passes_headers_to_browser(
        self, mock_http: AsyncMock, mock_bfetch: AsyncMock, mock_has: object
    ) -> None:
        mock_bfetch.return_value = _ARTICLE_HTML
        custom_headers = {"Authorization": "Bearer token123"}
        fetch_markdown("https://example.com", method="auto", headers=custom_headers)
        _, kwargs = mock_bfetch.call_args
        assert kwargs["headers"] == custom_headers

    @patch("stealthfetch._browsers.afetch_browser", new_callable=AsyncMock)
    def test_browser_mode_passes_headers(self, mock_bfetch: AsyncMock) -> None:
        mock_bfetch.return_value = _ARTICLE_HTML
        custom_headers = {"X-Custom": "value"}
        fetch_markdown("https://example.com", method="browser", headers=custom_headers)
        _, kwargs = mock_bfetch.call_args
        assert kwargs["headers"] == custom_headers


class TestRetry:
    @patch("stealthfetch._core.asyncio.sleep", new_callable=AsyncMock)
    @patch("stealthfetch._core._afetch_http", new_callable=AsyncMock)
    def test_retries_on_transient_5xx(
        self, mock_fetch: AsyncMock, mock_sleep: AsyncMock
    ) -> None:
        """5xx error retries and succeeds on second attempt."""
        mock_fetch.side_effect = [
            FetchError("https://example.com", reason="HTTP 500"),
            (_ARTICLE_HTML, 200, "text/html"),
        ]
        result = fetch_markdown("https://example.com", method="http", retries=2)
        assert "jellyfish" in result
        mock_sleep.assert_called_once_with(1)  # 2^0 = 1s

    @patch("stealthfetch._core.asyncio.sleep", new_callable=AsyncMock)
    @patch("stealthfetch._core._afetch_http", new_callable=AsyncMock)
    def test_retries_on_connection_error(
        self, mock_fetch: AsyncMock, mock_sleep: AsyncMock
    ) -> None:
        """Connection errors are retryable."""
        mock_fetch.side_effect = [
            ConnectionError("refused"),
            ConnectionError("refused"),
            (_ARTICLE_HTML, 200, "text/html"),
        ]
        result = fetch_markdown("https://example.com", method="http", retries=3)
        assert "jellyfish" in result
        assert mock_sleep.call_count == 2
        # Check exponential backoff: 1s, 2s
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)

    @patch("stealthfetch._core.asyncio.sleep", new_callable=AsyncMock)
    @patch("stealthfetch._core._afetch_http", new_callable=AsyncMock)
    def test_no_retry_on_4xx(
        self, mock_fetch: AsyncMock, mock_sleep: AsyncMock
    ) -> None:
        """4xx errors are not retried."""
        mock_fetch.side_effect = FetchError("https://example.com", reason="HTTP 403")
        with pytest.raises(FetchError, match="HTTP 403"):
            fetch_markdown("https://example.com", method="http", retries=3)
        mock_sleep.assert_not_called()

    @patch("stealthfetch._core._afetch_http", new_callable=_make_afetch_ok)
    def test_retries_zero_is_no_retry(self, mock_fetch: AsyncMock) -> None:
        """Default retries=0 works without any retry logic."""
        result = fetch_markdown("https://example.com", method="http", retries=0)
        assert "jellyfish" in result
        assert mock_fetch.call_count == 1

    @patch("stealthfetch._core.asyncio.sleep", new_callable=AsyncMock)
    @patch("stealthfetch._core._afetch_http", new_callable=AsyncMock)
    def test_exhausted_retries_raises(
        self, mock_fetch: AsyncMock, mock_sleep: AsyncMock
    ) -> None:
        """All retries exhausted raises the last error."""
        mock_fetch.side_effect = FetchError("https://example.com", reason="HTTP 502")
        with pytest.raises(FetchError, match="HTTP 502"):
            fetch_markdown("https://example.com", method="http", retries=2)
        assert mock_fetch.call_count == 3  # 1 initial + 2 retries

    @pytest.mark.asyncio
    @patch("stealthfetch._core.asyncio.sleep", new_callable=AsyncMock)
    @patch("stealthfetch._core._afetch_http", new_callable=AsyncMock)
    async def test_async_retry(
        self, mock_fetch: AsyncMock, mock_sleep: AsyncMock
    ) -> None:
        """Async path retries correctly too."""
        mock_fetch.side_effect = [
            FetchError("https://example.com", reason="HTTP 503"),
            (_ARTICLE_HTML, 200, "text/html"),
        ]
        result = await afetch_markdown("https://example.com", method="http", retries=1)
        assert "jellyfish" in result
