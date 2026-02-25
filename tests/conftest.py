"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def article_html() -> str:
    return (FIXTURES_DIR / "article.html").read_text()


@pytest.fixture(scope="session")
def tables_html() -> str:
    return (FIXTURES_DIR / "tables.html").read_text()


@pytest.fixture(scope="session")
def cloudflare_html() -> str:
    return (FIXTURES_DIR / "cloudflare_block.html").read_text()


@pytest.fixture(scope="session")
def captcha_html() -> str:
    return (FIXTURES_DIR / "captcha.html").read_text()


@pytest.fixture(scope="session")
def reddit_challenge_html() -> str:
    return (FIXTURES_DIR / "reddit_challenge.html").read_text()
