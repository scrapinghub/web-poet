from __future__ import annotations

import logging
from collections.abc import Awaitable
from contextvars import ContextVar
from typing import Callable

from web_poet.exceptions import RequestDownloaderVarError
from web_poet.page_inputs.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)

#: Frameworks that wants to support additional requests in ``web-poet`` should
#: set the appropriate implementation of ``request_downloader_var``
#: for requesting data.
RequestDownloaderT = Callable[[HttpRequest], Awaitable[HttpResponse]]
request_downloader_var: ContextVar[RequestDownloaderT] = ContextVar(
    "request_downloader"
)


async def _perform_request(request: HttpRequest) -> HttpResponse:
    """Given a :class:`~.Request`, execute it using the **request implementation**
    that was set in the ``web_poet.request_downloader_var`` :mod:`contextvars`
    instance.
    """

    logger.info(f"Requesting page: {request}")

    try:
        request_downloader = request_downloader_var.get()
    except LookupError as ex:
        raise RequestDownloaderVarError(
            "Additional requests are used inside the Page Object but the "
            "current framework has not set any HttpRequest Backend via "
            "'web_poet.request_downloader_var'"
        ) from ex

    return await request_downloader(request)
