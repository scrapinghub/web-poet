from typing import Optional, Dict, List, Any, AnyStr, Union

import attr

mapping = Dict[AnyStr, AnyStr]


@attr.define
class HttpResponseBody:
    """A container for holding the HTTP response body which is split into two
    parts.

    ``raw`` contains the preserved HTTP response body content in bytes.

    ``html`` should be content of the HTTP body, converted to unicode
    using the detected encoding of the response, preferably according
    to the web browser rules (respecting Content-Type header, etc.).
    """

    raw: bytes
    html: str


@attr.define
class HttpResponseHeaders:
    """A container for holdling the HTTP response headers.

    ``data`` contains the list of key-value pairs of headers. It could be either
    in string or raw bytes format.
    """
    data: List[mapping]


@attr.define
class ResponseData:
    """A container for the contents of a response, downloaded directly using an
    HTTP client.

    ``url`` should be an URL of the response (after all redirects),
    not an URL of the request, if possible.

    ``body`` contains the HTTP response body.

    The following are optional since it would depend on the source of the
    ``ResponseData`` if these are available or not. For example, the responses
    could simply come off from a local HTML file which doesn't contain ``headers``
    and ``status``.

    ``status`` should represent the int status code of the HTTP response.

    ``headers`` should contain the HTTP response headers.
    """

    url: str
    body: HttpResponseBody
    status: Optional[int] = None
    headers: Optional[HttpResponseHeaders] = None
