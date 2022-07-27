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
from types import MethodType

from web_poet.utils import cached_method, maybe_await


def field(method=None, *, cached=False):
    """
    Page Object methods decorated with ``@field`` decorator
    are called by :func:`item_from_fields` or :func:`item_from_fields_sync`
    to populate item attributes.

    Use ``@field(cached=True)`` to cache the method result.
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
            if not hasattr(owner, "_auto_item_fields"):
                # dict is used instead of set to preserve the insertion order
                owner._auto_item_fields = {}
            owner._auto_item_fields[name] = True

        def __get__(self, instance, owner=None):
            return MethodType(self.unbound_method, instance)

    if method is not None:
        # @field syntax
        res = _field(method)
        update_wrapper(res, method)
        return res
    else:
        # @field(...) syntax
        return _field


async def item_from_fields(obj, item_cls=dict):
    """Return an item of ``item_cls`` type, with its attributes populated
    from the ``obj`` methods decorated with :class:`field` decorator.
    """
    data = item_from_fields_sync(obj, item_cls=dict)
    return item_cls(**{name: await maybe_await(value) for name, value in data.items()})


def item_from_fields_sync(obj, item_cls=dict):
    """Synchronous version of :func:`item_from_fields`."""
    field_names = getattr(obj, "_auto_item_fields", {})
    return item_cls(**{name: getattr(obj, name)() for name in field_names})
