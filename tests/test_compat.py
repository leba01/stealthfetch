"""Tests for _compat module — feature detection and validation."""

from __future__ import annotations

from stealthfetch._compat import get_default_backend
from stealthfetch._errors import BrowserNotAvailable


class TestGetDefaultBackend:
    def test_returns_string(self) -> None:
        """Either returns a backend name or raises BrowserNotAvailable."""
        try:
            result = get_default_backend()
            assert result in ("camoufox", "patchright")
        except BrowserNotAvailable:
            pass  # Expected when no browser is installed


class TestBrowserNotAvailable:
    def test_error_message_includes_install_hint(self) -> None:
        exc = BrowserNotAvailable("camoufox")
        assert "pip install" in str(exc)
        assert "camoufox" in str(exc)

    def test_generic_backend_error(self) -> None:
        exc = BrowserNotAvailable("browser")
        assert "pip install" in str(exc)

    def test_patchright_backend_error(self) -> None:
        exc = BrowserNotAvailable("patchright")
        assert "pip install" in str(exc)
        assert "patchright" in str(exc)

    def test_backend_name_attribute(self) -> None:
        exc = BrowserNotAvailable("patchright")
        assert exc.backend_name == "patchright"
