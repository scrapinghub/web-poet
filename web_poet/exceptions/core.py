"""
Core Exceptions
~~~~~~~~~~~~~~~

These exceptions are tied to how **web-poet** operates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from web_poet import HttpRequest


__all__ = [
    "NoSavedHttpResponse",
    "PageObjectAction",
    "RequestDownloaderVarError",
    "Retry",
    "UseFallback",
]


class RequestDownloaderVarError(Exception):
    """The ``web_poet.request_downloader_var`` had its contents accessed but there
    wasn't any value set during the time requests are executed.

    See the documentation section about :ref:`setting up the contextvars <setup-contextvars>`
    to learn more about this.
    """


class PageObjectAction(ValueError):
    """Base class for exceptions that can be raised from a page object to
    indicate something to be done about that page object."""


class Retry(PageObjectAction):
    """The page object found that the input data is partial or empty, and a
    request retry may provide better input."""


class UseFallback(PageObjectAction):
    """The page object cannot extract data from the input, but the input seems
    valid, so an alternative data extraction implementation for the same item
    type may succeed."""


class NoSavedHttpResponse(AssertionError):
    """Indicates that there is no saved response for this request.

    Can only be raised when a :class:`~.HttpClient` instance is used to
    get saved responses.

    :param request: The :class:`~.HttpRequest` instance that was used.
    :type request: HttpRequest
    """

    def __init__(self, msg: str | None = None, request: HttpRequest | None = None):
        self.request = request
        if msg is None:
            msg = f"There is no saved response available for this HTTP Request: {self.request}"
        super().__init__(msg)
