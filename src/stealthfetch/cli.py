"""StealthFetch CLI — stealthfetch <url> [options]."""

from __future__ import annotations

import argparse
import sys
from urllib.parse import urlparse

from stealthfetch._errors import StealthFetchError


def _parse_proxy(proxy_url: str) -> dict[str, str]:
    """Parse a proxy URL into a dict with server, username, password."""
    parsed = urlparse(proxy_url)
    if not parsed.hostname or not parsed.scheme:
        raise ValueError(f"Invalid proxy URL: {proxy_url}")
    result: dict[str, str] = {
        "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
        if parsed.port
        else f"{parsed.scheme}://{parsed.hostname}",
    }
    if parsed.username:
        result["username"] = parsed.username
    if parsed.password:
        result["password"] = parsed.password
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stealthfetch",
        description="Fetch a URL and return clean, LLM-ready markdown.",
    )
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument(
        "-m",
        "--method",
        choices=["auto", "http", "browser"],
        default="auto",
        help="Fetch method (default: auto)",
    )
    parser.add_argument(
        "--backend",
        choices=["auto", "camoufox", "patchright"],
        default="auto",
        help="Browser backend (default: auto)",
    )
    parser.add_argument(
        "--no-links",
        action="store_true",
        help="Strip hyperlinks from output",
    )
    parser.add_argument(
        "--no-tables",
        action="store_true",
        help="Strip tables from output",
    )
    parser.add_argument(
        "--include-images",
        action="store_true",
        help="Include image references in output",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help="Proxy URL (e.g. http://user:pass@host:port)",
    )
    parser.add_argument(
        "--header",
        action="append",
        default=None,
        dest="headers",
        metavar="HEADER",
        help='HTTP header as "Name: value" (repeatable)',
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_get_version()}",
    )
    return parser


def _get_version() -> str:
    from stealthfetch import __version__

    return __version__


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    proxy: dict[str, str] | None = None
    if args.proxy:
        proxy = _parse_proxy(args.proxy)

    headers: dict[str, str] | None = None
    if args.headers:
        headers = {}
        for h in args.headers:
            if ":" not in h:
                print(f"Error: Invalid header (missing ':'): {h}", file=sys.stderr)
                sys.exit(1)
            name, value = h.split(":", 1)
            headers[name.strip()] = value.strip()

    try:
        from stealthfetch._core import fetch_markdown

        result = fetch_markdown(
            args.url,
            method=args.method,
            browser_backend=args.backend,
            include_links=not args.no_links,
            include_tables=not args.no_tables,
            include_images=args.include_images,
            timeout=args.timeout,
            proxy=proxy,
            headers=headers,
        )
        print(result)
    except (StealthFetchError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
