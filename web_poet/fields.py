"""
``web_poet.fields`` is a module with helpers for putting extraction logic
into separate Page Object methods / properties.
"""
import inspect
from contextlib import suppress
from functools import update_wrapper, wraps
from typing import (
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    MutableMapping,
    Optional,
    Type,
    TypeVar,
)

import attrs
from itemadapter import ItemAdapter

from web_poet.utils import cached_method, ensure_awaitable

_FIELDS_INFO_ATTRIBUTE_READ = "_web_poet_fields_info"
_FIELDS_INFO_ATTRIBUTE_WRITE = "_web_poet_fields_info_temp"


def _fields_template():
    return {"enabled": {}, "disabled": {}}


@attrs.define
class FieldInfo:
    """Information about a field"""

    #: name of the field
    name: str

    #: field metadata
    meta: Optional[dict] = None

    #: field processors
    out: Optional[List[Callable]] = None

    #: when set to ``True``, the field is not populated on ``.to_item()`` calls.
    disabled: bool = False


class FieldsMixin:
    """A mixin which is required for a class to support fields"""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # To support fields, we must ensure that fields dict is not shared
        # between subclasses, i.e. a decorator in a subclass doesn't affect
        # the base class. This is done by making decorator write to a
        # temporary location, and then merging it all on subclass creation.
        this_class_fields = getattr(
            cls, _FIELDS_INFO_ATTRIBUTE_WRITE, _fields_template()
        )
        base_class_fields = getattr(
            cls, _FIELDS_INFO_ATTRIBUTE_READ, _fields_template()
        )
        if base_class_fields or this_class_fields:
            enabled = {**base_class_fields["enabled"], **this_class_fields["enabled"]}
            for name in this_class_fields["disabled"]:
                if name in enabled:
                    del enabled[name]

            disabled = {
                **base_class_fields["disabled"],
                **this_class_fields["disabled"],
            }
            for name in base_class_fields["disabled"]:
                if name in enabled:
                    del disabled[name]

            setattr(
                cls,
                _FIELDS_INFO_ATTRIBUTE_READ,
                {"enabled": enabled, "disabled": disabled},
            )
            with suppress(AttributeError):
                delattr(cls, _FIELDS_INFO_ATTRIBUTE_WRITE)


def field(
    method=None,
    *,
    cached: bool = False,
    meta: Optional[dict] = None,
    out: Optional[List[Callable]] = None,
    disabled: bool = False,
):
    """
    Page Object method decorated with ``@field`` decorator becomes a property,
    which is then used by :class:`~.ItemPage`'s to_item() method to populate
    a corresponding item attribute.

    By default, the value is computed on each property access.
    Use ``@field(cached=True)`` to cache the property value.

    The ``meta`` parameter allows to store arbitrary information for the field,
    e.g. ``@field(meta={"expensive": True})``. This information can be later
    retrieved for all fields using the :func:`get_fields_dict` function.

    The ``out`` parameter is an optional list of field processors, which are
    functions applied to the value of the field before returning it.
    """

    class _field:
        def __init__(self, method):
            if not callable(method):
                raise TypeError(
                    f"@field decorator must be used on methods, {method!r} is decorated instead"
                )
            method = self._processed(method)
            if cached:
                self.unbound_method = cached_method(method)
            else:
                self.unbound_method = method

        def __set_name__(self, owner, name):
            if not hasattr(owner, _FIELDS_INFO_ATTRIBUTE_WRITE):
                setattr(owner, _FIELDS_INFO_ATTRIBUTE_WRITE, _fields_template())

            field_info = FieldInfo(name=name, meta=meta, out=out, disabled=disabled)
            switch = "disabled" if disabled else "enabled"
            getattr(owner, _FIELDS_INFO_ATTRIBUTE_WRITE)[switch][name] = field_info

        def __get__(self, instance, owner=None):
            return self.unbound_method(instance)

        @staticmethod
        def _process(value):
            for processor in out:
                value = processor(value)
            return value

        def _processed(self, method):
            """Returns a wrapper for method that calls processors on its result"""
            if not out:
                return method
            if inspect.iscoroutinefunction(method):

                async def processed(*args, **kwargs):
                    return self._process(await method(*args, **kwargs))

            else:

                def processed(*args, **kwargs):
                    return self._process(method(*args, **kwargs))

            return wraps(method)(processed)

    if method is not None:
        # @field syntax
        res = _field(method)
        update_wrapper(res, method)
        return res
    else:
        # @field(...) syntax
        return _field


def get_fields_dict(
    cls_or_instance, include_disabled: bool = False
) -> Dict[str, FieldInfo]:
    """Return a dictionary with information about the fields defined
    for the class: keys are field names, and values are
    :class:`web_poet.fields.FieldInfo` instances.
    """
    fields_info = getattr(
        cls_or_instance, _FIELDS_INFO_ATTRIBUTE_READ, _fields_template()
    )
    fields_dict = {}
    fields_dict.update(fields_info["enabled"])
    if include_disabled:
        fields_dict.update(fields_info["disabled"])
    return fields_dict


T = TypeVar("T")
UnknownFieldActions = Literal["ignore", "warn", "raise"]


# FIXME: type is ignored as a workaround for https://github.com/python/mypy/issues/3737
# inference works properly if a non-default item_cls is passed; for dict
# it's not working (return type is Any)
async def item_from_fields(
    obj,
    item_cls: Type[T] = dict,  # type: ignore[assignment]
    *,
    skip_nonitem_fields: bool = False,
    field_names: Optional[Iterable[str]] = None,
) -> T:
    """Return an item of ``item_cls`` type, with its attributes populated
    from the ``obj`` methods decorated with :class:`field` decorator.

    If ``skip_nonitem_fields`` is True, ``@fields`` whose names are not
    among ``item_cls`` field names are not passed to ``item_cls.__init__``.

    When ``skip_nonitem_fields`` is False (default), all ``@fields`` are passed
    to ``item_cls.__init__``, possibly causing exceptions if
    ``item_cls.__init__`` doesn't support them.
    """
    item_dict = item_from_fields_sync(
        obj,
        item_cls=dict,
        skip_nonitem_fields=False,
        field_names=field_names,
    )
    if field_names is None:
        field_names = list(item_dict.keys())
    if skip_nonitem_fields:
        field_names = _without_unsupported_field_names(item_cls, field_names)
    return item_cls(
        **{name: await ensure_awaitable(item_dict[name]) for name in field_names}
    )


def item_from_fields_sync(
    obj,
    item_cls: Type[T] = dict,  # type: ignore[assignment]
    *,
    skip_nonitem_fields: bool = False,
    field_names: Optional[Iterable[str]] = None,
) -> T:
    """Synchronous version of :func:`item_from_fields`."""
    if field_names is None:
        field_names = list(get_fields_dict(obj))
        if skip_nonitem_fields:
            field_names = _without_unsupported_field_names(item_cls, field_names)
    return item_cls(**{name: getattr(obj, name) for name in field_names})


def _without_unsupported_field_names(
    item_cls: type, field_names: Iterable[str]
) -> List[str]:
    item_field_names = ItemAdapter.get_field_names_from_class(item_cls)
    if item_field_names is None:  # item_cls doesn't define field names upfront
        return list(field_names)
    return list(set(field_names) & set(item_field_names))


@attrs.define
class SelectFields:
    """This is used as a dependency in a page object to control which fields it
    would populate the item class that it returns.
    """

    #: Fields that the page object would use to populate its item class. It's a
    #: mapping of field names to boolean values to where ``True`` would indicate
    #: it being included in ``.to_item()`` calls.
    fields: Optional[MutableMapping[str, bool]] = None

    #: Controls what happens when encountering an unknown field. For example,
    #: an unknown field was passed and the page object doesn't recognize it.
    #:
    #: Setting it to ``"raise"`` would raise an :class:`AttributeError`,
    #: ``"warn"`` produces a :class:`UserWarning`, while ``"ignore"`` does nothing.
    on_unknown_field: UnknownFieldActions = "raise"
