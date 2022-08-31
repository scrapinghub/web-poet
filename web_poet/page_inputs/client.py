import asyncio
import logging
from http import HTTPStatus
from typing import Callable, Dict, List, Optional, Union

from web_poet.exceptions import HttpResponseError
from web_poet.page_inputs.http import (
    HttpRequest,
    HttpRequestBody,
    HttpRequestHeaders,
    HttpResponse,
)
from web_poet.page_inputs.url import _Url
from web_poet.requests import _perform_request
from web_poet.utils import as_list

logger = logging.getLogger(__name__)

_StrMapping = Dict[str, str]
_Headers = Union[_StrMapping, HttpRequestHeaders]
_Body = Union[bytes, HttpRequestBody]
_StatusList = Union[str, int, List[Union[str, int]]]


class HttpClient:
    """Async HTTP client to be used in Page Objects.

    See :ref:`advanced-requests` for the usage information.

    HttpClient doesn't make HTTP requests on itself. It uses either the
    request function assigned to the ``web_poet.request_downloader_var``
    :mod:`contextvar <contextvars>`, or a function passed via
    ``request_downloader`` argument of the :meth:`~.HttpClient.__init__` method.

    Either way, this function should be an ``async def`` function which
    receives an  :class:`~.HttpRequest` instance, and either returns a
    :class:`~.HttpResponse` instance, or raises a subclass of
    :class:`~.HttpError`. You can read more in the
    :ref:`advanced-downloader-impl` documentation.
    """

    def __init__(self, request_downloader: Callable = None):
        self._request_downloader = request_downloader or _perform_request

    @staticmethod
    def _handle_status(
        response: HttpResponse,
        request: HttpRequest,
        *,
        allow_status: _StatusList = None,
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
        allow_status: _StatusList = None,
    ) -> HttpResponse:
        """This is a shortcut for creating an :class:`~.HttpRequest` instance and
        executing that request.

        :class:`~.HttpRequestError` is raised for
        *connection errors*, *connection and read timeouts*, etc.

        An :class:`~.HttpResponse` instance is returned for successful
        responses in the ``100-3xx`` status code range.

        Otherwise, an exception of type :class:`~.HttpResponseError` is raised.

        Rasing :class:`~.HttpResponseError` can be suppressed for certain
        status codes using the ``allow_status`` param - it is
        a list of status code values for which :class:`~.HttpResponse`
        should be returned instead of raising :class:`~.HttpResponseError`.

        There is a special "*" ``allow_status`` value which allows
        any status code.

        There is no need to include ``100-3xx`` status codes in ``allow_status``,
        because :class:`~.HttpResponseError` is not raised for them.
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
        allow_status: _StatusList = None,
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
        allow_status: _StatusList = None,
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
        self, request: HttpRequest, *, allow_status: _StatusList = None
    ) -> HttpResponse:
        """Execute the specified :class:`~.HttpRequest` instance using the
        request implementation configured in the :class:`~.HttpClient`
        instance.

        :class:`~.HttpRequestError` is raised for
        *connection errors*, *connection and read timeouts*, etc.

        :class:`~.HttpResponse` instance is returned for successful
        responses in the ``100-3xx`` status code range.

        Otherwise, an exception of type :class:`~.HttpResponseError` is raised.

        Rasing :class:`~.HttpResponseError` can be suppressed for certain
        status codes using the ``allow_status`` param - it is
        a list of status code values for which :class:`~.HttpResponse`
        should be returned instead of raising :class:`~.HttpResponseError`.

        There is a special "*" ``allow_status`` value which allows
        any status code.

        There is no need to include ``100-3xx`` status codes in ``allow_status``,
        because :class:`~.HttpResponseError` is not raised for them.
        """
        response = await self._request_downloader(request)
        self._handle_status(response, request, allow_status=allow_status)
        return response

    async def batch_execute(
        self,
        *requests: HttpRequest,
        return_exceptions: bool = False,
        allow_status: _StatusList = None,
    ) -> List[Union[HttpResponse, HttpResponseError]]:
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

        Like :meth:`~.HttpClient.execute`, :class:`~.HttpResponseError`
        will be raised for responses with status codes in the ``400-5xx`` range.
        The ``allow_status`` parameter could be used the same way here to prevent
        these exceptions from being raised.

        You can omit ``allow_status="*"`` if you're passing ``return_exceptions=True``.
        However, it would be returning :class:`~.HttpResponseError`
        instead of :class:`~.HttpResponse`.

        Lastly, a :class:`~.HttpRequestError` may be raised
        on cases like *connection errors*, *connection and read timeouts*, etc.
        """

        coroutines = [self.execute(r, allow_status=allow_status) for r in requests]
        responses = await asyncio.gather(
            *coroutines, return_exceptions=return_exceptions
        )
        return responses
