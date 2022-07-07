"""Contains some internal definitions that is internal to **web-poet**.

In general, users shouldn't import and use the contents of this module.
"""

from typing import Dict, List, Type, TypeVar

from multidict import CIMultiDict

T_headers = TypeVar("T_headers", bound="_HttpHeaders")


class _HttpHeaders(CIMultiDict):
    """A base container for holding the HTTP headers.

    For more info on its other features, read the API spec of
    :class:`multidict.CIMultiDict`.
    """

    @classmethod
    def from_name_value_pairs(cls: Type[T_headers], arg: List[Dict]) -> T_headers:
        """An alternative constructor for instantiation using a ``List[Dict]``
        where the 'key' is the header name while the 'value' is the header value.

        >>> pairs = [
        ...     {"name": "Content-Encoding", "value": "gzip"},
        ...     {"name": "content-length", "value": "648"}
        ... ]
        >>> headers = _HttpHeaders.from_name_value_pairs(pairs)
        >>> headers
        <_HttpHeaders('Content-Encoding': 'gzip', 'content-length': '648')>
        """
        return cls([(pair["name"], pair["value"]) for pair in arg])
