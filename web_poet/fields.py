"""
``web_poet.fields`` is a module with helpers for defining Page Objects.
It allows to define Page Objects in the following way:

.. code-block:: python

    from web_poet import ItemPage, field, item_from_fields


    class MyPage(ItemWebPage):
        @field
        def name(self):
            return self.response.css(".name").get()

        @field
        def price(self):
            return self.response.css(".price").get()

        @field
        def currency(self):
            return "USD"

        async def to_item(self):
            return await item_from_fields(self)

"""
from functools import update_wrapper
from typing import Dict, Optional

import attrs
from itemadapter import ItemAdapter

from web_poet.utils import cached_method, ensure_awaitable

_FIELDS_INFO_ATTRIBUTE = "_web_poet_fields_info"


@attrs.define
class FieldInfo:
    name: str
    meta: Optional[dict] = None


def field(method=None, *, cached: bool = False, meta: Optional[dict] = None):
    """
    Page Object method decorated with ``@field`` decorator becomes a property,
    which is used by :func:`item_from_fields` or :func:`item_from_fields_sync`
    to populate item attributes.

    By default, the value is computed on each property access.
    Use ``@field(cached=True)`` to cache the property value.

    The ``meta`` parameter allows to store arbitrary information for the field, 
    e.g. ``@field(meta={"expensive": True})``. This information can be later 
    retrieved for all fields using the :func:`fields_dict` function.
    """

    class _field:
        def __init__(self, method):
            if not callable(method):
                raise TypeError(f"@field decorator must be used on methods, {method!r} is decorated instead")
            if cached:
                self.unbound_method = cached_method(method)
            else:
                self.unbound_method = method

        def __set_name__(self, owner, name):
            if not hasattr(owner, _FIELDS_INFO_ATTRIBUTE):
                setattr(owner, _FIELDS_INFO_ATTRIBUTE, {})

            field_info = FieldInfo(name=name, meta=meta)
            getattr(owner, _FIELDS_INFO_ATTRIBUTE)[name] = field_info

        def __get__(self, instance, owner=None):
            return self.unbound_method(instance)

    if method is not None:
        # @field syntax
        res = _field(method)
        update_wrapper(res, method)
        return res
    else:
        # @field(...) syntax
        return _field


def fields_dict(cls_or_instance) -> Dict[str, FieldInfo]:
    """Return a dictionary with information about the fields defined
    for the class"""
    return getattr(cls_or_instance, _FIELDS_INFO_ATTRIBUTE, {})


async def item_from_fields(obj, item_cls=dict, *, item_cls_fields=False):
    """Return an item of ``item_cls`` type, with its attributes populated
    from the ``obj`` methods decorated with :class:`field` decorator.

    If ``item_cls_fields`` is True, ``@fields`` whose names don't match
    any of the ``item_cls`` attributes are not passed to ``item_cls.__init__``.
    When ``item_cls_fields`` is False (default), all ``@fields`` are passed
    to ``item_cls.__init__``.
    """
    item_dict = item_from_fields_sync(obj, item_cls=dict, item_cls_fields=False)
    field_names = item_dict.keys()
    if item_cls_fields:
        field_names = _without_unsupported_field_names(item_cls, field_names)
    return item_cls(**{name: await ensure_awaitable(item_dict[name]) for name in field_names})


def item_from_fields_sync(obj, item_cls=dict, *, item_cls_fields=False):
    """Synchronous version of :func:`item_from_fields`."""
    field_names = list(fields_dict(obj))
    if item_cls_fields:
        field_names = _without_unsupported_field_names(item_cls, field_names)
    return item_cls(**{name: getattr(obj, name) for name in field_names})


def _without_unsupported_field_names(item_cls, field_names):
    item_field_names = ItemAdapter.get_field_names_from_class(item_cls)
    if item_field_names is None:  # item_cls doesn't define field names upfront
        return field_names[:]
    return list(set(field_names) & set(item_field_names))
