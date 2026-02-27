"""Browser backend dispatcher."""

from __future__ import annotations

from stealthfetch._compat import get_default_backend, require_browser


def fetch_browser(
    url: str,
    *,
    backend: str = "auto",
    timeout: int = 30,
    proxy: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> str:
    """Fetch a URL using a stealth browser (sync).

    Args:
        url: The URL to fetch.
        backend: "auto", "camoufox", or "patchright".
        timeout: Timeout in seconds.
        proxy: Proxy config dict with "server", optional "username"/"password".
        headers: Additional HTTP headers to send with the request.

    Returns:
        Rendered HTML string.
    """
    name = _resolve_backend(backend)
    if name == "camoufox":
        from stealthfetch._browsers._camoufox import fetch as _cfetch

        return _cfetch(url, timeout=timeout, proxy=proxy, headers=headers)
    else:
        from stealthfetch._browsers._patchright import fetch as _pfetch

        return _pfetch(url, timeout=timeout, proxy=proxy, headers=headers)


async def afetch_browser(
    url: str,
    *,
    backend: str = "auto",
    timeout: int = 30,
    proxy: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> str:
    """Fetch a URL using a stealth browser (async).

    Args:
        url: The URL to fetch.
        backend: "auto", "camoufox", or "patchright".
        timeout: Timeout in seconds.
        proxy: Proxy config dict with "server", optional "username"/"password".
        headers: Additional HTTP headers to send with the request.

    Returns:
        Rendered HTML string.
    """
    name = _resolve_backend(backend)
    if name == "camoufox":
        from stealthfetch._browsers._camoufox import afetch as _cafetch

        return await _cafetch(url, timeout=timeout, proxy=proxy, headers=headers)
    else:
        from stealthfetch._browsers._patchright import afetch as _pafetch

        return await _pafetch(url, timeout=timeout, proxy=proxy, headers=headers)


def _resolve_backend(backend: str) -> str:
    """Resolve 'auto' to a concrete backend name and validate availability."""
    if backend == "auto":
        return get_default_backend()
    require_browser(backend)
    return backend
