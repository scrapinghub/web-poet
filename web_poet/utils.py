from __future__ import annotations

import inspect
import weakref
from collections import deque
from collections.abc import Iterable
from functools import lru_cache, partial, wraps
from types import MethodType
from typing import Any, Callable, TypeVar, get_args
from warnings import warn

import packaging.version
from async_lru import __version__ as async_lru_version
from async_lru import alru_cache
from url_matcher import Patterns


def callable_has_parameter(obj: Callable[..., Any], name: str) -> bool:
    try:
        sig = inspect.signature(obj)
    except ValueError:  # built-in, e.g. int
        return False
    else:
        return name in sig.parameters


def get_fq_class_name(cls: type) -> str:
    """Return the fully qualified name for a type.

    >>> from web_poet import Injectable
    >>> get_fq_class_name(Injectable)
    'web_poet.pages.Injectable'
    >>> from decimal import Decimal
    >>> get_fq_class_name(Decimal)
    'decimal.Decimal'
    """
    return f"{cls.__module__}.{cls.__qualname__}"


def _clspath(cls: type, forced: str | None = None) -> str:
    if forced is not None:
        return forced
    return get_fq_class_name(cls)


def _create_deprecated_class(
    name: str,
    new_class: type,
    clsdict: dict[str, Any] | None = None,
    warn_once: bool = True,
    old_class_path: str | None = None,
    new_class_path: str | None = None,
    subclass_warn_message: str = "{cls} inherits from deprecated class {old}, please inherit from {new}.",
    instance_warn_message: str = "{cls} is deprecated, instantiate {new} instead.",
) -> type:
    """
    Return a "deprecated" class that causes its subclasses to issue a warning.
    Subclasses of ``new_class`` are considered subclasses of this class.
    It also warns when the deprecated class is instantiated, but do not when
    its subclasses are instantiated.
    It can be used to rename a base class in a library. For example, if we
    have
        class OldName(SomeClass):
            # ...
    and we want to rename it to NewName, we can do the following::
        class NewName(SomeClass):
            # ...
        OldName = _create_deprecated_class('OldName', NewName)
    Then, if user class inherits from OldName, warning is issued. Also, if
    some code uses ``issubclass(sub, OldName)`` or ``isinstance(sub(), OldName)``
    checks they'll still return True if sub is a subclass of NewName instead of
    OldName.
    """

    class DeprecatedClass(new_class.__class__):  # type: ignore[misc, name-defined]
        deprecated_class = None
        warned_on_subclass = False

        def __new__(
            metacls, name: str, bases: tuple[type, ...], clsdict_: dict[str, Any]
        ) -> type:
            cls = super().__new__(metacls, name, bases, clsdict_)
            if metacls.deprecated_class is None:
                metacls.deprecated_class = cls
            return cls

        def __init__(cls, name: str, bases: tuple[type, ...], clsdict_: dict[str, Any]):
            meta = cls.__class__
            old = meta.deprecated_class
            if old in bases and not (warn_once and meta.warned_on_subclass):
                meta.warned_on_subclass = True
                msg = subclass_warn_message.format(
                    cls=_clspath(cls),
                    old=_clspath(old, old_class_path),
                    new=_clspath(new_class, new_class_path),
                )
                if warn_once:
                    msg += " (warning only on first subclass, there may be others)"
                warn(msg, DeprecationWarning, stacklevel=2)
            super().__init__(name, bases, clsdict_)

        # see https://www.python.org/dev/peps/pep-3119/#overloading-isinstance-and-issubclass
        # and https://docs.python.org/reference/datamodel.html#customizing-instance-and-subclass-checks
        # for implementation details
        def __instancecheck__(cls, inst: Any) -> bool:
            return any(cls.__subclasscheck__(c) for c in (type(inst), inst.__class__))

        def __subclasscheck__(cls, sub: type) -> bool:
            if cls is not DeprecatedClass.deprecated_class:
                # we should do the magic only if second `issubclass` argument
                # is the deprecated class itself - subclasses of the
                # deprecated class should not use custom `__subclasscheck__`
                # method.
                return super().__subclasscheck__(sub)

            if not inspect.isclass(sub):
                raise TypeError("issubclass() arg 1 must be a class")

            mro = getattr(sub, "__mro__", ())
            return any(c in {cls, new_class} for c in mro)

        def __call__(cls, *args: Any, **kwargs: Any) -> Any:
            old = DeprecatedClass.deprecated_class
            if cls is old:
                msg = instance_warn_message.format(
                    cls=_clspath(cls, old_class_path),
                    new=_clspath(new_class, new_class_path),
                )
                warn(msg, DeprecationWarning, stacklevel=2)
            return super().__call__(*args, **kwargs)

    deprecated_cls = DeprecatedClass(name, (new_class,), clsdict or {})

    try:
        frm = inspect.stack()[1]
        parent_module = inspect.getmodule(frm[0])
        if parent_module is not None:
            deprecated_cls.__module__ = parent_module.__name__
    except Exception as e:
        # Sometimes inspect.stack() fails (e.g. when the first import of
        # deprecated class is in jinja2 template). __module__ attribute is not
        # important enough to raise an exception as users may be unable
        # to fix inspect.stack() errors.
        warn(f"Error detecting parent module: {e!r}", stacklevel=1)

    return deprecated_cls


CallableT = TypeVar("CallableT", bound=Callable)


def memoizemethod_noargs(method: CallableT) -> CallableT:
    """Decorator to cache the result of a method (without arguments) using a
    weak reference to its object.

    It is faster than :func:`cached_method`, and doesn't add new attributes
    to the instance, but it doesn't work if objects are unhashable.
    """
    cache: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()

    @wraps(method)
    def new_method(self, *args, **kwargs):
        if self not in cache:
            cache[self] = method(self, *args, **kwargs)
        return cache[self]

    return new_method  # type: ignore[return-value]


def cached_method(method: CallableT) -> CallableT:
    """A decorator to cache method or coroutine method results,
    so that if it's called multiple times for the same instance,
    computation is only done once.

    The cache is unbound, but it's tied to the instance lifetime.

    .. note::

        :func:`cached_method` is needed because :func:`functools.lru_cache`
        doesn't work well on methods: self is used as a cache key,
        so a reference to an instance is kept in the cache, and this
        prevents deallocation of instances.

    This decorator adds a new private attribute to the instance named
    ``_cached_method_{decorated_method_name}``; make sure the class
    doesn't define an attribute of the same name.
    """
    cached_meth_name = f"_cached_method_{method.__name__}"
    if inspect.iscoroutinefunction(method):
        meth = _cached_method_async(method, cached_meth_name)
    else:
        meth = _cached_method_sync(method, cached_meth_name)

    meth.cached_method_name = cached_meth_name
    return meth


def _cached_method_sync(method, cached_method_name: str):
    @wraps(method)
    def inner(self, *args, **kwargs):
        if not hasattr(self, cached_method_name):
            # on a first call, create a lru_cache-wrapped method,
            # and store it on the instance
            bound_method = MethodType(method, self)
            cached_meth = lru_cache(maxsize=None)(bound_method)
            setattr(self, cached_method_name, cached_meth)
        else:
            cached_meth = getattr(self, cached_method_name)
        return cached_meth(*args, **kwargs)

    return inner


def _cached_method_async(method, cached_method_name: str):
    @wraps(method)
    async def inner(self, *args, **kwargs):
        if not hasattr(self, cached_method_name):
            # on a first call, create an alru_cache-wrapped method,
            # and store it on the instance
            bound_method = MethodType(method, self)
            cached_meth = _alru_cache(maxsize=None)(bound_method)
            setattr(self, cached_method_name, cached_meth)
        else:
            cached_meth = getattr(self, cached_method_name)
        return await cached_meth(*args, **kwargs)

    return inner


# async_lru >= 2.0.0 removed cache_exceptions argument, and changed
# its default value. `_alru_cache` is a compatibility function which works with
# all async_lru versions and uses the same approach for exception caching
# as async_lru >= 2.0.0.
_alru_cache: Callable = alru_cache
_async_lru_version = packaging.version.parse(async_lru_version)
if _async_lru_version.major < 2:
    _alru_cache = partial(alru_cache, cache_exceptions=False)


def as_list(value: Any) -> list[Any]:
    """Normalizes the value input as a list.

    >>> as_list(None)
    []
    >>> as_list("foo")
    ['foo']
    >>> as_list(123)
    [123]
    >>> as_list(["foo", "bar", 123])
    ['foo', 'bar', 123]
    >>> as_list(("foo", "bar", 123))
    ['foo', 'bar', 123]
    >>> as_list(range(5))
    [0, 1, 2, 3, 4]
    >>> def gen():
    ...     yield 1
    ...     yield 2
    >>> as_list(gen())
    [1, 2]
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if not isinstance(value, Iterable):
        return [value]
    return list(value)


async def ensure_awaitable(obj):
    """Return the value of obj, awaiting it if needed"""
    if inspect.isawaitable(obj):
        return await obj
    return obj


def str_to_pattern(url_pattern: str | Patterns) -> Patterns:
    if isinstance(url_pattern, Patterns):
        return url_pattern
    return Patterns([url_pattern])


def get_generic_param(cls: type, expected: type | tuple[type, ...]) -> type | None:
    """Search the base classes recursively breadth-first for a generic class and return its param.

    Returns the param of the first found class that is a subclass of ``expected``.
    """
    visited = set()
    queue = deque([cls])
    while queue:
        node = queue.popleft()
        visited.add(node)
        for base in getattr(node, "__orig_bases__", []):
            origin = getattr(base, "__origin__", None)
            if origin and issubclass(origin, expected):
                result = get_args(base)[0]
                if not isinstance(result, TypeVar):
                    return result
            queue.append(base)
    return None
