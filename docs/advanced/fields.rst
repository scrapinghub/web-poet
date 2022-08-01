.. _web-poet-fields:

======
Fields
======

Background
----------

It is common for Page Objects not to put all the extraction code to the
``to_item()`` method, but create properties or methods to extract
individual attributes, a method or property per attribute:

.. code-block:: python

    import attrs
    from web_poet import ItemPage, HttpResponse


    @attrs.define
    class MyPage(ItemPage):
        response: HttpResponse

        @property
        def name(self):
            return self.response.css(".name").get()

        @property
        def price(self):
            return self.response.css(".price").get()

        def to_item(self) -> dict:
            return {
                'name': self.name,
                'price': self.price
            }

This approach has 2 main advantages:

1. Often the code looks cleaner this way, it's easier to follow.
2. The resulting page object becomes more flexible and reusable:
   if not all data extracted in the ``to_item()`` method is needed,
   user can use properties for individual attributes. It's
   more efficient than running ``to_item()`` and only using some of the
   result.

However, writing and maintaining ``to_item()`` method can get tedious,
especially if there is a lot of properties.

web_poet.fields
---------------

To aid writing Page Objects in this style, ``web-poet`` provides
a few utilities:

* :func:`@web_poet.field <web_poet.fields.field>` decorator,
* :func:`web_poet.item_from_fields <web_poet.fields.item_from_fields>`
  and :func:`web_poet.item_from_fields_sync <web_poet.fields.item_from_fields_sync>`
  functions.

We can rewrite the example like this:

.. code-block:: python

    import attrs
    from web_poet import ItemPage, HttpResponse, field, item_from_fields_sync


    @attrs.define
    class MyPage(ItemPage):
        response: HttpResponse

        @field
        def name(self):
            return self.response.css(".name").get()

        @field
        def price(self):
            return self.response.css(".price").get()

        def to_item(self) -> dict:
            return item_from_fields_sync(self)

Methods annotated with :func:`@field <web_poet.fields.field>` decorator
become properties; for ``page = MyPage(...)`` instance
you can access them as ``page.name``.

As you can guess, :func:`~.item_from_fields_sync` uses all the properties
created with :func:`@field <web_poet.fields.field>` decorator, and returns
a dict with the result, where keys are method names, and values are
property values.

Asynchronous fields
-------------------

``async def`` fields are also supported, as well as a mix of
sync and async methods - use :func:`~.item_from_fields` in ``to_item``
to make it work.

For example, you might need to send :ref:`advanced-requests` to extract some
of the attributes:

.. code-block:: python

    import attrs
    from web_poet import ItemPage, HttpResponse, HttpClient, field, item_from_fields


    @attrs.define
    class MyPage(ItemPage):
        response: HttpResponse
        http_client: HttpClient

        @field
        def name(self):
            return self.response.css(".name").get()

        @field
        async def price(self):
            resp = self.http_client.get("...")
            return resp.json()['price']

        async def to_item(self) -> dict:
            return await item_from_fields(self)

Because :func:`~.item_from_fields` supports both sync and async fields,
it's recommended to use it over :func:`~.item_from_fields_sync`, even
if there are no async fields yet. The only reason to use
:func:`~.item_from_fields_sync` would be to avoid using
``async def to_item`` method.

If you want to get a value of an async field, make sure to await it:

.. code-block:: python

    page = MyPage(...)
    price = await page.price

Using Page Objects with async fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to a Page Object with async fields without calling its
``to_item`` method, make sure to await the field when needed, and
not await it when that's not needed:

.. code-block:: python

    page = MyPage(...)
    name = page.name
    price = await page.price

This is not ideal, because now the code which needs to use a page object
must be aware if a field is sync or async. If a field needs to be changed
from being sync to ``async def`` (or the other way around),
e.g. because of a website change, all the code which uses this page
object must be updated.

One approach to solve it is to always define all fields as ``async def``.
It works, but it makes the page objects harder to use in non-async environments.

Instead of doing this, you can also use :func:`~.ensure_awaitable` utility
function when accessing the fields:

.. code-block:: python

    from web_poet.utils import ensure_awaitable

    page = MyPage(...)
    name = await ensure_awaitable(page.name)
    price = await ensure_awaitable(page.price)

Now any field can be converted from sync to async, or the other way around,
and the code would keep working.

Item classes
------------

Structured items
~~~~~~~~~~~~~~~~

In all previous examples, ``to_item`` methods are returning ``dict``
instances. It is common to use item classes (e.g. dataclasses or
attrs instances) instead of unstructured dicts to hold the data:

.. code-block:: python

    import attrs
    from web_poet import ItemPage, HttpResponse

    @attrs.define
    class Item:
        name: str
        price: str


    @attrs.define
    class MyPage(ItemPage):
        # ...
        def to_item(self) -> Item:
            return Item(
                name=self.name,
                price=self.price
            )

:mod:`web_poet.fields` supports it, by allowing to pass an item class to the
:func:`~.item_from_fields` / :func:`~.item_from_fields_sync` functions:

.. code-block:: python

    @attrs.define
    class MyPage(ItemPage):
        # ...

        async def to_item(self) -> Item:
            return await item_from_fields(self, item_cls=Item)

Error prevention
~~~~~~~~~~~~~~~~

This approach plays particularly well with the
:func:`@field <web_poet.fields.field>` decorator, preventing some of the errors,
which may happen if results are plain "dicts".

Consider the following badly written page object:

.. code-block:: python

    import attrs
    from web_poet import ItemPage, HttpResponse, field, item_from_fields

    @attrs.define
    class Item:
        name: str
        price: str


    @attrs.define
    class MyPage(ItemPage):
        response: HttpResponse

        @field
        def nane(self):
            return self.response.css(".name").get()

        async def to_item(self) -> Item:
            return await item_from_fields(self, item_cls=Item)

Because Item class is used, a typo ("nane" instead of "name") is detected
at runtime: creation of Item instance would fail with a ``TypeError``, because
of unexpected keyword argument "nane".

After fixing it (renaming "nane" method to "name"), another error is going to be
detected: ``price`` argument is required, but there is no extraction method for
this attribute, so ``Item.__init__`` will raise another ``TypeError``,
indicating that a required argument is missing.

Without an Item class, none of these errors are detected.

Defining an Item class may be an overkill if you only have a single Page Object,
but item classes are of a great help when

* you need to extract data in the same format from multiple websites, or
* if you want to define the schema upfront.

Changing Item type
~~~~~~~~~~~~~~~~~~

Let's say there is a Page Object implemented, which outputs some standard
item. Maybe there is a library of such Page Objects available. But for a
particular project we might want to output an item of a different type:

* some attributes of the standard item may be not needed;
* there might be a need to implement extra attributes, which are not
  available in the standard item;
* names of attributes might be different.

There are a few ways to approach it. For example, if items are very
different, you might use the original Page Object as a dependency:

.. code-block:: python

    import attrs
    from my_library import FooPage, StandardItem
    from web_poet import ItemPage, ensure_awaitable

    @attrs.define
    class CustomItem:
        new_name: str
        new_price: str

    @attrs.define
    class CustomFooPage(ItemPage):
        response: HttpResponse
        standard: FooPage

        @field
        async def new_name(self):
            orig_name = await ensure_awaitable(self.standard.name)
            orig_brand = await ensure_awaitable(self.standard.brand)
            return f"{orig_brand}: {orig_name}"

        @field
        async def new_price(self):
            # ...

        async def to_item(self) -> CustomItem:
            return await item_from_fields(self, item_cls=CustomItem)

However, in many cases the items are quite similar, and share many of
the attributes. The easiest case is an addition of a new field; you can do
it like this:

.. code-block:: python

    @attrs.define
    class CustomItem(StandardItem):
        new_field: str

    @attrs.define
    class CustomFooPage(FooPage):

        @field
        def new_field(self) -> str:
            # ...

        async def to_item(self) -> CustomItem:
            # we need to override to_item to ensure CustomItem is returned
            return await item_from_fields(self, item_cls=CustomItem)

Removing fields (as well as renaming) is more tricky. The caveat is that
by default :func:`item_from_fields` uses all fields defined as ``@field``
to produce an item, passing all these values to ``Item.__init__``.

But if you follow the previous example, and inherit from the "base",
"standard" Page Object, there could be a ``@field`` which is not present
in then ``CustomItem``. It'd be passed to ``CustomItem.__init__``, causing
an exception.

To solve it, you can use ``item_cls_fields=True`` argument
of :func:`item_from_fields`. When this parameter is True, ``@fields`` which
are not defined in the item are skipped.

.. code-block:: python

    @attrs.define
    class CustomItem(Item):
        # let's pick only 1 attribute from StandardItem, nothing more
        name: str

    @attrs.define
    class CustomFooPage(FooPage):
        # inheriting from a page object which defines all StandardItem fields

        async def to_item(self) -> CustomItem:
            return await item_from_fields(self, item_cls=CustomItem,
                                          item_cls_fields=True)

Here CustomFooPage only uses ``name`` field of the ``FooPage``, ignoring
all other fields defined in ``FooPage``, because ``name`` is the only
field ``CustomItem`` supports.

To recap:

* Use ``item_cls_fields=False`` (default) when your Page Object corresponds
  to an item exactly, and you want to detect typos in field names even
  for optional fields.
* Use ``item_cls_fields=True`` when it's possible for the Page Object
  to contain more ``@fields`` than defined in the item class, e.g. because
  Page Object is inherited from some other base Page Object.

Caching
-------

When writing extraction code for Page Objects, it's common that several
attributes reuse some computation. For example, you might need to do
an additional request to get an API response, and then fill several
attributes from this response:

.. code-block:: python

    from web_poet import ItemPage, HttpResponse, HttpClient

    class MyPage(ItemPage):
        response: HttpResponse
        http: HttpClient

        async def to_item(self):
            api_url = self.response.css("...").get()
            api_response = await self.http.get(api_url).json()
            return {
                'name': self.response.css(".name ::text").get(),
                'price': api_response["price"],
                'sku': api_response["sku"],
            }

When converting such Page Objects to use fields, be careful not to make an
API call (or some other heavy computation) multiple times. You can do it by
extracting the heavy operation to a method, and caching the results:

.. code-block:: python

    from web_poet import ItemPage, HttpResponse, HttpClient, field, cached_method

    class MyPage(ItemPage):
        response: HttpResponse
        http: HttpClient

        @cached_method
        async def api_response(self):
            api_url = self.response.css("...").get()
            return await self.http.get(api_url).json()

        @field
        def name(self):
            return self.response.css(".name ::text").get()

        @field
        async def price(self):
            api_response = await self.api_response()
            return api_response["price"]

        @field
        async def sku(self):
            api_response = await self.api_response()
            return api_response["sku"]

        async def to_item(self):
            return await item_from_fields(self)

As you can see, ``web-poet`` provides :func:`~.cached_method` decorator,
which allows to memoize the function results. It supports both sync and
async methods, i.e. you can use it on regular methods (``def foo(self)``),
as well as on async methods (``async def foo(self)``).

The refactored example, with per-attribute fields, is more verbose than
the original one, where a single ``to_item`` method is used. However, it
provides some advantages - if only a subset of attributes is needed, then
it's possible to use the Page Object without doing unnecessary work.
For example, if user only needs ``name`` field in the example above, no
additional requests (API calls) will be made.

Sometimes you might want to cache ``field``, i.e. a property which computes an
attribute of the final item. In such cases, use ``@field(cached=True)``
decorator instead of ``@field``.

cached_method vs lru_cache vs cached_property
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're an experienced Python developer, you might wonder why is
:func:`~.cached_method` decorator needed, if Python already provides
:func:`functools.lru_cache`. For example, one can write this:

.. code-block:: python

    from functools import lru_cache
    from web_poet import ItemPage

    class MyPage(ItemPage):
        # ...
        @lru_cache
        def heavy_method(self):
            # ...

Don't do it! There are two issues with ``lru_cache``, which make it unsuitable
here:

1. It doesn't work properly on methods, because ``self`` is used as a part of the
   cache key. It means a reference to an instance is kept in the cache,
   and so created page objects are never deallocated, causing a memory leak.
2. ``lru_cache`` doesn't work on ``async def`` methods, so you can't cache
   e.g. results of API calls using ``lru_cache``.

:func:`~.cached_method` solves both of these issues. You may also use
:func:`functools.cached_property`, or an external package like async_property_
with async versions of ``@property`` and ``@cached_property`` decorators; unlike
``lru_cache``, they all work fine for this use case.

.. _async_property: https://github.com/ryananguiano/async_property