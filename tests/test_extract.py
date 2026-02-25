"""Tests for content extraction via trafilatura."""

from __future__ import annotations

import pytest

from stealthfetch._core import _extract_content
from stealthfetch._errors import ExtractionError


class TestExtraction:
    def test_article_extracts_content(self, article_html: str) -> None:
        result = _extract_content(article_html, url="https://example.com/article")
        assert "bioluminescent jellyfish" in result
        assert "Mariana Trench" in result

    def test_article_strips_nav(self, article_html: str) -> None:
        result = _extract_content(article_html, url="https://example.com/article")
        assert "Privacy" not in result
        assert "Terms" not in result

    def test_tables_preserved(self, tables_html: str) -> None:
        result = _extract_content(tables_html, include_tables=True)
        assert "ProBook" in result or "PowerMax" in result

    def test_extraction_returns_html(self, article_html: str) -> None:
        result = _extract_content(article_html, url="https://example.com/article")
        # trafilatura output_format="html" should contain HTML tags
        assert "<" in result

    def test_truly_empty_raises(self) -> None:
        """Pages with no extractable content cause trafilatura to return None."""
        empty_html = "<!DOCTYPE html><html><head></head><body></body></html>"
        with pytest.raises(ExtractionError):
            _extract_content(empty_html, url="https://example.com/empty")

    def test_links_included_by_default(self, article_html: str) -> None:
        result = _extract_content(
            article_html, include_links=True, url="https://example.com/article"
        )
        assert "href" in result or "research page" in result
