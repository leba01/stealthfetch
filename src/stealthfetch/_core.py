"""Core 3-layer pipeline: fetch → extract → convert."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from stealthfetch._compat import has_camoufox, has_patchright
from stealthfetch._detect import looks_blocked
from stealthfetch._errors import (
    ExtractionError,
    FetchError,
    validate_proxy,
    validate_url,
)

logger = logging.getLogger(__name__)

_VALID_METHODS = frozenset({"auto", "http", "browser"})
_VALID_BACKENDS = frozenset({"auto", "camoufox", "patchright"})
_MAX_RESPONSE_BYTES = 50_000_000  # 50 MB


@dataclass
class FetchResult:
    """Structured result containing markdown and page metadata."""

    markdown: str
    title: str | None
    author: str | None
    date: str | None
    description: str | None
    url: str | None
    hostname: str | None
    sitename: str | None


# --- Layer 1: Fetch ---


def _validate_params(
    url: str,
    method: str,
    browser_backend: str,
    proxy: dict[str, str] | None,
) -> None:
    """Validate all user-facing parameters up front."""
    validate_url(url)
    if method not in _VALID_METHODS:
        raise ValueError(
            f"Invalid method '{method}'. Must be one of: {', '.join(sorted(_VALID_METHODS))}"
        )
    if browser_backend not in _VALID_BACKENDS:
        raise ValueError(
            f"Invalid browser_backend '{browser_backend}'. "
            f"Must be one of: {', '.join(sorted(_VALID_BACKENDS))}"
        )
    if proxy is not None:
        validate_proxy(proxy)


def _build_curl_proxies(proxy: dict[str, str] | None) -> dict[str, str] | None:
    """Convert our proxy dict to curl_cffi's proxies format.

    curl_cffi expects credentials embedded in the URL (http://user:pass@host:port),
    unlike Playwright which takes them as separate fields.
    """
    if not proxy:
        return None
    server = proxy["server"]
    if "username" in proxy:
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(server)
        userinfo = proxy["username"]
        if "password" in proxy:
            userinfo += f":{proxy['password']}"
        netloc = f"{userinfo}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
        server = urlunparse(parsed._replace(netloc=netloc))
    return {"https": server, "http": server}


def _fetch_http(
    url: str,
    *,
    timeout: int = 30,
    proxy: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[str, int, str]:
    """Fetch via curl_cffi with Chrome TLS fingerprint.

    Returns:
        (html, status_code, content_type) tuple.
    """
    from curl_cffi import requests as curl_requests

    proxies = _build_curl_proxies(proxy)

    r = curl_requests.get(
        url,
        impersonate="chrome",
        timeout=timeout,
        proxies=proxies,  # type: ignore[arg-type]
        headers=headers,
    )
    # Validate final URL after redirects to prevent SSRF via 302
    try:
        validate_url(str(r.url))
    except ValueError as exc:
        raise FetchError(url, reason=str(exc)) from exc
    if len(r.content) > _MAX_RESPONSE_BYTES:
        raise FetchError(url, reason=f"Response too large ({len(r.content)} bytes)")
    content_type: str = r.headers.get("content-type", "text/html")
    return str(r.text), int(r.status_code), content_type


async def _afetch_http(
    url: str,
    *,
    timeout: int = 30,
    proxy: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[str, int, str]:
    """Async fetch via curl_cffi."""
    from curl_cffi import requests as curl_requests

    proxies = _build_curl_proxies(proxy)

    async with curl_requests.AsyncSession() as session:
        r = await session.get(
            url,
            impersonate="chrome",
            timeout=timeout,
            proxies=proxies,
            headers=headers,
        )
        # Validate final URL after redirects to prevent SSRF via 302
        try:
            validate_url(str(r.url))
        except ValueError as exc:
            raise FetchError(url, reason=str(exc)) from exc
        if len(r.content) > _MAX_RESPONSE_BYTES:
            raise FetchError(url, reason=f"Response too large ({len(r.content)} bytes)")
        # Extract response data while session is still alive
        content_type: str = r.headers.get("content-type", "text/html")
        text = str(r.text)
        status_code = int(r.status_code)
    return text, status_code, content_type


def _has_any_browser() -> bool:
    return has_camoufox() or has_patchright()


def _fetch(
    url: str,
    *,
    method: str = "auto",
    browser_backend: str = "auto",
    timeout: int = 30,
    proxy: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> str:
    """Fetch HTML with auto-escalation (sync)."""
    from stealthfetch._browsers import fetch_browser

    if method == "browser":
        return fetch_browser(
            url, backend=browser_backend, timeout=timeout, proxy=proxy, headers=headers
        )

    if method == "http":
        html, status_code, _ = _fetch_http(url, timeout=timeout, proxy=proxy, headers=headers)
        if status_code >= 400:
            raise FetchError(url, reason=f"HTTP {status_code}")
        return html

    # auto: try HTTP first, escalate to browser if blocked
    try:
        html, status_code, content_type = _fetch_http(
            url, timeout=timeout, proxy=proxy, headers=headers
        )
    except Exception as exc:
        logger.debug("HTTP fetch failed: %s", exc)
        if _has_any_browser():
            logger.info("Escalating to browser after HTTP failure")
            return fetch_browser(
                url, backend=browser_backend, timeout=timeout, proxy=proxy, headers=headers
            )
        raise FetchError(url, reason=str(exc)) from exc

    if looks_blocked(html, status_code=status_code, content_type=content_type):
        if _has_any_browser():
            logger.info("Response looks blocked, escalating to browser")
            return fetch_browser(
                url, backend=browser_backend, timeout=timeout, proxy=proxy, headers=headers
            )
        logger.warning(
            "Response looks blocked but no browser backend installed. "
            "Install with: pip install 'stealthfetch[browser]'"
        )

    return html


async def _afetch(
    url: str,
    *,
    method: str = "auto",
    browser_backend: str = "auto",
    timeout: int = 30,
    proxy: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> str:
    """Fetch HTML with auto-escalation (async)."""
    from stealthfetch._browsers import afetch_browser

    if method == "browser":
        return await afetch_browser(
            url, backend=browser_backend, timeout=timeout, proxy=proxy, headers=headers
        )

    if method == "http":
        html, status_code, _ = await _afetch_http(
            url, timeout=timeout, proxy=proxy, headers=headers
        )
        if status_code >= 400:
            raise FetchError(url, reason=f"HTTP {status_code}")
        return html

    # auto: try HTTP first, escalate to browser if blocked
    try:
        html, status_code, content_type = await _afetch_http(
            url, timeout=timeout, proxy=proxy, headers=headers
        )
    except Exception as exc:
        logger.debug("HTTP fetch failed: %s", exc)
        if _has_any_browser():
            logger.info("Escalating to browser after HTTP failure")
            return await afetch_browser(
                url, backend=browser_backend, timeout=timeout, proxy=proxy, headers=headers
            )
        raise FetchError(url, reason=str(exc)) from exc

    if looks_blocked(html, status_code=status_code, content_type=content_type):
        if _has_any_browser():
            logger.info("Response looks blocked, escalating to browser")
            return await afetch_browser(
                url, backend=browser_backend, timeout=timeout, proxy=proxy, headers=headers
            )
        logger.warning(
            "Response looks blocked but no browser backend installed. "
            "Install with: pip install 'stealthfetch[browser]'"
        )

    return html


# --- Layer 2: Extract ---


def _extract_content(
    html: str,
    *,
    include_links: bool = True,
    include_images: bool = False,
    include_tables: bool = True,
    url: str = "",
) -> str:
    """Extract main content via trafilatura, return clean HTML."""
    from trafilatura import extract

    result: str | None = extract(
        html,
        output_format="html",
        include_links=include_links,
        include_images=include_images,
        include_tables=include_tables,
        include_formatting=True,
        include_comments=False,
        favor_recall=True,
        url=url,
    )
    if result is None:
        raise ExtractionError(url, reason="trafilatura returned None")
    return str(result)


def _extract_metadata(html: str, *, url: str = "") -> dict[str, str | None]:
    """Extract page metadata via trafilatura."""
    from trafilatura import extract_metadata

    doc = extract_metadata(html, url or None)
    if doc is None:
        keys = ("title", "author", "date", "description", "url", "hostname", "sitename")
        return dict.fromkeys(keys)
    return {
        "title": doc.title,
        "author": doc.author,
        "date": doc.date,
        "description": doc.description,
        "url": doc.url,
        "hostname": doc.hostname,
        "sitename": doc.sitename,
    }


# --- Layer 3: Convert ---


def _to_markdown(html: str) -> str:
    """Convert clean HTML to markdown via html-to-markdown."""
    from html_to_markdown import ConversionOptions, convert

    options = ConversionOptions(heading_style="atx", wrap=False)
    return convert(html, options)


# --- Public API ---


def fetch_markdown(
    url: str,
    *,
    method: str = "auto",
    browser_backend: str = "auto",
    include_links: bool = True,
    include_images: bool = False,
    include_tables: bool = True,
    timeout: int = 30,
    proxy: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> str:
    """Fetch a URL and return clean, LLM-ready markdown.

    Args:
        url: The URL to fetch.
        method: Fetch method. "auto" tries HTTP first, escalates to browser
                on failure. "http" forces curl_cffi. "browser" forces browser.
        browser_backend: "auto", "camoufox", or "patchright". Only used when
                browser mode is triggered.
        include_links: Preserve hyperlinks in markdown output.
        include_images: Preserve image references in markdown output.
        include_tables: Preserve tables in markdown output.
        timeout: Request timeout in seconds.
        proxy: Proxy config dict {"server": str, "username": str, "password": str}.
        headers: Additional HTTP headers (merged with impersonation defaults).

    Returns:
        Clean markdown string of the page's main content.

    Raises:
        FetchError: If the page cannot be fetched after all methods exhausted.
        ExtractionError: If no main content can be extracted from the HTML.
        ValueError: If url, method, browser_backend, or proxy are invalid.
    """
    _validate_params(url, method, browser_backend, proxy)

    raw_html = _fetch(
        url,
        method=method,
        browser_backend=browser_backend,
        timeout=timeout,
        proxy=proxy,
        headers=headers,
    )
    clean_html = _extract_content(
        raw_html,
        include_links=include_links,
        include_images=include_images,
        include_tables=include_tables,
        url=url,
    )
    markdown = _to_markdown(clean_html).strip()

    if not markdown:
        raise ExtractionError(url, reason="conversion produced empty markdown")

    return markdown


async def afetch_markdown(
    url: str,
    *,
    method: str = "auto",
    browser_backend: str = "auto",
    include_links: bool = True,
    include_images: bool = False,
    include_tables: bool = True,
    timeout: int = 30,
    proxy: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> str:
    """Async version of fetch_markdown. Same signature and behavior."""
    _validate_params(url, method, browser_backend, proxy)

    raw_html = await _afetch(
        url,
        method=method,
        browser_backend=browser_backend,
        timeout=timeout,
        proxy=proxy,
        headers=headers,
    )

    # Run CPU-bound extract + convert off the event loop
    clean_html = await asyncio.to_thread(
        _extract_content,
        raw_html,
        include_links=include_links,
        include_images=include_images,
        include_tables=include_tables,
        url=url,
    )
    markdown = (await asyncio.to_thread(_to_markdown, clean_html)).strip()

    if not markdown:
        raise ExtractionError(url, reason="conversion produced empty markdown")

    return markdown


def fetch_result(
    url: str,
    *,
    method: str = "auto",
    browser_backend: str = "auto",
    include_links: bool = True,
    include_images: bool = False,
    include_tables: bool = True,
    timeout: int = 30,
    proxy: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> FetchResult:
    """Fetch a URL and return structured result with markdown and page metadata.

    Args:
        url: The URL to fetch.
        method: Fetch method. "auto" tries HTTP first, escalates to browser
                on failure. "http" forces curl_cffi. "browser" forces browser.
        browser_backend: "auto", "camoufox", or "patchright". Only used when
                browser mode is triggered.
        include_links: Preserve hyperlinks in markdown output.
        include_images: Preserve image references in markdown output.
        include_tables: Preserve tables in markdown output.
        timeout: Request timeout in seconds.
        proxy: Proxy config dict {"server": str, "username": str, "password": str}.
        headers: Additional HTTP headers (merged with impersonation defaults).

    Returns:
        FetchResult with markdown content and metadata fields (title, author,
        date, description, url, hostname, sitename).

    Raises:
        FetchError: If the page cannot be fetched after all methods exhausted.
        ExtractionError: If no main content can be extracted from the HTML.
        ValueError: If url, method, browser_backend, or proxy are invalid.
    """
    _validate_params(url, method, browser_backend, proxy)

    raw_html = _fetch(
        url,
        method=method,
        browser_backend=browser_backend,
        timeout=timeout,
        proxy=proxy,
        headers=headers,
    )
    clean_html = _extract_content(
        raw_html,
        include_links=include_links,
        include_images=include_images,
        include_tables=include_tables,
        url=url,
    )
    markdown = _to_markdown(clean_html).strip()

    if not markdown:
        raise ExtractionError(url, reason="conversion produced empty markdown")

    meta = _extract_metadata(raw_html, url=url)
    return FetchResult(
        markdown=markdown,
        title=meta["title"],
        author=meta["author"],
        date=meta["date"],
        description=meta["description"],
        url=meta["url"],
        hostname=meta["hostname"],
        sitename=meta["sitename"],
    )


async def afetch_result(
    url: str,
    *,
    method: str = "auto",
    browser_backend: str = "auto",
    include_links: bool = True,
    include_images: bool = False,
    include_tables: bool = True,
    timeout: int = 30,
    proxy: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> FetchResult:
    """Async version of fetch_result. Same signature and behavior."""
    _validate_params(url, method, browser_backend, proxy)

    raw_html = await _afetch(
        url,
        method=method,
        browser_backend=browser_backend,
        timeout=timeout,
        proxy=proxy,
        headers=headers,
    )

    # Run CPU-bound extract + convert off the event loop
    clean_html = await asyncio.to_thread(
        _extract_content,
        raw_html,
        include_links=include_links,
        include_images=include_images,
        include_tables=include_tables,
        url=url,
    )
    markdown = (await asyncio.to_thread(_to_markdown, clean_html)).strip()

    if not markdown:
        raise ExtractionError(url, reason="conversion produced empty markdown")

    meta = await asyncio.to_thread(_extract_metadata, raw_html, url=url)
    return FetchResult(
        markdown=markdown,
        title=meta["title"],
        author=meta["author"],
        date=meta["date"],
        description=meta["description"],
        url=meta["url"],
        hostname=meta["hostname"],
        sitename=meta["sitename"],
    )
