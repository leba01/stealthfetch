# StealthFetch

URL in, LLM-ready markdown out. Orchestration layer over curl_cffi, trafilatura, html-to-markdown, Camoufox, and Patchright.

## Architecture

Three-layer pipeline in `src/stealthfetch/_core.py`: **fetch → extract → convert**.

- **Fetch** — HTTP via curl_cffi with Chrome TLS fingerprint. Auto-escalates to stealth browser on block detection.
- **Extract** — trafilatura strips nav, ads, boilerplate. Returns clean HTML.
- **Convert** — html-to-markdown (Rust) produces final markdown.

Key modules:
- `_core.py` — pipeline + public API (`fetch_markdown`, `afetch_markdown`, `fetch_result`, `afetch_result`, `FetchResult`)
- `_detect.py` — block detection heuristics. Strong patterns (vendor-specific, always checked) vs weak patterns (generic, checked only on small pages <15k chars)
- `_errors.py` — exception hierarchy + SSRF URL/proxy validation (pre- and post-redirect)
- `_compat.py` — feature detection for optional browser deps (non-cached, allows mid-process install)
- `_browsers/` — browser backend abstraction. Dispatcher resolves "auto" → camoufox (preferred) or patchright
- `cli.py` — CLI entry point
- `mcp_server.py` — MCP server entry point (FastMCP, single `fetch_markdown` tool)

## Public API

4 functions: `fetch_markdown`, `afetch_markdown`, `fetch_result`, `afetch_result`
1 dataclass: `FetchResult` (markdown, title, author, date, description, url, hostname, sitename)
3 exceptions: `FetchError`, `ExtractionError`, `BrowserNotAvailable` (all inherit `StealthFetchError`)

## Conventions

- Strict mypy (`--strict` equivalent via pyproject.toml)
- Ruff linting: E, F, W, I, UP, B, SIM, C4, RUF, PERF, LOG
- Lazy imports for optional deps (browser backends, mcp) — keep startup fast
- `_` prefix for all private modules
- Async variants use `a` prefix (`afetch_markdown`)
- CPU-bound work runs off the event loop via `asyncio.to_thread` in async paths

## Commands

```bash
pytest                       # unit tests (99 tests)
pytest --run-integration     # + live HTTP tests
ruff check src/ tests/       # lint
mypy src/                    # type check
```

## Design Decisions

- HTTP-first, browser-only-when-needed — browsers are slow and detectable
- Strong vs weak pattern split in `_detect.py` prevents false-positive escalation on large articles
- SSRF validated twice: before request (literal IP + DNS resolution) and after redirects
- `FetchResult` metadata comes free from trafilatura's existing parse — no extra HTTP calls
