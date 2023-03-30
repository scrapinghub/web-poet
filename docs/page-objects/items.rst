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


ItemPage output item class
==========================

:class:`~web_poet.pages.ItemPage` and :class:`~web_poet.pages.WebPage` provide
an implementation of ``to_item`` that builds an item based on
:ref:`declared fields <fields>`.

When subclassing :class:`~web_poet.pages.ItemPage` or
:class:`~web_poet.pages.WebPage`, you can indicate between brackets the item
class that you wish the ``to_item`` method to return:

.. code-block:: python

   class MyPage(WebPage[MyItem]):
       ...

If you have a subclass of :class:`~web_poet.pages.ItemPage` or
:class:`~web_poet.pages.WebPage` that declares an output item class, and
you wish to create a subclass of it that changes the output item class, use
the :class:`~web_poet.pages.Returns` mixin to re-declare its output item class:

.. code-block:: python

   from web_poet import Returns


   class ParentPage(WebPage[ParentItem]):
       ...

   class ChildPage(ParentPage, Returns[ChildItem]):
       ...
