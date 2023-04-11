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

Best practices for item types
=============================

To keep your code maintainable, we recommend you to:

-   Reuse item types.

    For example, if you want to extract product details data from 2 e-commerce
    websites, try to use the same item type for both of them. Or at least try
    to define a base item type with shared fields, and only keep
    website-specific fields in website-specific items.

-   Keep item types as logic-free as possible.

    For example, any parsing and field cleanup logic is better handled through
    :ref:`page object classes <page-object-classes>`, e.g. using :ref:`field
    processors <field-processors>`.

If you are looking for ready-made item types, check out `zyte-common-items`_.

.. _zyte-common-items: https://zyte-common-items.readthedocs.io/en/latest/index.html
