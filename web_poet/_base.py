"""Contains some internal definitions that is internal to **web-poet**.

In general, users shouldn't import and use the contents of this module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, AnyStr, Union, overload

from multidict import CIMultiDict

if TYPE_CHECKING:
    # typing.Self requires Python 3.11
    from typing_extensions import Self


_AnyStrDict = dict[AnyStr, Union[AnyStr, list[AnyStr], tuple[AnyStr, ...]]]


class _HttpHeaders(CIMultiDict):
    """A base container for holding the HTTP headers.

    For more info on its other features, read the API spec of
    :class:`multidict.CIMultiDict`.
    """

    @classmethod
    def from_name_value_pairs(cls, arg: list[dict]) -> Self:
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

    @classmethod
    def from_bytes_dict(cls, arg: _AnyStrDict, encoding: str = "utf-8") -> Self:
        """An alternative constructor for instantiation where the header-value
        pairs could be in raw bytes form.

        This supports multiple header values in the form of ``List[bytes]`` and
        ``Tuple[bytes]]`` alongside a plain ``bytes`` value. A value in ``str``
        also works and wouldn't break the decoding process at all.

        By default, it converts the ``bytes`` value using "utf-8". However, this
        can easily be overridden using the ``encoding`` parameter.

        >>> raw_values = {
        ...     b"Content-Encoding": [b"gzip", b"br"],
        ...     b"Content-Type": [b"text/html"],
        ...     b"content-length": b"648",
        ... }
        >>> headers = _HttpHeaders.from_bytes_dict(raw_values)
        >>> headers
        <_HttpHeaders('Content-Encoding': 'gzip', 'Content-Encoding': 'br', 'Content-Type': 'text/html', 'content-length': '648')>
        """

        @overload
        def _norm(data: str | bytes) -> str: ...

        @overload
        def _norm(data: None) -> None: ...

        def _norm(data: str | bytes | None) -> str | None:
            if isinstance(data, str) or data is None:
                return data
            if isinstance(data, bytes):
                return data.decode(encoding)
            raise ValueError(f"Expecting str or bytes. Received {type(data)}")

        converted = []

        for header, value in arg.items():
            if isinstance(value, (list, tuple)):
                converted.extend([(_norm(header), _norm(v)) for v in value])
            else:
                converted.append((_norm(header), _norm(value)))

        return cls(converted)
