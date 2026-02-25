"""StealthFetch MCP server — exposes fetch_markdown as an MCP tool."""

from __future__ import annotations

import json


def main() -> None:
    """MCP server entry point."""
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP(
        "stealthfetch",
        instructions=(
            "Fetch any web page and return clean, LLM-ready markdown. "
            "Handles anti-bot protection (Cloudflare, DataDome, PerimeterX, Akamai) "
            "by auto-escalating from HTTP to a stealth browser. Built-in SSRF protection. "
            "Use for scraping websites, reading web pages, or fetching URLs that block "
            "normal HTTP requests."
        ),
    )

    @mcp.tool()  # type: ignore[untyped-decorator]
    async def fetch_markdown(
        url: str,
        method: str = "auto",
        browser_backend: str = "auto",
        include_links: bool = True,
        include_images: bool = False,
        include_tables: bool = True,
        timeout: int = 30,
        headers_json: str = "",
        proxy_server: str = "",
        proxy_username: str = "",
        proxy_password: str = "",
        include_metadata: bool = False,
    ) -> str:
        """Fetch a web page and return clean, LLM-ready markdown. Strips nav, ads, \
and boilerplate. Auto-escalates to a stealth browser if the site blocks normal \
HTTP requests (Cloudflare, DataDome, PerimeterX, Akamai). SSRF-safe.

        Args:
            url: The URL to fetch.
            method: "auto" (try HTTP, escalate to stealth browser on block),
                "http" (curl_cffi only), or "browser" (stealth browser — use for
                JS-heavy SPAs that render content client-side).
            browser_backend: "auto" (prefers camoufox), "camoufox" (stealth
                Firefox), or "patchright" (stealth Chromium).
            include_links: Preserve hyperlinks in output.
            include_images: Preserve image references in output.
            include_tables: Preserve tables in output.
            timeout: Request timeout in seconds.
            headers_json: Additional HTTP headers as JSON string, e.g. '{"Cookie": "x=1"}'.
            proxy_server: Proxy server URL, e.g. "http://proxy:8080".
            proxy_username: Proxy username (optional).
            proxy_password: Proxy password (optional).
            include_metadata: When True, returns JSON with markdown + page
                metadata (title, author, date, description, url, hostname,
                sitename). When False (default), returns plain markdown.

        Returns:
            Plain markdown string, or JSON with markdown + metadata when
            include_metadata is True.
        """
        headers: dict[str, str] | None = None
        if headers_json:
            parsed_headers = json.loads(headers_json)
            if not isinstance(parsed_headers, dict) or not all(
                isinstance(k, str) and isinstance(v, str)
                for k, v in parsed_headers.items()
            ):
                raise ValueError(
                    "headers_json must be a JSON object with string keys and values"
                )
            headers = parsed_headers

        proxy: dict[str, str] | None = None
        if proxy_server:
            proxy = {"server": proxy_server}
            if proxy_username:
                proxy["username"] = proxy_username
            if proxy_password:
                proxy["password"] = proxy_password

        kwargs: dict[str, object] = {
            "method": method,
            "browser_backend": browser_backend,
            "include_links": include_links,
            "include_images": include_images,
            "include_tables": include_tables,
            "timeout": timeout,
            "headers": headers,
            "proxy": proxy,
        }

        if include_metadata:
            import dataclasses

            from stealthfetch._core import afetch_result

            result = await afetch_result(url, **kwargs)  # type: ignore[arg-type]
            return json.dumps(dataclasses.asdict(result))

        from stealthfetch._core import afetch_markdown

        return await afetch_markdown(url, **kwargs)  # type: ignore[arg-type]

    mcp.run()


if __name__ == "__main__":
    main()
