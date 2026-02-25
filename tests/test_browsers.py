"""Tests for browser backend dispatch and shared utilities."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from stealthfetch._browsers import _resolve_backend
from stealthfetch._browsers._constants import build_proxy
from stealthfetch._errors import BrowserNotAvailable


class TestResolveBackend:
    @patch("stealthfetch._compat.has_camoufox", return_value=True)
    def test_auto_prefers_camoufox(self, mock_has: object) -> None:
        assert _resolve_backend("auto") == "camoufox"

    @patch("stealthfetch._compat.has_camoufox", return_value=False)
    @patch("stealthfetch._compat.has_patchright", return_value=True)
    def test_auto_falls_back_to_patchright(
        self, mock_pr: object, mock_cf: object
    ) -> None:
        assert _resolve_backend("auto") == "patchright"

    @patch("stealthfetch._compat.has_camoufox", return_value=False)
    @patch("stealthfetch._compat.has_patchright", return_value=False)
    def test_auto_raises_when_none_available(
        self, mock_pr: object, mock_cf: object
    ) -> None:
        with pytest.raises(BrowserNotAvailable):
            _resolve_backend("auto")

    @patch("stealthfetch._compat.has_camoufox", return_value=True)
    def test_explicit_camoufox(self, mock_has: object) -> None:
        assert _resolve_backend("camoufox") == "camoufox"

    @patch("stealthfetch._compat.has_patchright", return_value=True)
    def test_explicit_patchright(self, mock_has: object) -> None:
        assert _resolve_backend("patchright") == "patchright"

    @patch("stealthfetch._compat.has_camoufox", return_value=False)
    def test_explicit_missing_raises(self, mock_has: object) -> None:
        with pytest.raises(BrowserNotAvailable):
            _resolve_backend("camoufox")


class TestBuildProxy:
    def test_none_returns_none(self) -> None:
        assert build_proxy(None) is None

    def test_empty_dict_returns_none(self) -> None:
        assert build_proxy({}) is None

    def test_server_only(self) -> None:
        result = build_proxy({"server": "http://proxy:8080"})
        assert result == {"server": "http://proxy:8080"}

    def test_with_credentials(self) -> None:
        result = build_proxy({
            "server": "http://proxy:8080",
            "username": "user",
            "password": "pass",
        })
        assert result == {
            "server": "http://proxy:8080",
            "username": "user",
            "password": "pass",
        }


class TestFetchBrowserDispatch:
    @patch("stealthfetch._compat.has_camoufox", return_value=True)
    @patch("stealthfetch._browsers._camoufox.fetch", return_value="<html>ok</html>")
    def test_fetch_browser_camoufox(self, mock_fetch: object, mock_has: object) -> None:
        from stealthfetch._browsers import fetch_browser

        result = fetch_browser("https://example.com", backend="camoufox")
        assert result == "<html>ok</html>"

    @patch("stealthfetch._compat.has_patchright", return_value=True)
    @patch("stealthfetch._browsers._patchright.fetch", return_value="<html>ok</html>")
    def test_fetch_browser_patchright(
        self, mock_fetch: object, mock_has: object
    ) -> None:
        from stealthfetch._browsers import fetch_browser

        result = fetch_browser("https://example.com", backend="patchright")
        assert result == "<html>ok</html>"
