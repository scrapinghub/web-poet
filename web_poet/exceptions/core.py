"""
Core Exceptions
~~~~~~~~~~~~~~~

These exceptions are tied to how **web-poet** operates.
"""


class InvalidInput(ValueError):
    """The page object found that the input data is not valid for this page
    object, and a request retry is unlikely to make a difference.

    A common scenario is that where the input data does not match the type of
    item that the page object returns. For example, a scenario where a product
    page object gets a product list page as input, instead of a product details
    page.
    """

    pass


class RequestDownloaderVarError(Exception):
    """The ``web_poet.request_downloader_var`` had its contents accessed but there
    wasn't any value set during the time requests are executed.

    See the documentation section about :ref:`setting up the contextvars <setup-contextvars>`
    to learn more about this.
    """

    pass


class Retry(ValueError):
    """The page object found that the input data is partial or empty, and a
    request retry may provide better input.

    See :ref:`retries`.
    """

    pass
