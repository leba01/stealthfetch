"""Patchright browser backend — sync and async."""

from __future__ import annotations

import logging

from stealthfetch._browsers._constants import BODY_READY_JS, BODY_READY_TIMEOUT, build_proxy

logger = logging.getLogger(__name__)


def fetch(
    url: str,
    *,
    timeout: int = 30,
    proxy: dict[str, str] | None = None,
) -> str:
    """Fetch a URL with Patchright stealth browser (sync)."""
    from patchright.sync_api import sync_playwright

    logger.debug("Patchright sync fetch: %s", url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, proxy=build_proxy(proxy))  # type: ignore[arg-type]
        try:
            page = browser.new_page()
            page.set_default_timeout(timeout * 1000)
            page.goto(url, wait_until="domcontentloaded")
            try:
                page.wait_for_function(BODY_READY_JS, timeout=BODY_READY_TIMEOUT)
            except Exception:
                logger.debug(
                    "Body readiness check timed out, continuing with current content"
                )
            return str(page.content())
        finally:
            browser.close()


async def afetch(
    url: str,
    *,
    timeout: int = 30,
    proxy: dict[str, str] | None = None,
) -> str:
    """Fetch a URL with Patchright stealth browser (async)."""
    from patchright.async_api import async_playwright

    logger.debug("Patchright async fetch: %s", url)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, proxy=build_proxy(proxy))  # type: ignore[arg-type]
        try:
            page = await browser.new_page()
            page.set_default_timeout(timeout * 1000)
            await page.goto(url, wait_until="domcontentloaded")
            try:
                await page.wait_for_function(BODY_READY_JS, timeout=BODY_READY_TIMEOUT)
            except Exception:
                logger.debug(
                    "Body readiness check timed out, continuing with current content"
                )
            return str(await page.content())
        finally:
            await browser.close()
