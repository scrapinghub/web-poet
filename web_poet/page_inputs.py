import attr


@attr.s(auto_attribs=True)
class ResponseData:
    """A container for URL and HTML content of a response, downloaded
    directly using an HTTP client.

    ``url`` should be an URL of the response (after all redirects),
    not an URL of the request, if possible.

    ``html`` should be content of the HTTP body, converted to unicode
    using the detected encoding of the response, preferably according
    to the web browser rules (respecting Content-Type header, etc.)
    """
    url: str
    html: str
