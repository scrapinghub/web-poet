import inspect
from typing import Optional, Dict, Any, ByteString, Union, Set
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


class Meta(dict):
    """Container class that could contain any arbitrary data to be passed into
    a Page Object.

    This is basically a subclass of a ``dict`` but adds some additional
    functionalities to ensure consistent and compatible Page Objects across
    different use cases:

    * A class variable named ``required_data`` to ensure consistent
      arguments. If it's instantiated with missing ``keys`` from
      ``required_data``, then a ``ValueError`` is raised.

    * Ensures that some params with data types that are difficult to
      provide or pass like ``lambdas`` are checked. Otherwise, a ``ValueError``
      is raised.
    """

    # Contains the required "keys" when instantiating and setting attributes.
    required_data: Set = set()

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
        missing_required_keys = self.required_data - kwargs.keys()
        if missing_required_keys:
            raise ValueError(
                f"These keys are required for instantiation: {missing_required_keys}"
            )
        for val in kwargs.values():
            self.is_restricted_value(val)
        super().__init__(*args, **kwargs)

    def __setitem__(self, key: Any, value: Any) -> None:
        self.is_restricted_value(value)
        super().__setattr__(key, value)

    def is_restricted_value(self, value: Any) -> None:
        """Raises an error if a given value isn't allowed inside the meta.

        This behavior can be controlled by tweaking the class variable
        :meth:`~.web_poet.page_inputs.Meta.restrictions`.
        """
        violations = []

        for restrictor, err in self.restrictions.items():
            if restrictor(value):
                violations.append(f"{err} is not allowed: {value}")

        if violations:
            raise ValueError(f"Found these issues: {', '.join(violations)}")
