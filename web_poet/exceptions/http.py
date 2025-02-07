"""
HTTP Exceptions
~~~~~~~~~~~~~~~

These are exceptions pertaining to common issues faced when executing HTTP
operations.
"""

from __future__ import annotations

from web_poet.page_inputs.http import HttpRequest, HttpResponse


class HttpError(IOError):
    """Indicates that an exception has occurred when handling an HTTP operation.

    This is used as a **base class** for more specific errors and could be vague
    since it could denote problems either in the HTTP Request or Response.

    For more specific errors, it would be better to use :class:`.HttpRequestError`
    and :class:`.HttpResponseError`.

    :param request: Request that triggered the exception.
    :type request: HttpRequest
    """

    def __init__(self, msg: str | None = None, request: HttpRequest | None = None):
        #: Request that triggered the exception.
        self.request: HttpRequest | None = request
        if msg is None:
            msg = f"An Error ocurred when executing this HTTP Request: {self.request}"
        super().__init__(msg)


class HttpRequestError(HttpError):
    """Indicates that an exception has occurred when the **HTTP Request** was
    being handled.

    :param request: The :class:`~.HttpRequest` instance that was used.
    :type request: HttpRequest
    """

    pass


class HttpResponseError(HttpError):
    """Indicates that an exception has occurred when the **HTTP Response** was
    received.

    For responses that are in the status code ``100-3xx range``, this exception
    shouldn't be raised at all. However, for responses in the ``400-5xx``, this
    will be raised by **web-poet**.

    .. note::

        Frameworks implementing **web-poet** should **NOT** raise this  exception.

        This exception is raised by web-poet itself, based on ``allow_status``
        parameter found in the methods of :class:`~.HttpClient`.

    :param request: Request that got the response that triggered the exception.
    :type request: HttpRequest
    :param response: Response that triggered the exception.
    :type response: HttpResponse
    """

    def __init__(
        self,
        msg: str | None = None,
        response: HttpResponse | None = None,
        request: HttpRequest | None = None,
    ):
        #: Response that triggered the exception.
        self.response: HttpResponse | None = response
        if msg is None:
            msg = f"Unexpected HTTP Response received: {self.response}"
        super().__init__(msg, request=request)
