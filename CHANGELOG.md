# Changelog

## 0.2.0 (2026-02-24)

- Add `fetch_result()` / `afetch_result()` — same pipeline as `fetch_markdown`, returns `FetchResult` dataclass with `markdown` + metadata fields (`title`, `author`, `date`, `description`, `url`, `hostname`, `sitename`) extracted as a free side-effect of trafilatura parsing
- Add `FetchResult` dataclass, exported from the top-level package
- MCP server: add `include_metadata` parameter to `fetch_markdown` tool — when `True`, returns JSON with markdown and metadata instead of plain string

## 0.1.0 (2026-02-24)

Initial release.

- 3-layer pipeline: fetch (curl_cffi) → extract (trafilatura) → convert (html-to-markdown)
- Auto-escalation from HTTP to stealth browser on block detection
- Browser backends: Camoufox (default) and Patchright (fallback)
- Block detection: HTTP status codes, content-type awareness, pattern matching (Cloudflare, DataDome, PerimeterX, Akamai)
- SSRF protection: rejects private IPs, non-http(s) schemes, DNS rebinding, redirect-chain exploits
- CLI: `stealthfetch <url>` with proxy, timeout, headers, and output options
- MCP server: `stealthfetch-mcp` with full parameter support
- Async support: `afetch_markdown()`
- Proxy support with optional authentication
- Custom HTTP headers
- Response size limit (50 MB)
- Strict type hints (mypy strict) and full linting (ruff)
