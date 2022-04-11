"""This module has a full support for :mod:`asyncio` that enables developers to
perform asynchronous additional requests inside of Page Objects.

Note that the implementation to fully execute any :class:`~.Request` is not
handled in this module. With that, the framework using **web-poet** must supply
the implementation.

You can read more about this in the :ref:`advanced-downloader-impl` documentation.
"""

import asyncio
import logging
from contextvars import ContextVar
from typing import Optional, List, Dict, Union, Callable, AnyStr

import attrs

from web_poet._base import _HttpHeaders, _HttpBody
from web_poet.page_inputs import HttpResponse
from web_poet.exceptions import RequestBackendError

logger = logging.getLogger(__name__)


# Frameworks that wants to support additional requests in ``web-poet`` should
# set the appropriate implementation for requesting data.
request_backend_var: ContextVar = ContextVar("request_backend")


class HttpRequestBody(_HttpBody):
    """A container for holding the raw HTTP request body in bytes format."""

    pass


class HttpRequestHeaders(_HttpHeaders):
    """A container for holding the HTTP request headers.

    It's able to accept instantiation via an Iterable of Tuples:

    >>> pairs = [("Content-Encoding", "gzip"), ("content-length", "648")]
    >>> HttpRequestHeaders(pairs)
    <HttpRequestHeaders('Content-Encoding': 'gzip', 'content-length': '648')>

    It's also accepts a mapping of key-value pairs as well:

    >>> pairs = {"Content-Encoding": "gzip", "content-length": "648"}
    >>> headers = HttpRequestHeaders(pairs)
    >>> headers
    <HttpRequestHeaders('Content-Encoding': 'gzip', 'content-length': '648')>

    Note that this also supports case insensitive header-key lookups:

    >>> headers.get("content-encoding")
    'gzip'
    >>> headers.get("Content-Length")
    '648'

    These are just a few of the functionalities it inherits from
    :class:`multidict.CIMultiDict`. For more info on its other features, read
    the API spec of :class:`multidict.CIMultiDict`.
    """

    pass


Mapping = Dict[str, str]
Headers = Union[Mapping, HttpRequestHeaders]
Body = Union[bytes, HttpRequestBody]


@attrs.define(auto_attribs=False, slots=False, eq=False)
class HttpRequest:
    """Represents a generic HTTP request used by other functionalities in
    **web-poet** like :class:`~.HttpClient`.
    """

    url: str = attrs.field()
    method: str = attrs.field(default="GET")
    headers: HttpRequestHeaders = attrs.field(
        factory=HttpRequestHeaders, converter=HttpRequestHeaders
    )
    body: HttpRequestBody = attrs.field(
        factory=HttpRequestBody, converter=HttpRequestBody
    )


async def _perform_request(request: HttpRequest) -> HttpResponse:
    """Given a :class:`~.Request`, execute it using the **request implementation**
    that was set in the ``web_poet.request_backend_var`` :mod:`contextvars`
    instance.

    .. warning::
        By convention, this function should return a :class:`~.HttpResponse`.
        However, the underlying downloader assigned in
        ``web_poet.request_backend_var`` might change that, depending on
        how the framework using **web-poet** implements it.
    """

    logger.info(f"Requesting page: {request}")

    try:
        request_backend = request_backend_var.get()
    except LookupError:
        raise RequestBackendError(
            "Additional requests are used inside the Page Object but the "
            "current framework has not set any HttpRequest Backend via "
            "'web_poet.request_backend_var'"
        )

    response_data: HttpResponse = await request_backend(request)
    return response_data


class HttpClient:
    """A convenient client to easily execute requests.

    By default, it uses the request implementation assigned in the
    ``web_poet.request_backend_var`` which is a :mod:`contextvars` instance to
    download the actual requests. However, it can easily be overridable by
    providing an optional ``request_downloader`` callable.

    Providing the request implementation by dependency injection would be a good
    alternative solution when you want to avoid setting up :mod:`contextvars`
    like ``web_poet.request_backend_var``.

    In any case, this doesn't contain any implementation about how to execute
    any requests fed into it. When setting that up, make sure that the downloader
    implementation returns a :class:`~.HttpResponse` instance.
    """

    def __init__(self, request_downloader: Callable = None):
        self.request_downloader = request_downloader or _perform_request

    async def request(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: Optional[Headers] = None,
        body: Optional[Body] = None,
    ) -> HttpResponse:
        """This is a shortcut for creating a :class:`HttpRequest` instance and executing
        that request.

        A :class:`~.HttpResponse` instance should then be returned.

        .. warning::
            By convention, the request implementation supplied optionally to
            :class:`~.HttpClient` should return a :class:`~.HttpResponse` instance.
            However, the underlying implementation supplied might change that,
            depending on how the framework using **web-poet** implements it.
        """
        req = HttpRequest(url, method, headers or {}, body or b"")
        return await self.request_downloader(req)

    async def get(self, url: str, *, headers: Optional[Headers] = None) -> HttpResponse:
        """Similar to :meth:`~.HttpClient.request` but peforming a ``GET``
        request.
        """
        return await self.request(url=url, method="GET", headers=headers)

    async def post(
        self,
        url: str,
        *,
        headers: Optional[Headers] = None,
        body: Optional[Body] = None,
    ) -> HttpResponse:
        """Similar to :meth:`~.HttpClient.request` but performing a ``POST``
        request.
        """
        return await self.request(url=url, method="POST", headers=headers, body=body)

    async def batch_requests(self, *requests: HttpRequest) -> List[HttpResponse]:
        """Similar to :meth:`~.HttpClient.request` but accepts a collection of
        :class:`~.HttpRequest` instances that would be batch executed.
        """

        coroutines = [self.request_downloader(r) for r in requests]
        responses = await asyncio.gather(*coroutines)
        return responses
