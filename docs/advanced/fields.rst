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

        def name(self):
            return self.response.css(".name").get()

        def price(self):
            return self.response.css(".price").get()

        def to_item(self) -> dict:
            return {
                'name': self.name(),
                'price': self.price()
            }

This approach has 2 main advantages:

1. Often the code looks cleaner this way, it's easier to follow.
2. The resulting page object becomes more flexible and reusable:
   if not all data extracted in the ``to_item()`` method is needed,
   user can call extraction methods for individual attributes. It's
   more efficient than running ``to_item()`` and only using some of the
   result.

However, writing and maintaining ``to_item()`` method can get tedious,
especially if there is a lot of extraction methods.

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


As you can guess, :func:`~.item_from_fields_sync` uses all the methods annotated
with :func:`@field <web_poet.fields.field>` decorator, and creates a dict
with the result, where keys are method names, and values are results of
calling these methods.

Asynchronous extraction methods
-------------------------------

``async def`` extraction methods are also supported, as well as a mix of
sync and async methods - use :func:`~.item_from_fields` for this.
For example, you might send :ref:`advanced-requests` to extract some
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

Because :func:`~.item_from_fields` supports both sync and async extraction
methods, it's recommended to use it over :func:`~.item_from_fields_sync`, even
if there are no async extraction methods yet. The only reason to use
:func:`~.item_from_fields_sync` would be to avoid using
``async def to_item`` method.

Item classes
------------

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
                name=self.name(),
                price=self.price()
            )

:mod:`web_poet.fields` supports it, by allowing to pass an item class to the
:func:`~.item_from_fields` / :func:`~.item_from_fields_sync` functions:

.. code-block:: python

    @attrs.define
    class MyPage(ItemPage):
        # ...

        async def to_item(self) -> Item:
            return await item_from_fields(self, item_cls=Item)


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
API call (or some other heavy computation) twice. You can do it by extracting
the heavy operation to a method, and caching the results:

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

Sometimes you might want to cache ``field``, i.e. a method which computes an
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
with async versions of `@property` and `@cached_property` decorators; unlike
``lru_cache``, they all work fine for this use case.

.. _async_property: https://github.com/ryananguiano/async_property