import inspect
from typing import Optional, Dict, Any, List

import attr
from multidict import CIMultiDict


class HttpResponseBody(bytes):
    """A container for holding the raw HTTP response body in bytes format."""

    pass


class HttpResponseHeaders(CIMultiDict):
    """A container for holding the HTTP response headers.

    It's able to accept instantiation via an Iterable of Tuples:

    >>> pairs = [("Content-Encoding", "gzip"), ("content-length", "648")]
    >>> HttpResponseHeaders(pairs)
    <HttpResponseHeaders('Content-Encoding': 'gzip', 'content-length': '648')>

    It's also accepts a mapping of key-value pairs as well:

    >>> pairs = {"Content-Encoding": "gzip", "content-length": "648"}
    >>> headers = HttpResponseHeaders(pairs)
    >>> headers
    <HttpResponseHeaders('Content-Encoding': 'gzip', 'content-length': '648')>

    Note that this also supports case insensitive header-key lookups:

    >>> headers.get("content-encoding")
    'gzip'
    >>> headers.get("Content-Length")
    '648'

    These are just a few of the functionalities it inherits from
    :class:`multidict.CIMultiDict`. For more info on its other features, read
    the API spec of :class:`multidict.CIMultiDict`.
    """

    @classmethod
    def from_name_value_pairs(cls, arg: List[Dict]):
        """An alternative constructor for instantiation using a ``List[Dict]``
        where the 'key' is the header name while the 'value' is the header value.

        >>> pairs = [
        ...     {"name": "Content-Encoding", "value": "gzip"},
        ...     {"name": "content-length", "value": "648"}
        ... ]
        >>> headers = HttpResponseHeaders.from_name_value_pairs(pairs)
        >>> headers
        <HttpResponseHeaders('Content-Encoding': 'gzip', 'content-length': '648')>
        """
        return cls([(pair["name"], pair["value"]) for pair in arg])


@attr.define
class ResponseData:
    """A container for the contents of a response, downloaded directly using an
    HTTP client.

    ``url`` should be an URL of the response (after all redirects),
    not an URL of the request, if possible.

    ``html`` should be content of the HTTP body, converted to unicode
    using the detected encoding of the response, preferably according
    to the web browser rules (respecting Content-Type header, etc.)

    ``body`` contains the raw HTTP response body.

    The following are optional since it would depend on the source of the
    ``ResponseData`` if these are available or not. For example, the responses
    could simply come off from a local HTML file which doesn't contain ``headers``
    and ``status``.

    ``status`` should represent the int status code of the HTTP response.

    ``headers`` should contain the HTTP response headers.
    """

    url: str
    html: str
    body: Optional[HttpResponseBody] = None
    status: Optional[int] = None
    headers: Optional[HttpResponseHeaders] = None


class Meta(dict):
    """Container class that could contain any arbitrary data to be passed into
    a Page Object.

    This is basically a subclass of a ``dict`` that adds the ability to check
    if any of the assigned values are not allowed. This ensures that some input
    parameters with data types that are difficult to provide or pass via CLI
    like ``lambdas`` are checked. Otherwise, a ``ValueError`` is raised.
    """

    # Any "value" that returns True for the functions here are not allowed.
    restrictions: Dict = {
        inspect.ismodule: "module",
        inspect.isclass: "class",
        inspect.ismethod: "method",
        inspect.isfunction: "function",
        inspect.isgenerator: "generator",
        inspect.isgeneratorfunction: "generator",
        inspect.iscoroutine: "coroutine",
        inspect.isawaitable: "awaitable",
        inspect.istraceback: "traceback",
        inspect.isframe: "frame",
    }

    def __init__(self, *args, **kwargs) -> None:
        for val in kwargs.values():
            self.enforce_value_restriction(val)
        super().__init__(*args, **kwargs)

    def __setitem__(self, key: Any, value: Any) -> None:
        self.enforce_value_restriction(value)
        super().__setattr__(key, value)

    def enforce_value_restriction(self, value: Any) -> None:
        """Raises a ``ValueError`` if a given value isn't allowed inside the meta.

        This method is called during :class:`~.Meta` instantiation and setting
        new values in an existing instance.

        This behavior can be controlled by tweaking the class variable named
        ``restrictions``.
        """
        violations = []

        for restrictor, err in self.restrictions.items():
            if restrictor(value):
                violations.append(f"{err} is not allowed: {value}")

        if violations:
            raise ValueError(f"Found these issues: {', '.join(violations)}")
