"""
HTTP Exceptions
~~~~~~~~~~~~~~~

These are exceptions pertaining to common issues faced when executing HTTP
operations.
"""


class HttpRequestError(IOError):
    """Indicates that an exception has occurred when the HTTP Request was being
    handled.

    For responses that are successful but don't have a ``200`` **status code**,
    this exception shouldn't be raised at all. Instead, the :class:`~.HttpResponse`
    should simply reflect the response contents as is.
    """

    pass
