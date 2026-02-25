"""Async usage of StealthFetch."""

import asyncio

from stealthfetch import afetch_markdown


async def main() -> None:
    # Fetch multiple URLs concurrently
    urls = [
        "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "https://en.wikipedia.org/wiki/Rust_(programming_language)",
    ]
    results = await asyncio.gather(*[afetch_markdown(url) for url in urls])

    for url, md in zip(urls, results):
        print(f"\n{'='*60}")
        print(f"URL: {url}")
        print(f"Length: {len(md)} chars")
        print(md[:200])


asyncio.run(main())
