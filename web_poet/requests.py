"""
Quick Start
-----------

.. code-block:: python

    from web_poet import requests

Developers could then use this alongside the ``async/await`` syntax in Python
to issue additional requests.


Use Cases
---------

Additional requests in Page Objects are hard to avoid since webpages nowadays
requires some dynamic interactions. Some examples would be:

    - "clicking" a load more button that loads more data.
    - "scrolling" to paginate an infinite page.
    - "hovering" that reveals a tool-tip containing additional page info.
    - etc

In most cases, these are done via AJAX requests.

.. warning::

    Additional requests should not be confused with "crawling" which aims to
    visit multiple webpages from a given website. Additional requests are simply
    a means to interact with the website to access more information from it.


Use for other frameworks
------------------------

Please note that on its own, ``web_poet.request`` doesn't do anything. It doesn't
know how to implement the request on its own. Thus, for frameworks or projects
wanting to use additional requests in Page Objects, they need to set the
implementation of how to download things via:

.. code-block:: python

    web_poet.request_backend_var.set(downloader_implementation)
"""

import asyncio
import logging
from contextvars import ContextVar
from typing import Optional, List, Dict, ByteString, Any, Union

import attr

logger = logging.getLogger(__name__)


# Frameworks that wants to support additional requests in ``web-poet`` should
# set the appropriate implementation for requesting data.
request_backend_var: ContextVar = ContextVar("request_backend")


class RequestBackendError(Exception):
    pass


@attr.define
class GenericRequest:
    """Represents a generic HTTP request."""

    url: str
    method: str = "GET"
    headers: Optional[Dict[Union[str, ByteString], Any]] = None
    body: Optional[str] = None


async def perform_request(request: GenericRequest):
    logger.info(f"Requesting page: {request}")

    try:
        request_backend = request_backend_var.get()
    except LookupError:
        raise RequestBackendError(
            "Additional requests are used inside the Page Object but the "
            "current framework has not set any Request Backend via "
            "'web_poet.request_backend_var'"
        )

    response_data = await request_backend(request)
    return response_data


class HttpClient:
    def __init__(self, request_downloader=None):
        self.request_downloader = request_downloader or perform_request

    async def request(self, *requests: List[GenericRequest]):
        coroutines = [self.request_downloader(r) for r in requests]
        responses = await asyncio.gather(*coroutines)
        return responses
