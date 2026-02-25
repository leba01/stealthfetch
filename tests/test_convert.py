"""Tests for HTML-to-markdown conversion."""

from __future__ import annotations

from stealthfetch._core import _to_markdown


class TestConversion:
    def test_headings_use_atx_style(self) -> None:
        assert "# Title" in _to_markdown("<h1>Title</h1>")
        assert "## Sub" in _to_markdown("<h2>Sub</h2>")

    def test_inline_formatting(self) -> None:
        assert "**bold**" in _to_markdown("<strong>bold</strong>")
        assert "*em*" in _to_markdown("<em>em</em>")

    def test_table(self) -> None:
        html = """<table>
        <thead><tr><th>Name</th><th>Value</th></tr></thead>
        <tbody><tr><td>A</td><td>1</td></tr></tbody>
        </table>"""
        md = _to_markdown(html)
        assert "Name" in md
        assert "|" in md

    def test_empty_html(self) -> None:
        assert _to_markdown("").strip() == ""
