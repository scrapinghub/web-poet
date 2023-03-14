.. _items:

=====
Items
=====

The ``to_item`` method of a :ref:`page object class <page-object-classes>` must
return an item.

An item is a data container object supported by the itemadapter_ library.
Because itemadapter_ allows implementing support for arbitrary types, any kind
of Python object can potentially work as an item.

.. _itemadapter: https://github.com/scrapy/itemadapter


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

To define a base class that subclasses :class:`~web_poet.pages.ItemPage` or
:class:`~web_poet.pages.WebPage` but does not define an actual output item
class either, use :data:`~web_poet.pages.ItemT` as its output item class:

.. code-block:: python

   from web_poet.pages import ItemT


   class BasePage(WebPage[ItemT]):
       ...

If you have a subclass of :class:`~web_poet.pages.ItemPage` or
:class:`~web_poet.pages.WebPage` that *does* declare an output item class, and
you wish to create a subclass of it that changes the output item class, use
the :class:`~web_poet.pages.Returns` mixin to re-declare its output item class:

.. code-block:: python

   from web_poet import Returns


   class ParentPage(WebPage[ParentItem]):
       ...

   class ChildPage(ParentPage, Returns[ChildItem]):
       ...
