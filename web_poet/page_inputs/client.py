"""This module has a full support for :mod:`asyncio` that enables developers to
perform asynchronous additional requests inside of Page Objects.

Note that the implementation to fully execute any :class:`~.Request` is not
handled in this module. With that, the framework using **web-poet** must supply
the implementation.

You can read more about this in the :ref:`advanced-downloader-impl` documentation.
"""

import asyncio
import logging
from typing import Optional, Dict, List, Union, Callable
from http import HTTPStatus

from web_poet.requests import request_backend_var, _perform_request
from web_poet.page_inputs.http import (
    HttpRequest,
    HttpRequestHeaders,
    HttpRequestBody,
    HttpResponse,
)
from web_poet.exceptions import RequestBackendError, HttpResponseError
from web_poet.utils import as_list
from web_poet._base import _Url

logger = logging.getLogger(__name__)

_StrMapping = Dict[str, str]
_Headers = Union[_StrMapping, HttpRequestHeaders]
_Body = Union[bytes, HttpRequestBody]
_Status = Union[str, int]


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
        request: HttpRequest,
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

        status = HTTPStatus(response.status)
        msg = f"{response.status} {status.name} response for {response.url}"
        raise HttpResponseError(msg, request=request, response=response)

    async def request(
        self,
        url: Union[str, _Url],
        *,
        method: str = "GET",
        headers: Optional[_Headers] = None,
        body: Optional[_Body] = None,
        allow_status: List[_Status] = None,
    ) -> HttpResponse:
        """This is a shortcut for creating a :class:`~.HttpRequest` instance and
        executing that request.

        A :class:`web_poet.exceptions.http.HttpRequestError` will be raised on
        cases like *connection errors*, *connection and read timeouts*, etc.

        A :class:`~.HttpResponse` instance should then be returned for successful
        responses in the 100-3xx status code range. Otherwise, an exception of
        type :class:`web_poet.exceptions.http.HttpResponseError` will be raised.

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
        response = await self.execute(req, allow_status=allow_status)
        return response

    async def get(
        self,
        url: Union[str, _Url],
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
        url: Union[str, _Url],
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

    async def execute(
        self, request: HttpRequest, *, allow_status: List[_Status] = None
    ) -> HttpResponse:
        """Accepts a single instance of :class:`~.HttpRequest` and executes it
        using the request implementation configured in the :class:`~.HttpClient`
        instance.

        A :class:`web_poet.exceptions.http.HttpRequestError` will be raised on
        cases like *connection errors*, *connection and read timeouts*, etc.

        A :class:`~.HttpResponse` instance should then be returned for successful
        responses in the 100-3xx status code range. Otherwise, an exception of
        type :class:`web_poet.exceptions.http.HttpResponseError` will be raised.

        This behavior can be changed by suppressing the exceptions on select
        status codes using the ``allow_status`` param:

            * Passing status code values would not raise the exception when it
              occurs. This would return the response as-is.
            * Passing a "*" value would basically allow any status codes.
        """
        response = await self._request_downloader(request)
        self._handle_status(response, request, allow_status=allow_status)
        return response

    async def batch_execute(
        self,
        *requests: HttpRequest,
        return_exceptions: bool = False,
        allow_status: List[_Status] = None,
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

        Like :meth:`~.HttpClient.execute`, :class:`web_poet.exceptions.http.HttpResponseError`
        will be raised for responses with status codes in the ``400-5xx`` range.
        The ``allow_status`` parameter could be used the same way here to prevent
        these exceptions from being raised.

        You can omit ``allow_status="*"`` if you're passing ``return_exceptions=True``.
        However, it would be returning :class:`web_poet.exceptions.http.HttpResponseError`
        instead of :class:`~.HttpResponse`.

        Lastly, a :class:`web_poet.exceptions.http.HttpRequestError` may be raised
        on cases like *connection errors*, *connection and read timeouts*, etc.
        """

        coroutines = [self.execute(r, allow_status=allow_status) for r in requests]
        responses = await asyncio.gather(
            *coroutines, return_exceptions=return_exceptions
        )
        return responses
