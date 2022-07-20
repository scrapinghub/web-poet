"""
Module with helpers for defining Page Objects. It allows to define Page Objects
in the following way:

.. code-block: python

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
from types import MethodType

from web_poet.utils import maybe_await


class field:
    """
    Page Object methods decorated with ``field`` decorator
    are called by :func:`item_from_fields` or :func:`item_from_fields_sync`
    to populate item attributes.
    """

    def __init__(self, meth):
        # fixme: validation?
        self.meth = meth

    def __set_name__(self, owner, name):
        if not hasattr(owner, "_auto_item_fields"):
            # dict is used instead of set to preserve the insertion order
            owner._auto_item_fields = {}
        owner._auto_item_fields[name] = True

    def __get__(self, obj, objtype=None):
        return MethodType(self.meth, obj)


async def item_from_fields(obj, item_cls=dict):
    """Return an item of ``item_cls`` type, with its attributes populated
    from the ``obj`` methods decorated with :class:`field` decorator.
    """
    data = item_from_fields_sync(obj, item_cls=dict)
    return item_cls(**{name: await maybe_await(value) for name, value in data.items()})


def item_from_fields_sync(obj, item_cls=dict):
    """Synchronous version of :func:`item_from_fields`."""
    return item_cls(**{name: getattr(obj, name)() for name in getattr(obj, "_auto_item_fields", {})})
