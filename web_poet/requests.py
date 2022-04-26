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
from typing import Optional, List, Callable, Union, Dict

import attrs

from web_poet.page_inputs import (
    HttpResponse,
    HttpRequest,
    HttpRequestHeaders,
    HttpRequestBody,
)
from web_poet.exceptions import RequestBackendError, HttpRequestError
from web_poet.utils import as_list

logger = logging.getLogger(__name__)

_StrMapping = Dict[str, str]
_Headers = Union[_StrMapping, HttpRequestHeaders]
_Body = Union[bytes, HttpRequestBody]
_Status = Union[str, int]


# Frameworks that wants to support additional requests in ``web-poet`` should
# set the appropriate implementation for requesting data.
request_backend_var: ContextVar = ContextVar("request_backend")


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
        self._request_downloader = request_downloader or _perform_request

    @staticmethod
    def _handle_status(
        response: HttpResponse,
        *,
        allow_status: List[_Status] = None,
    ) -> None:
        allow_status_normalized = list(map(str, as_list(allow_status)))
        allow_all_status = any(
            [True for s in allow_status_normalized if "*" == s.strip()]
        )

        if (
            allow_all_status
            or response.status is None  # allows serialized responses from tests
            or response.status < 400
            or str(response.status) in allow_status_normalized
        ):
            return

        if 400 <= response.status < 500:
            kind = "Client"
        elif 500 <= response.status < 600:
            kind = "Server"

        msg = f"{response.status} {kind} Error for {response.url}"
        raise HttpRequestError(msg)

    async def request(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: Optional[_Headers] = None,
        body: Optional[_Body] = None,
        allow_status: List[_Status] = None,
    ) -> HttpResponse:
        """This is a shortcut for creating a :class:`~.HttpRequest` instance and
        executing that request.

        A :class:`~.HttpResponse` instance should then be returned for successful
        responses in the 100-3xx status code range. Otherwise, an exception of
        type :class:`web_poet.exceptions.http.HttpRequestError` will be raised.

        This behavior can be changed by suppressing the exceptions on select
        status codes using the ``allow_status`` param:

            * Passing status code values would not raise the exception when it
              occurs. This would return the response as-is.
            * Passing a "*" value would basically allow any status codes.

        .. warning::
            By convention, the request implementation supplied optionally to
            :class:`~.HttpClient` should return a :class:`~.HttpResponse` instance.
            However, the underlying implementation supplied might change that,
            depending on how the framework using **web-poet** implements it.
        """
        headers = headers or {}
        body = body or b""
        req = HttpRequest(url=url, method=method, headers=headers, body=body)

        response = await self.execute(req)
        self._handle_status(response, allow_status=allow_status)

        return response

    async def get(
        self,
        url: str,
        *,
        headers: Optional[_Headers] = None,
        allow_status: List[_Status] = None,
    ) -> HttpResponse:
        """Similar to :meth:`~.HttpClient.request` but peforming a ``GET``
        request.
        """
        return await self.request(
            url=url,
            method="GET",
            headers=headers,
            allow_status=allow_status,
        )

    async def post(
        self,
        url: str,
        *,
        headers: Optional[_Headers] = None,
        body: Optional[_Body] = None,
        allow_status: List[_Status] = None,
    ) -> HttpResponse:
        """Similar to :meth:`~.HttpClient.request` but performing a ``POST``
        request.
        """
        return await self.request(
            url=url,
            method="POST",
            headers=headers,
            body=body,
            allow_status=allow_status,
        )

    async def execute(self, request: HttpRequest) -> HttpResponse:
        """Accepts a single instance of :class:`~.HttpRequest` and executes it
        using the request implementation configured in the :class:`~.HttpClient`
        instance.

        This returns a single :class:`~.HttpResponse`.
        """
        return await self._request_downloader(request)

    async def batch_execute(
        self, *requests: HttpRequest, return_exceptions: bool = False
    ) -> List[Union[HttpResponse, Exception]]:
        """Similar to :meth:`~.HttpClient.execute` but accepts a collection of
        :class:`~.HttpRequest` instances that would be batch executed.

        The order of the :class:`~.HttpResponses` would correspond to the order
        of :class:`~.HttpRequest` passed.

        If any of the :class:`~.HttpRequest` raises an exception upon execution,
        the exception is raised.

        To prevent this, the actual exception can be returned alongside any
        successful :class:`~.HttpResponse`. This enables salvaging any usable
        responses despite any possible failures. This can be done by setting
        ``True`` to the ``return_exceptions`` parameter.
        """

        coroutines = [self._request_downloader(r) for r in requests]
        responses = await asyncio.gather(
            *coroutines, return_exceptions=return_exceptions
        )
        return responses
