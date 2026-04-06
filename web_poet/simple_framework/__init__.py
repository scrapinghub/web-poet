"""Simple, built-in :ref:`web-poet framework <frameworks>` for simple use
cases."""

try:
    import niquests  # noqa: F401
    from playwright.async_api import async_playwright  # noqa: F401
except ImportError:
    message = (
        "Could not import web_poet.simple_framework dependencies. "
        "Install `web-poet[simple_framework]`."
    )
    raise ImportError(message) from None

from ._api import browser, get_item, get_page

__all__ = [
    "browser",
    "get_item",
    "get_page",
]
