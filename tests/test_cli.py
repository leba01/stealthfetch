"""Tests for CLI argument parsing and error handling."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from stealthfetch._errors import FetchError
from stealthfetch.cli import _build_parser, _parse_proxy, main


class TestArgParsing:
    def test_url_required(self) -> None:
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_url_parsed(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["https://example.com"])
        assert args.url == "https://example.com"

    def test_method_default(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["https://example.com"])
        assert args.method == "auto"

    def test_backend_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["https://example.com", "--backend", "camoufox"])
        assert args.backend == "camoufox"

    def test_no_links_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["https://example.com", "--no-links"])
        assert args.no_links is True

    def test_timeout_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["https://example.com", "-t", "60"])
        assert args.timeout == 60

    def test_proxy_flag(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(
            ["https://example.com", "--proxy", "http://proxy:8080"]
        )
        assert args.proxy == "http://proxy:8080"

    def test_header_flag_single(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(
            ["https://example.com", "--header", "Cookie: session=abc"]
        )
        assert args.headers == ["Cookie: session=abc"]

    def test_header_flag_multiple(self) -> None:
        parser = _build_parser()
        args = parser.parse_args([
            "https://example.com",
            "--header", "Cookie: session=abc",
            "--header", "Accept: text/html",
        ])
        assert args.headers == ["Cookie: session=abc", "Accept: text/html"]


class TestProxyParsing:
    def test_simple_proxy(self) -> None:
        result = _parse_proxy("http://proxy:8080")
        assert result["server"] == "http://proxy:8080"
        assert "username" not in result

    def test_proxy_with_credentials(self) -> None:
        result = _parse_proxy("http://user:pass@proxy:8080")
        assert result["server"] == "http://proxy:8080"
        assert result["username"] == "user"
        assert result["password"] == "pass"

    def test_https_proxy(self) -> None:
        result = _parse_proxy("https://proxy:3128")
        assert result["server"] == "https://proxy:3128"

    def test_malformed_proxy_no_hostname(self) -> None:
        with pytest.raises(ValueError, match="Invalid proxy URL"):
            _parse_proxy("not-a-url")

    def test_malformed_proxy_empty(self) -> None:
        with pytest.raises(ValueError, match="Invalid proxy URL"):
            _parse_proxy("")


class TestMainExecution:
    @patch(
        "stealthfetch._core.fetch_markdown",
        return_value="# Test\n\nHello world",
    )
    def test_successful_output(
        self, mock_fetch: object, capsys: pytest.CaptureFixture[str]
    ) -> None:
        main(["https://example.com"])
        captured = capsys.readouterr()
        assert "Hello world" in captured.out

    @patch(
        "stealthfetch._core.fetch_markdown",
        side_effect=FetchError("https://example.com", "Network error"),
    )
    def test_stealthfetch_error_exits_1(self, mock_fetch: object) -> None:
        with pytest.raises(SystemExit):
            main(["https://example.com"])

    @patch(
        "stealthfetch._core.fetch_markdown",
        side_effect=ValueError("Invalid URL"),
    )
    def test_value_error_exits_1(self, mock_fetch: object) -> None:
        with pytest.raises(SystemExit):
            main(["https://example.com"])
