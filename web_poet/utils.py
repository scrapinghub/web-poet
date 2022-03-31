import weakref
from functools import wraps
from typing import Any, Optional, List


def memoizemethod_noargs(method):
    """Decorator to cache the result of a method (without arguments) using a
    weak reference to its object
    """
    cache = weakref.WeakKeyDictionary()

    @wraps(method)
    def new_method(self, *args, **kwargs):
        if self not in cache:
            cache[self] = method(self, *args, **kwargs)
        return cache[self]

    return new_method


def as_list(value: Optional[Any]) -> List[Any]:
    """Normalizes the value input as a list.

    >>> as_list(None)
    []
    >>> as_list("foo")
    ['foo']
    >>> as_list(123)
    [123]
    >>> as_list(["foo", "bar", 123])
    ['foo', 'bar', 123]
    """
    if value is None:
        return []
    if not isinstance(value, list):
        return [value]
    return list(value)
