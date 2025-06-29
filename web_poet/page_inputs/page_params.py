from __future__ import annotations

from typing import TypeVar

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class PageParams(dict[_KT, _VT]):
    """Container class that could contain any arbitrary data to be passed into
    a Page Object.

    Note that this is simply a subclass of Python's ``dict``.
    """
