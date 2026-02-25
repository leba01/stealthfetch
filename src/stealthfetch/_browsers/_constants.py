"""Shared constants and utilities for browser backends."""

BODY_READY_JS = "document.body && document.body.innerText.trim().length > 100"
BODY_READY_TIMEOUT = 10_000  # ms


def build_proxy(proxy: dict[str, str] | None) -> dict[str, str] | None:
    """Convert a stealthfetch proxy dict to a Playwright-compatible proxy dict."""
    if not proxy:
        return None
    result: dict[str, str] = {"server": proxy["server"]}
    if "username" in proxy:
        result["username"] = proxy["username"]
    if "password" in proxy:
        result["password"] = proxy["password"]
    return result
