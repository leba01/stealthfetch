# StealthFetch

[![CI](https://github.com/leba01/stealthfetch/actions/workflows/ci.yml/badge.svg)](https://github.com/leba01/stealthfetch/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/stealthfetch)](https://pypi.org/project/stealthfetch/)
[![Python](https://img.shields.io/pypi/pyversions/stealthfetch)](https://pypi.org/project/stealthfetch/)
[![License: AGPL-3.0](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)

URL in, LLM-ready markdown out.

```python
from stealthfetch import fetch_markdown

md = fetch_markdown("https://en.wikipedia.org/wiki/Web_scraping")
```

Fetches any web page, strips nav, ads, and boilerplate, returns clean markdown. If the site blocks you, it auto-escalates to a stealth browser. One function, no config.

StealthFetch doesn't reinvent the hard parts: [curl_cffi](https://github.com/lexiforest/curl_cffi), [trafilatura](https://github.com/adbar/trafilatura), [html-to-markdown](https://github.com/kreuzberg-dev/html-to-markdown), [Camoufox](https://github.com/daijro/camoufox), and [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright) do the heavy lifting. StealthFetch is the orchestration layer: wiring them together, detecting blocks, deciding when to escalate, and handling the security concerns most tools skip.

## How It Works

```
URL
 │
 ▼
┌──────────────────────────────────────────────────────────────────────┐
│  FETCH        curl_cffi · Chrome TLS fingerprint                    │
│               blocked? → auto-escalate to Camoufox / Patchright     │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────────┐
│  EXTRACT      trafilatura · strips nav, ads, boilerplate            │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────────┐
│  CONVERT      html-to-markdown (Rust)                               │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                ▼
                             markdown
```

Each layer is one library call. The libraries do the hard work.

## What StealthFetch Owns

### Block Detection

Most anti-bot systems give themselves away before you ever see a captcha. StealthFetch uses status codes (403, 429, 503) as a fast first pass, then pattern-matches HTML signatures from Cloudflare, DataDome, PerimeterX, and Akamai. The trick is knowing when *not* to check: vendor-specific signatures (like `_cf_chl_opt` or `perimeterx`) are always checked because they never appear in real content. Generic phrases like "just a moment" or "access denied" are only checked on small pages (< 15k chars) since on a real article those strings are just words.

### Auto-Escalation

Headless browsers are slow, heavy, and detectable in their own right. An HTTP request with a Chrome TLS fingerprint (via curl_cffi) gets through most sites just fine. So StealthFetch tries HTTP first always. It only spins up a stealth browser when the response actually looks blocked. The interesting part isn't the browser itself, it's the decision of *when* to use it.

### SSRF Protection

Most scraping tools — [including ones with 60-85k GitHub stars](https://www.bluerock.io/post/mcp-furi-microsoft-markitdown-vulnerabilities) — trust whatever URL you hand them. StealthFetch doesn't. A hostname that resolves to `127.0.0.1`? Rejected. A redirect chain that bounces through three domains and lands on a private IP? Caught. IPv6-mapped IPv4 bypasses, link-local addresses are all validated before the request goes out, and again after redirects resolve.

## Works On

Most sites return clean markdown in **under a second**. Sites behind Cloudflare, DataDome, or PerimeterX get detected and auto-escalated to a stealth browser — takes **5–8 seconds** but you don't have to think about it.

| Site | What You Get |
|------|-------------|
| Wikipedia, Reuters, BBC News, TechCrunch | Articles and news — straight through |
| Hacker News | Threads and comments |
| Stack Overflow | Q&A with code blocks |
| Medium | Articles — Cloudflare-protected, but no false-positive escalation (passive JS, not a block page) |
| Reddit | Blocked. Auto-escalates to browser, but still blocked. Needs proxy rotation (use [Firecrawl](https://github.com/mendableai/firecrawl)). |
| Amazon | Blocked. Same story — CAPTCHA defeats the stealth browser too. |

## Why Should I Use This Over Firecrawl?

Every MCP tool gets injected into the system prompt. This is what that costs:

| | StealthFetch | Firecrawl |
|---|---|---|
| MCP tools registered | 1 | 12 |
| System prompt overhead | ~400 tokens | ~6,000–12,000 tokens |
| Normal site latency | 0.4–0.5s | 2–7s |
| Cloudflare/DataDome site | 0.5s (HTTP) / 5–8s (browser) | 2–7s |
| Cost | Free, AGPL-3.0 | 500 pages/mo free, then $16+/mo |
| Reddit/Amazon | Blocked | Works (proxy rotation) |

StealthFetch is a local HTTP call. Firecrawl is a round-trip to their API. Firecrawl wins on proxy rotation at scale and structured extraction.

## Install

Try it — no install needed (requires [uv](https://docs.astral.sh/uv/getting-started/installation/)):

```bash
uvx stealthfetch https://en.wikipedia.org/wiki/Web_scraping
```

Install as a library:

```bash
pip install stealthfetch
```

> **Note:** trafilatura brings ~20 transitive dependencies (lxml, charset-normalizer, etc.). Total install is ~50 packages.

Add stealth browser support (necessary for escalation logic):

```bash
pip install "stealthfetch[browser]"
camoufox fetch
```

## CLI

```bash
stealthfetch https://en.wikipedia.org/wiki/Web_scraping
stealthfetch https://spa-app.com -m browser
stealthfetch https://example.com --no-links --no-tables
stealthfetch https://example.com --header "Cookie: session=abc"
```

## MCP Server

StealthFetch is an [MCP](https://modelcontextprotocol.io/) server — any MCP client (Claude Desktop, Claude Code, Cursor, etc.) can call it as a tool to fetch web pages as markdown.

No install needed — add this to your MCP client config:

```json
{
  "mcpServers": {
    "stealthfetch": {
      "command": "uvx",
      "args": ["--from", "stealthfetch[mcp]", "stealthfetch-mcp"]
    }
  }
}
```

Or if you prefer a persistent install:

```bash
pip install "stealthfetch[mcp]"
```

```json
{
  "mcpServers": {
    "stealthfetch": {
      "command": "stealthfetch-mcp"
    }
  }
}
```

> **Fun fact:** I use StealthFetch as my web search MCP server inside Claude Code. 

## API

### `fetch_markdown(url, **kwargs) -> str`

Also available as `afetch_markdown` — same signature, async. Extraction and conversion run off the event loop via `asyncio.to_thread`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | required | URL to fetch |
| `method` | `str` | `"auto"` | `"auto"`, `"http"`, or `"browser"` |
| `browser_backend` | `str` | `"auto"` | `"auto"`, `"camoufox"`, or `"patchright"` |
| `include_links` | `bool` | `True` | Preserve hyperlinks |
| `include_images` | `bool` | `False` | Preserve image references |
| `include_tables` | `bool` | `True` | Preserve tables |
| `timeout` | `int` | `30` | Timeout in seconds |
| `proxy` | `dict` | `None` | `{"server": "...", "username": "...", "password": "..."}` |
| `headers` | `dict` | `None` | Additional HTTP headers |


### `fetch_result(url, **kwargs) -> FetchResult`

Same fetch/extract/convert pipeline as `fetch_markdown`, but returns a structured dataclass with the markdown **and** page metadata extracted as a free side-effect of parsing.

```python
from stealthfetch import fetch_result

r = fetch_result("https://en.wikipedia.org/wiki/Web_scraping", method="http")
print(r.title)       # "Web scraping"
print(r.author)      # "Wikipedia contributors" (when available)
print(r.date)        # ISO 8601 date (when available)
print(r.markdown[:200])
```

`FetchResult` fields:

| Field | Type | Description |
|-------|------|-------------|
| `markdown` | `str` | Cleaned markdown content |
| `title` | `str \| None` | Page title |
| `author` | `str \| None` | Author name |
| `date` | `str \| None` | Publication date (ISO 8601 when available) |
| `description` | `str \| None` | Meta description |
| `url` | `str \| None` | Canonical URL (may differ from input) |
| `hostname` | `str \| None` | Hostname |
| `sitename` | `str \| None` | Publisher name |

To get a plain dict: `dataclasses.asdict(result)`.

`afetch_result` has the same signature, async.

## Optional Dependencies

| Extra | What it adds |
|-------|-------------|
| `stealthfetch[camoufox]` | Camoufox stealth Firefox |
| `stealthfetch[patchright]` | Patchright stealth Chromium |
| `stealthfetch[browser]` | Both |
| `stealthfetch[mcp]` | MCP server |

Python 3.10+. Tested on 3.10–3.13, Linux and macOS.

## Roadmap

Things that would make sense if this gets traction:

- **Full site crawling** — follow links, respect sitemaps, return a structured set of pages instead of just one. Right now StealthFetch is single-page-in, markdown-out — it was built with AI coding agents in mind, where one page at a time is usually what you need.
- **Homebrew tap** — `brew install stealthfetch` for people who don't want to think about Python
- **Docker image** — bundle browser backends pre-installed, no `camoufox fetch` step, plays well with [Docker's MCP Catalog](https://docs.docker.com/ai/mcp-catalog-and-toolkit/)

Contributions welcome.

## License

AGPL-3.0 — free to use, modify, and distribute. If you run it as a service, you must open-source your stack. Commercial licenses available for organizations that need a different arrangement.
