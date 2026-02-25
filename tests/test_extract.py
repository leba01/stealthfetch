"""Tests for content extraction via trafilatura."""

from __future__ import annotations

import pytest

from stealthfetch._core import _extract_content, _extract_metadata
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


class TestMetadataExtraction:
    def test_returns_all_expected_keys(self, article_html: str) -> None:
        meta = _extract_metadata(article_html, url="https://example.com/article")
        for key in ("title", "author", "date", "description", "url", "hostname", "sitename"):
            assert key in meta

    def test_title_extracted(self, article_html: str) -> None:
        meta = _extract_metadata(article_html, url="https://example.com/article")
        assert meta["title"] is not None
        assert isinstance(meta["title"], str)

    def test_values_are_str_or_none(self, article_html: str) -> None:
        meta = _extract_metadata(article_html, url="https://example.com/article")
        for key, value in meta.items():
            assert value is None or isinstance(value, str), f"{key} has unexpected type"

    def test_empty_html_returns_none_values(self) -> None:
        empty_html = "<!DOCTYPE html><html><head></head><body></body></html>"
        meta = _extract_metadata(empty_html)
        # Should not raise; values may be None for empty pages
        assert isinstance(meta, dict)
        for key in ("title", "author", "date", "description", "url", "hostname", "sitename"):
            assert key in meta

    def test_no_url_still_returns_dict(self, article_html: str) -> None:
        meta = _extract_metadata(article_html)
        assert isinstance(meta, dict)
        assert "title" in meta
