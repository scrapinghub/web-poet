.. _items:

=====
Items
=====

The ``to_item`` method of a :ref:`page object class <page-object-classes>` must
return an item.

An item is a data container object supported by the itemadapter_ library, such
as a :class:`dict`, an attrs_ class, or a :func:`~dataclasses.dataclass`
class. For example:

.. code-block:: python

   @attrs.define
   class MyItem:
       foo: int
       bar: str

.. _attrs: https://www.attrs.org/en/stable/
.. _itemadapter: https://github.com/scrapy/itemadapter

Because itemadapter_ allows implementing support for arbitrary types,
any kind of Python object can potentially work as an item.
