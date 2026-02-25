"""Block and captcha detection heuristics."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_BLOCKED_STATUS_CODES = frozenset({403, 429, 503})

# Anti-bot vendor signatures + challenge page phrases.
# Checked on ALL pages regardless of size — these never appear in real content.
_STRONG_PATTERNS = (
    # Cloudflare (actual challenge page elements, not passive JS)
    "cf-browser-verification",
    "_cf_chl_opt",
    # DataDome
    "datadome",
    "dd.js",
    # PerimeterX
    "perimeterx",
    "px-captcha",
    # Akamai
    "bot manager",
    # Challenge page phrases
    "prove your humanity",
    "verify you are human",
)

# Generic phrases that could appear in real articles or as passive
# scripts on non-blocked pages. Only checked on small pages (< _THRESHOLD_CHARS).
_WEAK_PATTERNS = (
    "just a moment",
    "captcha",
    "access denied",
    "unusual traffic",
    "security check",
    "please verify",
    "ray id",
    # CF bot-management JS loaded on all CF-protected pages, not just challenges
    "challenge-platform",
)

_THRESHOLD_CHARS = 15_000


def looks_blocked(
    html: str,
    *,
    status_code: int = 200,
    content_type: str = "text/html",
) -> bool:
    """Heuristic check: does this response look like a block/captcha page?

    Only checks for anti-bot block pages. Non-HTML content types are NOT
    considered blocked — they are legitimate responses that happen to not
    be HTML (JSON APIs, PDFs, etc.).

    Args:
        html: The response body.
        status_code: HTTP status code.
        content_type: Content-Type header value.

    Returns:
        True if the response appears to be a block page.
    """
    if status_code in _BLOCKED_STATUS_CODES:
        logger.debug("Blocked: HTTP %d", status_code)
        return True

    # Only pattern-check HTML responses — non-HTML is not a block signal
    if content_type and "text/html" not in content_type.lower():
        return False

    lower = html.lower()

    # Strong patterns: always check (vendor-specific, no false-positive risk)
    for pattern in _STRONG_PATTERNS:
        if pattern in lower:
            logger.debug("Blocked: matched strong pattern '%s'", pattern)
            return True

    # Weak patterns: only check small pages to avoid false positives
    if len(html) < _THRESHOLD_CHARS:
        for pattern in _WEAK_PATTERNS:
            if pattern in lower:
                logger.debug("Blocked: matched pattern '%s'", pattern)
                return True

    return False
