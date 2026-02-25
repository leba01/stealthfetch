"""StealthFetch — URL in, LLM-ready markdown out."""

from importlib.metadata import version

from stealthfetch._core import afetch_markdown, fetch_markdown
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
    "StealthFetchError",
    "__version__",
    "afetch_markdown",
    "fetch_markdown",
]
