---
name: fetching-web-content
description: >
  Fetches web pages and returns clean, LLM-ready markdown with automatic
  anti-bot bypass. Handles Cloudflare, DataDome, PerimeterX, and Akamai
  by auto-escalating from HTTP to a stealth browser. Use when fetching
  URLs, scraping websites, reading web pages as markdown, or when a
  site blocks normal HTTP requests. Built-in SSRF protection.
---

# StealthFetch

## Quick start

```python
from stealthfetch import fetch_markdown

md = fetch_markdown("https://en.wikipedia.org/wiki/Web_scraping")
```

One function. No config. Returns clean markdown.

## When to use what

**`fetch_markdown(url)`** — just need the text content as markdown.

**`fetch_result(url)`** — need page metadata (title, author, date, description) alongside the markdown. Returns a `FetchResult` dataclass.

**`method="browser"`** — force stealth browser for JavaScript-heavy SPAs that render content client-side. Default `"auto"` handles most cases (tries HTTP first, escalates on block detection).

## Async

All functions have async variants: `afetch_markdown`, `afetch_result`. Same signatures.

```python
from stealthfetch import afetch_markdown

md = await afetch_markdown("https://example.com")
```

## Common parameters

| Parameter | Default | When to change |
|-----------|---------|----------------|
| `include_links` | `True` | Set `False` to strip hyperlinks |
| `include_images` | `False` | Set `True` to preserve image references |
| `include_tables` | `True` | Set `False` to strip tables |
| `timeout` | `30` | Increase for slow sites |
| `headers` | `None` | Pass cookies or auth headers |
| `proxy` | `None` | `{"server": "http://proxy:8080"}` |

## Error handling

```python
from stealthfetch import StealthFetchError, FetchError, ExtractionError

try:
    md = fetch_markdown(url)
except FetchError:
    # Could not reach the URL (network, blocked, timeout)
except ExtractionError:
    # Page fetched but no main content found
```

`BrowserNotAvailable` is raised when browser mode is needed but no backend is installed.

## Full API reference

See [reference.md](reference.md) for complete function signatures, all parameters, and the `FetchResult` dataclass.
