"""
Core Exceptions
~~~~~~~~~~~~~~~

These exceptions are tied to how **web-poet** operates.
"""


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
