"""
HTTP Exceptions
~~~~~~~~~~~~~~~

These are exceptions pertaining to common issues faced when executing HTTP
operations.
"""


class HttpRequestError(IOError):
    """Indicates that an exception has occurred when the HTTP Request was being
    handled.
    """

    pass
