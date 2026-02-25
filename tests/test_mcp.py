"""Tests for the MCP server — parameter parsing and tool forwarding."""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _get_mcp_tool() -> Any:
    """Run mcp_server.main() with a fake FastMCP to capture the registered tool function."""
    captured: dict[str, Any] = {}

    class FakeFastMCP:
        def __init__(self, name: str, **kwargs: Any) -> None:
            pass

        def tool(self) -> Any:
            def decorator(fn: Any) -> Any:
                captured["fn"] = fn
                return fn

            return decorator

        def run(self) -> None:
            pass

    fake_fastmcp_mod = MagicMock()
    fake_fastmcp_mod.FastMCP = FakeFastMCP

    with patch.dict(
        sys.modules,
        {
            "mcp": MagicMock(),
            "mcp.server": MagicMock(),
            "mcp.server.fastmcp": fake_fastmcp_mod,
        },
    ):
        from stealthfetch import mcp_server

        mcp_server.main()

    return captured["fn"]


_MCP_TOOL: Any = _get_mcp_tool()


@pytest.mark.asyncio
class TestMCPToolForwarding:
    """The MCP tool should forward all parameters correctly to afetch_markdown."""

    @patch("stealthfetch._core.afetch_markdown", new_callable=AsyncMock)
    async def test_url_forwarded(self, mock_afetch: AsyncMock) -> None:
        mock_afetch.return_value = "# Title"
        result = await _MCP_TOOL("https://example.com")
        assert result == "# Title"
        assert mock_afetch.call_args.args[0] == "https://example.com"

    @patch("stealthfetch._core.afetch_markdown", new_callable=AsyncMock)
    async def test_all_params_forwarded(self, mock_afetch: AsyncMock) -> None:
        mock_afetch.return_value = "ok"
        await _MCP_TOOL(
            "https://example.com",
            method="http",
            browser_backend="camoufox",
            include_links=False,
            include_images=True,
            include_tables=False,
            timeout=60,
        )
        kw = mock_afetch.call_args.kwargs
        assert kw["method"] == "http"
        assert kw["browser_backend"] == "camoufox"
        assert kw["include_links"] is False
        assert kw["include_images"] is True
        assert kw["include_tables"] is False
        assert kw["timeout"] == 60


@pytest.mark.asyncio
class TestMCPHeadersParsing:
    """headers_json string should be parsed into a dict."""

    @patch("stealthfetch._core.afetch_markdown", new_callable=AsyncMock)
    async def test_headers_json_parsed(self, mock_afetch: AsyncMock) -> None:
        mock_afetch.return_value = "ok"
        await _MCP_TOOL(
            "https://example.com",
            headers_json='{"Cookie": "x=1", "Accept": "text/html"}',
        )
        assert mock_afetch.call_args.kwargs["headers"] == {
            "Cookie": "x=1",
            "Accept": "text/html",
        }

    @patch("stealthfetch._core.afetch_markdown", new_callable=AsyncMock)
    async def test_empty_headers_json_passes_none(self, mock_afetch: AsyncMock) -> None:
        mock_afetch.return_value = "ok"
        await _MCP_TOOL("https://example.com", headers_json="")
        assert mock_afetch.call_args.kwargs["headers"] is None

    async def test_invalid_headers_json_raises(self) -> None:
        with pytest.raises(Exception):
            await _MCP_TOOL("https://example.com", headers_json="not-json")

    async def test_headers_json_list_raises(self) -> None:
        with pytest.raises(ValueError, match="JSON object"):
            await _MCP_TOOL("https://example.com", headers_json='["a", "b"]')

    async def test_headers_json_non_string_values_raise(self) -> None:
        with pytest.raises(ValueError, match="JSON object"):
            await _MCP_TOOL("https://example.com", headers_json='{"X-Count": 42}')


@pytest.mark.asyncio
class TestMCPProxyAssembly:
    """Flat proxy_server/username/password params should be assembled into a proxy dict."""

    @patch("stealthfetch._core.afetch_markdown", new_callable=AsyncMock)
    async def test_proxy_with_credentials(self, mock_afetch: AsyncMock) -> None:
        mock_afetch.return_value = "ok"
        await _MCP_TOOL(
            "https://example.com",
            proxy_server="http://proxy:8080",
            proxy_username="user",
            proxy_password="pass",
        )
        assert mock_afetch.call_args.kwargs["proxy"] == {
            "server": "http://proxy:8080",
            "username": "user",
            "password": "pass",
        }

    @patch("stealthfetch._core.afetch_markdown", new_callable=AsyncMock)
    async def test_proxy_server_only(self, mock_afetch: AsyncMock) -> None:
        mock_afetch.return_value = "ok"
        await _MCP_TOOL("https://example.com", proxy_server="http://proxy:8080")
        proxy = mock_afetch.call_args.kwargs["proxy"]
        assert proxy == {"server": "http://proxy:8080"}
        assert "username" not in proxy
        assert "password" not in proxy

    @patch("stealthfetch._core.afetch_markdown", new_callable=AsyncMock)
    async def test_no_proxy_passes_none(self, mock_afetch: AsyncMock) -> None:
        mock_afetch.return_value = "ok"
        await _MCP_TOOL("https://example.com")
        assert mock_afetch.call_args.kwargs["proxy"] is None
