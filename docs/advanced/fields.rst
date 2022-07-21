.. _web-poet-fields:

======
Fields
======

Background
----------

It is common for Page Objects not to put all the extraction code to the
``to_item()`` method, but create properties or methods to extract
individual attributes, a method per attribute:

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
sync and async methods. For example, you might use :ref:`advanced-requests`
to extract some of the attributes:

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
            return item_from_fields(self)

Because :func:`~.item_from_fields` supports both sync and async extraction
methods, it's recommended to use over :func:`~.item_from_fields_sync`, even
if there are no async extraction methods yet.

Item clasess
------------

In previous examples, ``to_item`` methods are returning ``dict``
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

web_poet.fields support it, by allowing to pass an item class to the
:func:`~.item_from_fields` / :func:`~.item_from_fields_sync` functions:

.. code-block:: python

    @attrs.define
    class MyPage(ItemPage):
        # ...

        async def to_item(self) -> Item:
            return item_from_fields(self, item_cls=Item)


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
            return item_from_fields(self, item_cls=Item)

Because Item class is used, a typo ("nane" instead of "name") will be detected:
creation of Item instance would fail with a ``TypeError``, because
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
