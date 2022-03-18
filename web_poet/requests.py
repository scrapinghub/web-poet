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
from typing import Optional, List, Dict, ByteString, Any, Union, Callable

import attr

from web_poet.page_inputs import HttpResponse

logger = logging.getLogger(__name__)


mapping = Dict[Union[str, ByteString], Any]

# Frameworks that wants to support additional requests in ``web-poet`` should
# set the appropriate implementation for requesting data.
request_backend_var: ContextVar = ContextVar("request_backend")


class RequestBackendError(Exception):
    """Indicates that the ``web_poet.request_backend_var`` wasn't set
    by the framework using **web-poet**.

    See the documentation section about :ref:`setting up the contextvars <setup-contextvars>`
    to learn more about this.
    """

    pass


@attr.define
class Request:
    """Represents a generic HTTP request used by other functionalities in
    **web-poet** like :class:`~.HttpClient`.
    """

    url: str
    method: str = "GET"
    headers: Optional[mapping] = None
    body: Optional[str] = None


async def _perform_request(request: Request) -> ResponseData:
    """Given a :class:`~.Request`, execute it using the **request implementation**
    that was set in the ``web_poet.request_backend_var`` :mod:`contextvars`
    instance.

    .. warning::
        By convention, this function should return a :class:`~.ResponseData`.
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
            "current framework has not set any Request Backend via "
            "'web_poet.request_backend_var'"
        )

    response_data: ResponseData = await request_backend(request)
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
    implementation returns a :class:`~.ResponseData` instance.
    """

    def __init__(self, request_downloader: Callable = None):
        self.request_downloader = request_downloader or _perform_request

    async def request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[mapping] = None,
        body: Optional[str] = None,
    ) -> ResponseData:
        """This is a shortcut for creating a :class:`Request` instance and executing
        that request.

        A :class:`~.ResponseData` instance should then be returned.

        .. warning::
            By convention, the request implementation supplied optionally to
            :class:`~.HttpClient` should return a :class:`~.ResponseData` instance.
            However, the underlying implementation supplied might change that,
            depending on how the framework using **web-poet** implements it.
        """
        r = Request(url, method, headers, body)
        return await self.request_downloader(r)

    async def get(self, url: str, headers: Optional[mapping] = None) -> ResponseData:
        """Similar to :meth:`~.HttpClient.request` but peforming a ``GET``
        request.
        """
        return await self.request(url=url, method="GET", headers=headers)

    async def post(
        self, url: str, headers: Optional[mapping] = None, body: Optional[str] = None
    ) -> ResponseData:
        """Similar to :meth:`~.HttpClient.request` but peforming a ``POST``
        request.
        """
        return await self.request(url=url, method="POST", headers=headers, body=body)

    async def batch_requests(self, *requests: Request) -> List[ResponseData]:
        """Similar to :meth:`~.HttpClient.request` but accepts a collection of
        :class:`~.Request` instances that would be batch executed.
        """

        coroutines = [self.request_downloader(r) for r in requests]
        responses = await asyncio.gather(*coroutines)
        return responses
