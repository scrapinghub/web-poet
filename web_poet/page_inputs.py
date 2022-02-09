from typing import Optional, Dict, Any, ByteString, Union
from contextlib import suppress

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

    The following are optional since it would depend on the source of the
    ``ResponseData`` if these are available or not. For example, the responses
    could simply come off from a local HTML file which doesn't contain ``headers``
    and ``status``.

    ``status`` should represent the int status code of the HTTP response.

    ``headers`` should contain the HTTP response headers.
    """

    url: str
    html: str
    status: Optional[int] = None
    headers: Optional[Dict[Union[str, ByteString], Any]] = None


class Meta:
    """Container class that could contain any arbitrary data.

    Using this is more useful to pass things around compared to a ``dict`` due
    to these following characteristics:

        - You can use Python's "." attribute syntax for it.
        - Accessing attributes that are not existing won't result in errors.
          Instead, a ``None`` value will be returned.
        - The same goes for deleting attributes that don't exist wherein errors
          will be suppressed.

    This makes the code simpler by avoiding try/catch, checking an attribute's
    existence, using ``get()``, etc.
    """

    def __init__(self, **kwargs):
        object.__setattr__(self, "_data", kwargs)

    def __getattr__(self, key):
        return self._data.get(key)

    def __delattr__(self, key):
        with suppress(KeyError):
            del self._data[key]

    def __setattr__(self, key, value):
        self._data[key] = value
