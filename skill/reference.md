# API Reference

## Contents
- Functions: fetch_markdown, afetch_markdown, fetch_result, afetch_result
- FetchResult dataclass
- Exception hierarchy
- MCP tool interface
- Install extras

## Functions

All four functions share the same parameters:

```python
def fetch_markdown(
    url: str,
    *,
    method: str = "auto",           # "auto" | "http" | "browser"
    browser_backend: str = "auto",  # "auto" | "camoufox" | "patchright"
    include_links: bool = True,
    include_images: bool = False,
    include_tables: bool = True,
    timeout: int = 30,
    proxy: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> str: ...

def fetch_result(...same params...) -> FetchResult: ...

# Async variants — identical signatures
async def afetch_markdown(...) -> str: ...
async def afetch_result(...) -> FetchResult: ...
```

### Parameter details

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | URL to fetch. SSRF-validated (rejects private/loopback IPs). |
| `method` | `str` | `"auto"`: HTTP first, escalate to browser on block. `"http"`: curl_cffi only. `"browser"`: stealth browser only. |
| `browser_backend` | `str` | `"auto"`: prefers camoufox. `"camoufox"`: stealth Firefox. `"patchright"`: stealth Chromium. |
| `include_links` | `bool` | Preserve hyperlinks in markdown output. |
| `include_images` | `bool` | Preserve image references in markdown output. |
| `include_tables` | `bool` | Preserve tables in markdown output. |
| `timeout` | `int` | Request timeout in seconds. |
| `proxy` | `dict \| None` | `{"server": "http://proxy:8080", "username": "u", "password": "p"}`. Username/password optional. |
| `headers` | `dict \| None` | Additional HTTP headers merged with impersonation defaults. |

## FetchResult

```python
@dataclass
class FetchResult:
    markdown: str           # Cleaned markdown content
    title: str | None       # Page title
    author: str | None      # Author name
    date: str | None        # Publication date (ISO 8601 when available)
    description: str | None # Meta description
    url: str | None         # Canonical URL (may differ from input)
    hostname: str | None    # Hostname
    sitename: str | None    # Publisher name
```

Convert to dict: `dataclasses.asdict(result)`.

## Exceptions

All inherit from `StealthFetchError`:

| Exception | When raised |
|-----------|-------------|
| `FetchError` | Network failure, HTTP error, blocked with no browser available |
| `ExtractionError` | Page fetched but trafilatura found no main content |
| `BrowserNotAvailable` | Browser mode needed but camoufox/patchright not installed |

## MCP tool interface

The MCP server exposes a single `fetch_markdown` tool. Parameters differ slightly from the Python API for MCP compatibility:

| MCP parameter | Maps to |
|---------------|---------|
| `headers_json` | `headers` — pass as JSON string: `'{"Cookie": "x=1"}'` |
| `proxy_server` | `proxy["server"]` |
| `proxy_username` | `proxy["username"]` |
| `proxy_password` | `proxy["password"]` |
| `include_metadata` | When `True`, returns JSON with markdown + metadata (uses `fetch_result` internally) |

## Install extras

| Extra | What it adds |
|-------|-------------|
| `stealthfetch[camoufox]` | Camoufox stealth Firefox |
| `stealthfetch[patchright]` | Patchright stealth Chromium |
| `stealthfetch[browser]` | Both browser backends |
| `stealthfetch[mcp]` | MCP server (mcp>=1.26.0) |
