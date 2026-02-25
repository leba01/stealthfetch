"""Lazy imports and feature detection for optional browser backends."""

from __future__ import annotations

from stealthfetch._errors import BrowserNotAvailable

# Not using @functools.cache — these check on every call so that
# installing a browser backend mid-process (e.g., in a long-running
# MCP server) is detected without restart.


def has_camoufox() -> bool:
    """Check if camoufox is importable."""
    try:
        import camoufox.sync_api  # noqa: F401

        return True
    except ImportError:
        return False


def has_patchright() -> bool:
    """Check if patchright is importable."""
    try:
        import patchright.sync_api  # noqa: F401

        return True
    except ImportError:
        return False


def require_browser(backend: str) -> None:
    """Raise BrowserNotAvailable if the requested backend is missing."""
    if backend == "camoufox" and not has_camoufox():
        raise BrowserNotAvailable("camoufox")
    if backend == "patchright" and not has_patchright():
        raise BrowserNotAvailable("patchright")


def get_default_backend() -> str:
    """Return the best available browser backend name.

    Raises:
        BrowserNotAvailable: If no browser backend is installed.
    """
    if has_camoufox():
        return "camoufox"
    if has_patchright():
        return "patchright"
    raise BrowserNotAvailable("browser")
