"""
``web_poet.fields`` is a module with helpers for putting extraction logic
into separate Page Object methods / properties.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from contextlib import suppress
from functools import update_wrapper, wraps
from typing import Any, Generic, TypeVar, cast, overload

import attrs
from itemadapter import ItemAdapter

from web_poet.utils import cached_method, callable_has_parameter, ensure_awaitable

_FIELDS_INFO_ATTRIBUTE_READ = "_web_poet_fields_info"
_FIELDS_INFO_ATTRIBUTE_WRITE = "_web_poet_fields_info_temp"
_FIELD_METHODS_ATTRIBUTE = "_web_poet_field_methods"

_PageT = TypeVar("_PageT")
_ReturnT = TypeVar("_ReturnT")
_FieldMethod = Callable[[_PageT], _ReturnT]


@attrs.define
class FieldInfo:
    """Information about a field"""

    #: name of the field
    name: str

    #: field metadata
    meta: dict | None = None

    #: field processors
    out: list[Callable] | None = None


class FieldsMixin:
    """A mixin which is required for a class to support fields"""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # To support fields, we must ensure that fields dict is not shared
        # between subclasses, i.e. a decorator in a subclass doesn't affect
        # the base class. This is done by making decorator write to a
        # temporary location, and then merging it all on subclass creation.
        this_class_fields: dict[str, FieldInfo] = getattr(
            cls, _FIELDS_INFO_ATTRIBUTE_WRITE, {}
        )
        base_fields: dict[str, FieldInfo] = {}
        for base_class in cls.__bases__:
            fields = getattr(base_class, _FIELDS_INFO_ATTRIBUTE_READ, {})
            base_fields.update(fields)
        if base_fields or this_class_fields:
            fields = {**base_fields, **this_class_fields}
            setattr(cls, _FIELDS_INFO_ATTRIBUTE_READ, fields)
            with suppress(AttributeError):
                delattr(cls, _FIELDS_INFO_ATTRIBUTE_WRITE)
        setattr(cls, _FIELD_METHODS_ATTRIBUTE, {})


class _FieldDescriptor(Generic[_PageT, _ReturnT]):
    def __init__(
        self,
        method: _FieldMethod[_PageT, _ReturnT],
        *,
        cached: bool,
        meta: dict | None,
        out: list[Callable] | None,
    ):
        if not callable(method):
            raise TypeError(
                f"@field decorator must be used on methods, {method!r} is decorated instead"
            )
        self.original_method = method
        self.cached = cached
        self.meta = meta
        self.out = out
        self.name: str | None = None
        update_wrapper(cast("Callable", self), method)

    def __set_name__(self, owner, name: str) -> None:
        self.name = name
        if not hasattr(owner, _FIELDS_INFO_ATTRIBUTE_WRITE):
            setattr(owner, _FIELDS_INFO_ATTRIBUTE_WRITE, {})

        field_info = FieldInfo(name=name, meta=self.meta, out=self.out)
        getattr(owner, _FIELDS_INFO_ATTRIBUTE_WRITE)[name] = field_info

    @overload
    def __get__(
        self, instance: None, owner: type[_PageT] | None = None
    ) -> _FieldDescriptor[_PageT, _ReturnT]: ...

    @overload
    def __get__(
        self, instance: _PageT, owner: type[_PageT] | None = None
    ) -> _ReturnT: ...

    def __get__(self, instance, owner=None):
        # When accessed on the class (instance is None) return the
        # descriptor itself (which has been wrapped with the original
        # function attributes) so that __doc__ and other metadata are
        # preserved.
        if instance is None:
            return self

        # We use the original method and the out arg from the field and
        # the Processors class from the instance class, so caching needs to
        # take into account the instance class and the field object. So we
        # use the field object id() as a key when caching the method in
        # the instance class.
        cache_key = id(self)
        method = self._get_processed_method(owner, cache_key)
        if method is None:
            if self.out is not None:
                processor_functions = self.out
            elif hasattr(owner, "Processors"):
                assert self.name is not None
                processor_functions = getattr(owner.Processors, self.name, [])
            else:
                processor_functions = []
            processors: list[tuple[Callable, bool]] = []
            for processor_function in processor_functions:
                takes_page = callable_has_parameter(processor_function, "page")
                processors.append((processor_function, takes_page))
            method = self._processed(self.original_method, processors)
            if self.cached:
                method = cached_method(method)
            self._set_processed_method(owner, cache_key, method)

        return cast("_ReturnT", method(instance))

    @staticmethod
    def _get_processed_method(page_cls, key: int):
        return getattr(page_cls, _FIELD_METHODS_ATTRIBUTE).get(key)

    @staticmethod
    def _set_processed_method(page_cls, key: int, method) -> None:
        getattr(page_cls, _FIELD_METHODS_ATTRIBUTE)[key] = method

    @staticmethod
    def _process(value: Any, page, processors: list[tuple[Callable, bool]]) -> Any:
        for processor, takes_page in processors:
            value = processor(value, page=page) if takes_page else processor(value)
        return value

    @staticmethod
    def _processed(method, processors: list[tuple[Callable, bool]]):
        """Returns a wrapper for method that calls processors on its result"""
        if inspect.iscoroutinefunction(method):

            async def processed(page):
                if hasattr(page, "_validate_input"):
                    validation_item = page._validate_input()
                    if validation_item is not None:
                        return getattr(validation_item, method.__name__)
                return _FieldDescriptor._process(await method(page), page, processors)

        else:

            def processed(page):
                if hasattr(page, "_validate_input"):
                    validation_item = page._validate_input()
                    if validation_item is not None:
                        return getattr(validation_item, method.__name__)
                return _FieldDescriptor._process(method(page), page, processors)

        return wraps(method)(processed)


@overload
def field(
    method: _FieldMethod[_PageT, _ReturnT],
    *,
    cached: bool = False,
    meta: dict | None = None,
    out: list[Callable] | None = None,
) -> _FieldDescriptor[_PageT, _ReturnT]: ...


@overload
def field(
    method: None = None,
    *,
    cached: bool = False,
    meta: dict | None = None,
    out: list[Callable] | None = None,
) -> Callable[[_FieldMethod[_PageT, _ReturnT]], _FieldDescriptor[_PageT, _ReturnT]]: ...


def field(
    method: _FieldMethod[Any, Any] | None = None,
    *,
    cached: bool = False,
    meta: dict | None = None,
    out: list[Callable] | None = None,
):
    """
    Page Object method decorated with ``@field`` decorator becomes a property,
    which is then used by :class:`~.ItemPage`'s to_item() method to populate a
    corresponding item attribute.

    By default, the value is computed on each property access. Use
    ``@field(cached=True)`` to cache the property value.

    The ``meta`` parameter allows to store arbitrary information for the field,
    e.g. ``@field(meta={"expensive": True})``. This information can be later
    retrieved for all fields using the :func:`get_fields_dict` function.

    The ``out`` parameter is an optional list of field processors, which are
    functions applied to the value of the field before returning it.
    """

    if method is not None:
        # @field syntax
        res = _FieldDescriptor(method, cached=cached, meta=meta, out=out)
        update_wrapper(cast("Callable", res), method)
        return res

    # @field(...) syntax
    def decorator(
        wrapped_method: _FieldMethod[_PageT, _ReturnT],
    ) -> _FieldDescriptor[_PageT, _ReturnT]:
        return _FieldDescriptor(
            wrapped_method,
            cached=cached,
            meta=meta,
            out=out,
        )

    return decorator


def get_fields_dict(cls_or_instance) -> dict[str, FieldInfo]:
    """Return a dictionary with information about the fields defined
    for the class: keys are field names, and values are
    :class:`web_poet.fields.FieldInfo` instances.
    """
    return getattr(cls_or_instance, _FIELDS_INFO_ATTRIBUTE_READ, {})


T = TypeVar("T")


@overload
async def item_from_fields(
    obj,
    item_cls: type[T],
    *,
    skip_nonitem_fields: bool = False,
) -> T: ...


@overload
async def item_from_fields(
    obj,
    *,
    skip_nonitem_fields: bool = False,
) -> dict[str, Any]: ...


async def item_from_fields(
    obj,
    item_cls: type[T | dict[str, Any]] = dict,
    *,
    skip_nonitem_fields: bool = False,
) -> T | dict[str, Any]:
    """Return an item of ``item_cls`` type, with its attributes populated
    from the ``obj`` methods decorated with :class:`field` decorator.

    If ``skip_nonitem_fields`` is True, ``@fields`` whose names are not
    among ``item_cls`` field names are not passed to ``item_cls.__init__``.

    When ``skip_nonitem_fields`` is False (default), all ``@fields`` are passed
    to ``item_cls.__init__``, possibly causing exceptions if
    ``item_cls.__init__`` doesn't support them.
    """
    item_dict = item_from_fields_sync(obj, item_cls=dict, skip_nonitem_fields=False)
    field_names = list(item_dict.keys())
    if skip_nonitem_fields:
        field_names = _without_unsupported_field_names(item_cls, field_names)
    return item_cls(
        **{name: await ensure_awaitable(item_dict[name]) for name in field_names}
    )


@overload
def item_from_fields_sync(
    obj,
    item_cls: type[T],
    *,
    skip_nonitem_fields: bool = False,
) -> T: ...


@overload
def item_from_fields_sync(
    obj,
    *,
    skip_nonitem_fields: bool = False,
) -> dict[str, Any]: ...


def item_from_fields_sync(
    obj,
    item_cls: type[T | dict[str, Any]] = dict,
    *,
    skip_nonitem_fields: bool = False,
) -> T | dict[str, Any]:
    """Synchronous version of :func:`item_from_fields`."""
    field_names = list(get_fields_dict(obj))
    if skip_nonitem_fields:
        field_names = _without_unsupported_field_names(item_cls, field_names)
    return item_cls(**{name: getattr(obj, name) for name in field_names})


def _without_unsupported_field_names(
    item_cls: type, field_names: list[str]
) -> list[str]:
    item_field_names = ItemAdapter.get_field_names_from_class(item_cls)
    if item_field_names is None:  # item_cls doesn't define field names upfront
        return field_names[:]
    return list(set(field_names) & set(item_field_names))
