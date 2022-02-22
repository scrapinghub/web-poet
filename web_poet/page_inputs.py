from typing import Optional, Dict, Any, ByteString, Union

import attr

from web_poet import Request


@attr.s(auto_attribs=True)
class ResponseData:
    """A container for URL and HTML content of a response, downloaded
    directly using an HTTP client.

    ``url`` should be an URL of the response (after all redirects),
    not an URL of the request, if possible.

    ``html`` should be content of the HTTP body, converted to unicode
    using the detected encoding of the response, preferably according
    to the web browser rules (respecting Content-Type header, etc.)

    The following are optional since it would depend on the source of the
    ``ResponseData`` if these are available or not. For example, the responses
    could simply come off from a local HTML file which doesn't contain ``headers``
    and ``status``.

    ``status`` should represent the int status code of the HTTP response.

    ``headers`` should contain the HTTP response headers.

    ``request`` links the ``web_poet.Requests`` that was used to produce it.
    """

    url: str
    body: HttpResponseBody
    status: Optional[int] = None
    headers: Optional[HttpResponseHeaders] = None
    request: Optional[Request] = None


@attr.define
class HttpResponseBody:
    raw_data: bytes
    html: str


@attr.define
class HttpResponseHeaders:
    data: List[Dict[ByteString, ByteString]]
