"""Camoufox browser backend — sync and async."""

from __future__ import annotations

import logging

from stealthfetch._browsers._constants import BODY_READY_JS, BODY_READY_TIMEOUT, build_proxy

logger = logging.getLogger(__name__)


def fetch(
    url: str,
    *,
    timeout: int = 30,
    proxy: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> str:
    """Fetch a URL with Camoufox stealth browser (sync)."""
    from camoufox.sync_api import Camoufox

    logger.debug("Camoufox sync fetch: %s", url)
    camoufox_proxy = build_proxy(proxy)

    with Camoufox(  # type: ignore[no-untyped-call]
        headless=True,
        proxy=camoufox_proxy,
        geoip=bool(proxy),
        block_images=True,
        block_webrtc=True,
    ) as browser:
        page = browser.new_page()
        page.set_default_timeout(timeout * 1000)
        if headers:
            page.set_extra_http_headers(headers)
        page.goto(url, wait_until="domcontentloaded")
        try:
            page.wait_for_function(BODY_READY_JS, timeout=BODY_READY_TIMEOUT)
        except Exception:
            logger.debug("Body readiness check timed out, continuing with current content")
        return str(page.content())


async def afetch(
    url: str,
    *,
    timeout: int = 30,
    proxy: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> str:
    """Fetch a URL with Camoufox stealth browser (async)."""
    from camoufox.async_api import AsyncCamoufox

    logger.debug("Camoufox async fetch: %s", url)
    camoufox_proxy = build_proxy(proxy)

    async with AsyncCamoufox(  # type: ignore[no-untyped-call]
        headless=True,
        proxy=camoufox_proxy,
        geoip=bool(proxy),
        block_images=True,
        block_webrtc=True,
    ) as browser:
        page = await browser.new_page()
        page.set_default_timeout(timeout * 1000)
        if headers:
            await page.set_extra_http_headers(headers)
        await page.goto(url, wait_until="domcontentloaded")
        try:
            await page.wait_for_function(BODY_READY_JS, timeout=BODY_READY_TIMEOUT)
        except Exception:
            logger.debug("Body readiness check timed out, continuing with current content")
        return str(await page.content())
