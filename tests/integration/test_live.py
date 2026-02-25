"""Integration tests — real HTTP requests.

Run with: pytest tests_integration/ --run-integration
"""

from __future__ import annotations

import pytest


class TestLiveFetch:
    def test_wikipedia(self) -> None:
        from stealthfetch import fetch_markdown

        md = fetch_markdown(
            "https://en.wikipedia.org/wiki/Web_scraping", method="http"
        )
        assert len(md) > 100
        assert "scraping" in md.lower() or "web" in md.lower()

    def test_example_com(self) -> None:
        from stealthfetch import fetch_markdown

        md = fetch_markdown("https://example.com", method="http")
        assert "Example Domain" in md or "example" in md.lower()

    @pytest.mark.asyncio
    async def test_async_fetch(self) -> None:
        from stealthfetch import afetch_markdown

        md = await afetch_markdown("https://example.com", method="http")
        assert len(md) > 0
