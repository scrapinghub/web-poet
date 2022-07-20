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

    pass


class Retry(ValueError):
    """The page object found that the input data is partial or empty, and a
    request retry may provide better input.

    See :ref:`retries`.
    """

    pass
