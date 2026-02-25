"""Basic usage of StealthFetch."""

from stealthfetch import fetch_markdown

# Simple fetch — URL in, markdown out
md = fetch_markdown("https://en.wikipedia.org/wiki/Web_scraping")
print(md[:500])
print(f"\n--- Total length: {len(md)} chars ---")
