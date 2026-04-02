"""Simple, built-in :ref:`web-poet framework <frameworks>` for simple use
cases."""

try:
    import niquests  # noqa: F401
except ImportError:
    message = "Could not import nirequests. Install `web-poet[simple_framework]`."
    raise ImportError(message) from None

from ._api import (
    get_item,
)

__all__ = [
    "get_item",
]
