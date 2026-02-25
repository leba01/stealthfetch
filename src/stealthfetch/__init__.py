"""StealthFetch — URL in, LLM-ready markdown out."""

from importlib.metadata import version

from stealthfetch._core import (
    FetchResult,
    afetch_markdown,
    afetch_result,
    fetch_markdown,
    fetch_result,
)
from stealthfetch._errors import (
    BrowserNotAvailable,
    ExtractionError,
    FetchError,
    StealthFetchError,
)

__version__ = version("stealthfetch")

__all__ = [
    "BrowserNotAvailable",
    "ExtractionError",
    "FetchError",
    "FetchResult",
    "StealthFetchError",
    "__version__",
    "afetch_markdown",
    "afetch_result",
    "fetch_markdown",
    "fetch_result",
]
