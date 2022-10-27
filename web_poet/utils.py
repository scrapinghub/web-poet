import inspect
import weakref
from collections.abc import Iterable
from functools import lru_cache, wraps
from types import MethodType
from typing import Any, Callable, List, Optional, TypeVar, Union
from warnings import warn

from async_lru import alru_cache
from url_matcher import Patterns


def _clspath(cls, forced=None):
    if forced is not None:
        return forced
    return f"{cls.__module__}.{cls.__name__}"


def _create_deprecated_class(
    name,
    new_class,
    clsdict=None,
    warn_once=True,
    old_class_path=None,
    new_class_path=None,
    subclass_warn_message="{cls} inherits from deprecated class {old}, please inherit from {new}.",
    instance_warn_message="{cls} is deprecated, instantiate {new} instead.",
):
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

    class DeprecatedClass(new_class.__class__):

        deprecated_class = None
        warned_on_subclass = False

        def __new__(metacls, name, bases, clsdict_):
            cls = super().__new__(metacls, name, bases, clsdict_)
            if metacls.deprecated_class is None:
                metacls.deprecated_class = cls
            return cls

        def __init__(cls, name, bases, clsdict_):
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
        def __instancecheck__(cls, inst):
            return any(cls.__subclasscheck__(c) for c in (type(inst), inst.__class__))

        def __subclasscheck__(cls, sub):
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

        def __call__(cls, *args, **kwargs):
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
        warn(f"Error detecting parent module: {e!r}")

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
            cached_meth = alru_cache(maxsize=None)(bound_method)
            setattr(self, cached_method_name, cached_meth)
        else:
            cached_meth = getattr(self, cached_method_name)
        return await cached_meth(*args, **kwargs)

    return inner


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


def str_to_pattern(url_pattern: Union[str, Patterns]) -> Patterns:
    if isinstance(url_pattern, Patterns):
        return url_pattern
    return Patterns([url_pattern])
