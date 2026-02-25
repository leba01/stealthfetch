"""Tests for block/captcha detection heuristics."""

from __future__ import annotations

import pytest

from stealthfetch._detect import looks_blocked


class TestStatusCodes:
    @pytest.mark.parametrize(
        ("status_code", "expected"),
        [
            (403, True),
            (429, True),
            (503, True),
            (200, False),
            (301, False),
        ],
    )
    def test_status_code_detection(self, status_code: int, expected: bool) -> None:
        html = "<html><body>Some content</body></html>"
        assert looks_blocked(html, status_code=status_code) is expected


class TestContentType:
    def test_json_not_blocked(self) -> None:
        """Non-HTML content types are NOT blocked — they're legitimate responses."""
        assert looks_blocked("{}", content_type="application/json") is False

    def test_pdf_not_blocked(self) -> None:
        assert looks_blocked("", content_type="application/pdf") is False

    def test_xml_not_blocked(self) -> None:
        assert looks_blocked("<xml/>", content_type="application/xml") is False

    def test_html_not_blocked(self) -> None:
        assert (
            looks_blocked("<html></html>", content_type="text/html; charset=utf-8")
            is False
        )

    def test_empty_content_type_not_blocked(self) -> None:
        assert looks_blocked("<html></html>", content_type="") is False


class TestPatternMatching:
    @pytest.mark.parametrize(
        ("html", "reason"),
        [
            ("<html><body>Just a moment...</body></html>", "just a moment"),
            ("<html><body>Access Denied</body></html>", "access denied"),
            ('<html><script src="dd.js"></script></html>', "datadome"),
            ("<html><div id='px-captcha'></div></html>", "perimeterx"),
            ("<html><body>Bot Manager detected</body></html>", "bot manager"),
            (
                "<html><body>unusual traffic from your network</body></html>",
                "unusual traffic",
            ),
        ],
        ids=["just-a-moment", "access-denied", "datadome", "perimeterx",
             "bot-manager", "unusual-traffic"],
    )
    def test_pattern_detected(self, html: str, reason: str) -> None:
        assert looks_blocked(html) is True, f"should detect {reason}"

    def test_cloudflare_verification(self, cloudflare_html: str) -> None:
        assert looks_blocked(cloudflare_html) is True

    def test_captcha_page(self, captcha_html: str) -> None:
        assert looks_blocked(captcha_html) is True


class TestThreshold:
    def test_large_page_with_weak_pattern_not_blocked(self) -> None:
        """Large pages with weak patterns are not flagged (false-positive guard)."""
        html = "<html><body>" + ("x" * 15_000) + " captcha </body></html>"
        assert looks_blocked(html) is False

    def test_large_page_with_strong_pattern_blocked(self) -> None:
        """Large pages with strong (vendor-specific) patterns are still caught."""
        html = "<html><body>" + ("x" * 20_000) + " cf-browser-verification </body></html>"
        assert looks_blocked(html) is True

    def test_large_page_with_challenge_platform_not_blocked(self) -> None:
        """challenge-platform is passive CF JS — not a block signal on large pages."""
        script = "<script src='/cdn-cgi/challenge-platform/scripts/jsd/main.js'></script>"
        html = f"<html><head>{script}</head><body>" + ("x" * 20_000) + "</body></html>"
        assert looks_blocked(html) is False

    def test_reddit_challenge_blocked(self, reddit_challenge_html: str) -> None:
        """Reddit's 'prove your humanity' page is detected even though it's large."""
        assert len(reddit_challenge_html) > 15_000
        assert looks_blocked(reddit_challenge_html) is True

    def test_small_page_with_pattern_blocked(self) -> None:
        html = "<html><body>captcha required</body></html>"
        assert looks_blocked(html) is True

    def test_normal_article_not_blocked(self, article_html: str) -> None:
        assert looks_blocked(article_html) is False
