"""StealthFetch error hierarchy."""

from __future__ import annotations

import ipaddress
import socket
from typing import ClassVar
from urllib.parse import urlparse


class StealthFetchError(Exception):
    """Base error for all StealthFetch exceptions."""

    def __init__(self, message: str, *, url: str = "", reason: str = "") -> None:
        self.url = url
        self.reason = reason
        super().__init__(message)


class FetchError(StealthFetchError):
    """Could not fetch the URL."""

    def __init__(self, url: str, reason: str = "") -> None:
        super().__init__(
            f"Failed to fetch {url}: {reason}" if reason else f"Failed to fetch {url}",
            url=url,
            reason=reason,
        )


class ExtractionError(StealthFetchError):
    """Could not extract main content from HTML."""

    def __init__(self, url: str, reason: str = "") -> None:
        super().__init__(
            f"Extraction failed for {url}: {reason}"
            if reason
            else f"Extraction failed for {url}",
            url=url,
            reason=reason,
        )


class BrowserNotAvailable(StealthFetchError):
    """Requested browser backend is not installed."""

    _INSTALL_HINTS: ClassVar[dict[str, str]] = {
        "camoufox": 'pip install "stealthfetch[camoufox]" && camoufox fetch',
        "patchright": 'pip install "stealthfetch[patchright]"',
    }

    def __init__(self, backend_name: str) -> None:
        hint = self._INSTALL_HINTS.get(backend_name, 'pip install "stealthfetch[browser]"')
        super().__init__(
            f"Browser backend '{backend_name}' is not installed. Install with: {hint}",
            url="",
            reason=f"missing dependency: {backend_name}",
        )
        self.backend_name = backend_name


_ALLOWED_SCHEMES = frozenset({"http", "https"})


def validate_url(url: str) -> None:
    """Validate that a URL is safe to fetch (no SSRF).

    Rejects:
        - Non-http(s) schemes (file://, javascript:, ftp://, etc.)
        - Private/loopback IPs (127.x, 10.x, 172.16-31.x, 192.168.x, 169.254.x)
        - Empty or malformed URLs

    Raises:
        ValueError: If the URL is not safe to fetch.
    """
    if not url or not url.strip():
        raise ValueError("URL must not be empty")

    parsed = urlparse(url)

    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(
            f"URL scheme '{parsed.scheme}' is not allowed. Only http and https are supported."
        )

    if not parsed.hostname:
        raise ValueError(f"URL has no hostname: {url}")

    # Check for private/loopback IPs (literal)
    try:
        addr = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        pass  # Not a literal IP — check via DNS below
    else:
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_unspecified:
            raise ValueError(
                f"URL points to a private/loopback address ({parsed.hostname}). "
                "This is not allowed for security reasons."
            )

    # Resolve hostname and validate all addresses against private ranges
    try:
        infos = socket.getaddrinfo(parsed.hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return  # Can't resolve — let the fetch layer handle it

    for info in infos:
        resolved = ipaddress.ip_address(info[4][0])
        # Check IPv6-mapped IPv4
        if hasattr(resolved, "ipv4_mapped") and resolved.ipv4_mapped:
            resolved = resolved.ipv4_mapped
        if (
            resolved.is_private
            or resolved.is_loopback
            or resolved.is_link_local
            or resolved.is_unspecified
        ):
            raise ValueError(
                f"URL hostname '{parsed.hostname}' resolves to private/loopback "
                f"address ({resolved}). This is not allowed for security reasons."
            )


def validate_proxy(proxy: dict[str, str]) -> None:
    """Validate that a proxy dict has the required 'server' key.

    Raises:
        ValueError: If 'server' key is missing.
    """
    if "server" not in proxy:
        raise ValueError(
            "Proxy dict must contain a 'server' key. "
            'Example: {"server": "http://proxy:8080", "username": "u", "password": "p"}'
        )
