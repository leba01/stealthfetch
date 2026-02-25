"""StealthFetch MCP server — exposes fetch_markdown as an MCP tool."""

from __future__ import annotations

import json


def main() -> None:
    """MCP server entry point."""
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP(
        "stealthfetch",
        instructions="Fetch any URL and return LLM-ready markdown.",
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
    ) -> str:
        """Fetch a URL and return clean, LLM-ready markdown.

        Args:
            url: The URL to fetch.
            method: "auto" (try HTTP, escalate to browser), "http", or "browser".
            browser_backend: "auto", "camoufox", or "patchright".
            include_links: Preserve hyperlinks in output.
            include_images: Preserve image references in output.
            include_tables: Preserve tables in output.
            timeout: Request timeout in seconds.
            headers_json: Additional HTTP headers as a JSON string (e.g. '{"Cookie": "x=1"}').
            proxy_server: Proxy server URL (e.g. "http://proxy:8080").
            proxy_username: Proxy username (optional).
            proxy_password: Proxy password (optional).

        Returns:
            Clean markdown string of the page's main content.
        """
        from stealthfetch._core import afetch_markdown

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

        return await afetch_markdown(
            url,
            method=method,
            browser_backend=browser_backend,
            include_links=include_links,
            include_images=include_images,
            include_tables=include_tables,
            timeout=timeout,
            headers=headers,
            proxy=proxy,
        )

    mcp.run()


if __name__ == "__main__":
    main()
