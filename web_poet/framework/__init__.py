"""Built-in :ref:`web-poet framework <frameworks>` for simple use cases."""

try:
    import niquests  # noqa: F401
    from playwright.async_api import async_playwright  # noqa: F401
except ImportError as exception:
    message = (
        "Could not import web_poet.framework dependencies. Install web-poet[framework]."
    )
    raise ImportError(message) from exception

from ._api import Framework, playwright_engine

__all__ = [
    "Framework",
    "playwright_engine",
]
