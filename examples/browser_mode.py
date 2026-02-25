"""Browser mode for JS-heavy sites.

Requires: pip install "stealthfetch[browser]" && camoufox fetch
"""

from stealthfetch import fetch_markdown

# Force browser mode for JS-rendered SPAs
md = fetch_markdown(
    "https://en.wikipedia.org/wiki/Web_scraping",
    method="browser",
)
print(md[:500])

# Use a specific browser backend
md = fetch_markdown(
    "https://en.wikipedia.org/wiki/Web_scraping",
    method="browser",
    browser_backend="camoufox",
)
print(md[:500])
