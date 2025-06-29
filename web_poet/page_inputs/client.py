from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Union, cast

from web_poet.exceptions import HttpError, HttpResponseError
from web_poet.exceptions.core import NoSavedHttpResponse
from web_poet.page_inputs.http import (
    HttpRequest,
    HttpRequestBody,
    HttpRequestHeaders,
    HttpResponse,
    request_fingerprint,
)
from web_poet.requests import RequestDownloaderT, _perform_request
from web_poet.utils import as_list

if TYPE_CHECKING:
    from collections.abc import Iterable

from web_poet.page_inputs.url import _Url

logger = logging.getLogger(__name__)

_StrMapping = dict[str, str]
_Headers = Union[_StrMapping, HttpRequestHeaders]
_Body = Union[bytes, HttpRequestBody]
_StatusList = Union[str, int, list[Union[str, int]]]


@dataclass
class _SavedResponseData:
    """Class for storing a request and its result."""

    request: HttpRequest
    response: HttpResponse | None
    exception: HttpError | None = None

    def fingerprint(self) -> str:
        """Return the request fingeprint."""
        return request_fingerprint(self.request)


class HttpClient:
    """Async HTTP client to be used in Page Objects.

    See :ref:`additional-requests` for the usage information.

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

    def __init__(
        self,
        request_downloader: RequestDownloaderT | None = None,
        *,
        save_responses: bool = False,
        return_only_saved_responses: bool = False,
        responses: Iterable[_SavedResponseData] | None = None,
    ):
        self._request_downloader = request_downloader or _perform_request
        self.save_responses = save_responses
        self.return_only_saved_responses = return_only_saved_responses
        self._saved_responses: dict[str, _SavedResponseData] = {
            data.fingerprint(): data for data in responses or []
        }

    @staticmethod
    def _handle_status(
        response: HttpResponse,
        request: HttpRequest,
        *,
        allow_status: _StatusList | None = None,
    ) -> None:
        allow_status_normalized = list(map(str, as_list(allow_status)))
        allow_all_status = any(
            True for s in allow_status_normalized if s.strip() == "*"
        )

        if (
            allow_all_status
            or response.status is None  # allows serialized responses from tests
            or response.status < 400
            or str(response.status) in allow_status_normalized
        ):
            return

        status_name = _http_status_name(response.status)
        msg = f"{response.status} {status_name} response for {response.url}"
        raise HttpResponseError(msg, request=request, response=response)

    async def request(
        self,
        url: str | _Url,
        *,
        method: str = "GET",
        headers: _Headers | None = None,
        body: _Body | None = None,
        allow_status: _StatusList | None = None,
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
        return await self.execute(req, allow_status=allow_status)

    async def get(
        self,
        url: str | _Url,
        *,
        headers: _Headers | None = None,
        allow_status: _StatusList | None = None,
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
        url: str | _Url,
        *,
        headers: _Headers | None = None,
        body: _Body | None = None,
        allow_status: _StatusList | None = None,
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
        self, request: HttpRequest, *, allow_status: _StatusList | None = None
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
        if self.return_only_saved_responses:
            for fp, saved_data in self._saved_responses.items():
                if request_fingerprint(request) == fp:
                    if saved_data.exception:
                        raise saved_data.exception
                    assert saved_data.response
                    self._handle_status(
                        saved_data.response,
                        saved_data.request,
                        allow_status=allow_status,
                    )
                    return saved_data.response
            raise NoSavedHttpResponse(request=request)

        try:
            response = await self._request_downloader(request)
        except HttpError as ex:
            if self.save_responses:
                self._saved_responses[request_fingerprint(request)] = (
                    _SavedResponseData(request, None, ex)
                )
            raise

        if self.save_responses:
            self._saved_responses[request_fingerprint(request)] = _SavedResponseData(
                request, response
            )
        self._handle_status(response, request, allow_status=allow_status)
        return response

    async def batch_execute(
        self,
        *requests: HttpRequest,
        return_exceptions: bool = False,
        allow_status: _StatusList | None = None,
    ) -> list[HttpResponse | HttpResponseError]:
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
        return cast("list[Union[HttpResponse, HttpResponseError]]", responses)

    def get_saved_responses(self) -> Iterable[_SavedResponseData]:
        """Return saved requests and responses."""
        return self._saved_responses.values()


def _http_status_name(status: int) -> str:
    """
    >>> _http_status_name(200)
    'OK'
    >>> _http_status_name(404)
    'NOT_FOUND'
    >>> _http_status_name(999)
    'UNKNOWN'
    """
    try:
        return HTTPStatus(status).name
    except ValueError:
        return "UNKNOWN"
