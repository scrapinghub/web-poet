import logging
from contextvars import ContextVar

from web_poet.exceptions import RequestBackendError
from web_poet.page_inputs.http import (
    HttpRequest,
    HttpResponse,
)

logger = logging.getLogger(__name__)

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
