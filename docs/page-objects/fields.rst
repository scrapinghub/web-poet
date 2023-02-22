.. _fields:

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

@field decorator
----------------
To aid writing Page Objects in this style, ``web-poet`` provides
the :func:`@web_poet.field <web_poet.fields.field>` decorator:

.. code-block:: python

    import attrs
    from web_poet import ItemPage, HttpResponse, field


    @attrs.define
    class MyPage(ItemPage):
        response: HttpResponse

        @field
        def name(self):
            return self.response.css(".name").get()

        @field
        def price(self):
            return self.response.css(".price").get()

:class:`~.ItemPage` has a default ``to_item()``
implementation: it uses all the properties created with the
:func:`@field <web_poet.fields.field>` decorator, and returns
a dict with the result, where keys are method names, and values are
property values. In the example above, ``to_item()`` returns a
``{"name": ..., "price": ...}`` dict with the extracted data.

Methods annotated with the :func:`@field <web_poet.fields.field>` decorator
become properties; for a ``page = MyPage(...)`` instance
you can access them as ``page.name``.

It's important to note that the default
:meth:`ItemPage.to_item() <web_poet.pages.ItemPage.to_item>` implementation
is an ``async def`` function - make sure to await its result:
``item = await page.to_item()``

Asynchronous fields
-------------------

The reason :class:`~.ItemPage` provides an async ``to_item`` method by
default is that both regular and ``async def`` fields are supported.

For example, you might need to send :ref:`additional-requests` to extract some
of the attributes:

.. code-block:: python

    import attrs
    from web_poet import ItemPage, HttpResponse, HttpClient, field


    @attrs.define
    class MyPage(ItemPage):
        response: HttpResponse
        http: HttpClient

        @field
        def name(self):
            return self.response.css(".name").get()

        @field
        async def price(self):
            resp = await self.http.get("...")
            return resp.json()['price']

Using Page Objects with async fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to use a Page Object with async fields without calling its
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

Field processors
----------------

It's often needed to clean or process field values using reusable functions.
``@field`` takes an optional ``out`` argument with a list of such functions.
They will be applied to the field value before returning it:

.. code-block:: python

    from web_poet import ItemPage, HttpResponse, field

    def clean_tabs(s):
        return s.replace('\t', ' ')

    class MyPage(ItemPage):
        response: HttpResponse

        @field(out=[clean_tabs, str.strip])
        def name(self):
            return self.response.css(".name ::text").get()

Note that while processors can be applied to async fields, they need to be
sync functions themselves.

It's also possible to implement field cleaning and processing in ``to_item``
but in that case accessing a field directly will return the value without
processing, so it's preferable to use field processors instead.

.. _item-classes:

Item Classes
------------

In all previous examples, ``to_item`` methods are returning ``dict``
instances. It is common to use item classes (e.g. dataclasses or
attrs instances) instead of unstructured dicts to hold the data:

.. code-block:: python

    import attrs
    from web_poet import ItemPage, HttpResponse

    @attrs.define
    class Product:
        name: str
        price: str


    @attrs.define
    class ProductPage(ItemPage):
        # ...
        def to_item(self) -> Product:
            return Product(
                name=self.name,
                price=self.price
            )

:mod:`web_poet.fields` supports it, by allowing to parametrize
:class:`~.ItemPage` with an item class:

.. code-block:: python

    @attrs.define
    class ProductPage(ItemPage[Product]):
        # ...

When :class:`~.ItemPage` is parametrized with an item class,
its ``to_item()`` method starts to return item instances, instead
of ``dict`` instances. In the example above ``ProductPage.to_item`` method
returns ``Product`` instances.

Defining an item class may be an overkill if you only have a single Page Object,
but item classes are of a great help when

* you need to extract data in the same format from multiple websites, or
* if you want to define the schema upfront.

Error prevention
~~~~~~~~~~~~~~~~

Item classes play particularly well with the
:func:`@field <web_poet.fields.field>` decorator, preventing some of the errors,
which may happen if results are plain "dicts".

Consider the following badly written page object:

.. code-block:: python

    import attrs
    from web_poet import ItemPage, HttpResponse, field

    @attrs.define
    class Product:
        name: str
        price: str


    @attrs.define
    class ProductPage(ItemPage[Product]):
        response: HttpResponse

        @field
        def nane(self):
            return self.response.css(".name").get()

Because the ``Product`` item class is used, a typo ("nane" instead of "name")
is detected at runtime: the creation of a ``Product`` instance would fail with
a ``TypeError``, because of the unexpected keyword argument "nane".

After fixing it (renaming "nane" method to "name"), another error is going to be
detected: the ``price`` argument is required, but there is no extraction method for
this attribute, so ``Product.__init__`` will raise another ``TypeError``,
indicating that a required argument is missing.

Without an item class, none of these errors are detected.

Changing Item Class
~~~~~~~~~~~~~~~~~~~

Let's say there is a Page Object implemented, which outputs some standard
item. Maybe there is a library of such Page Objects available. But for a
particular project we might want to output an item of a different type:

* some attributes of the standard item might not be needed;
* there might be a need to implement extra attributes, which are not
  available in the standard item;
* names of attributes might be different.

There are a few ways to approach it. If items are very
different, using the original Page Object as a dependency is a good approach:

.. code-block:: python

    import attrs
    from my_library import FooPage, StandardItem
    from web_poet import ItemPage, HttpResponse, field, ensure_awaitable

    @attrs.define
    class CustomItem:
        new_name: str
        new_price: str

    @attrs.define
    class CustomFooPage(ItemPage[CustomItem]):
        response: HttpResponse
        standard: FooPage

        @field
        async def new_name(self):
            orig_name = await ensure_awaitable(self.standard.name)
            orig_brand = await ensure_awaitable(self.standard.brand)
            return f"{orig_brand}: {orig_name}"

        @field
        async def new_price(self):
            ...

However, if items are similar, and share many attributes, this approach
could lead to boilerplate code. For example, you might be extending an item
with a new field, and it'd be required to duplicate definitions for all
other fields.

Instead of using dependency injection you can make your Page Object
a subclass of the original Page Object; that's a nice way to add a new field
to the item:

.. code-block:: python

    import attrs
    from my_library import FooPage, StandardItem
    from web_poet import field, Returns

    @attrs.define
    class CustomItem(StandardItem):
        new_field: str

    @attrs.define
    class CustomFooPage(FooPage, Returns[CustomItem]):

        @field
        def new_field(self) -> str:
            # ...

Note how :class:`~.Returns` is used as one of the base classes of
``CustomFooPage``; it allows to change the item class returned by a page object.

Removing fields (as well as renaming) is a bit more tricky.

The caveat is that by default :class:`~.ItemPage` uses all fields
defined as ``@field`` to produce an item, passing all these values to
item's ``__init__`` method. So, if you follow the previous example, and
inherit from the "base", "standard" Page Object, there could be a ``@field``
from the base class which is not present in the ``CustomItem``.
It'd be still passed to ``CustomItem.__init__``, causing an exception.

One way to solve it is to make the original Page Object a dependency
instead of inheriting from it, as explained in the beginning.

Alternatively, you can use ``skip_nonitem_fields=True`` class argument - it tells
:meth:`~.ItemPage.to_item` to skip ``@fields`` which are not defined
in the item:

.. code-block:: python

    @attrs.define
    class CustomItem:
        # let's pick only 1 attribute from StandardItem, nothing more
        name: str

    class CustomFooPage(FooPage, Returns[CustomItem], skip_nonitem_fields=True):
        pass


Here, ``CustomFooPage.to_item`` only uses ``name`` field of the ``FooPage``, ignoring
all other fields defined in ``FooPage``, because ``skip_nonitem_fields=True``
is passed, and ``name`` is the only field ``CustomItem`` supports.

To recap:

* Use ``Returns[NewItemType]`` to change the item class in a subclass.
* Don't use ``skip_nonitem_fields=True`` when your Page Object corresponds
  to an item exactly, or when you're only adding fields. This is a safe
  approach, which allows to detect typos in field names, even for optional
  fields.
* Use ``skip_nonitem_fields=True`` when it's possible for the Page Object
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

As you can see, ``web-poet`` provides :func:`~.cached_method` decorator,
which allows to memoize the function results. It supports both sync and
async methods, i.e. you can use it on regular methods (``def foo(self)``),
as well as on async methods (``async def foo(self)``).

The refactored example, with per-attribute fields, is more verbose than
the original one, where a single ``to_item`` method is used. However, it
provides some advantages — if only a subset of attributes is needed, then
it's possible to use the Page Object without doing unnecessary work.
For example, if user only needs ``name`` field in the example above, no
additional requests (API calls) will be made.

Sometimes you might want to cache a ``@field``, i.e. a property which computes
an attribute of the final item. In such cases, use ``@field(cached=True)``
decorator instead of ``@field``.

``cached_method`` vs ``lru_cache`` vs ``cached_property``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Don't do it! There are two issues with :func:`functools.lru_cache`, which make
it unsuitable here:

1. It doesn't work properly on methods, because ``self`` is used as a part of the
   cache key. It means a reference to an instance is kept in the cache,
   and so created page objects are never deallocated, causing a memory leak.
2. :func:`functools.lru_cache` doesn't work on ``async def`` methods, so you
   can't cache e.g. results of API calls using :func:`functools.lru_cache`.

:func:`~.cached_method` solves both of these issues. You may also use
:func:`functools.cached_property`, or an external package like async_property_
with async versions of ``@property`` and ``@cached_property`` decorators; unlike
:func:`functools.lru_cache`, they all work fine for this use case.

.. _async_property: https://github.com/ryananguiano/async_property

Exceptions caching
~~~~~~~~~~~~~~~~~~

Note that exceptions are not cached - neither by :func:`~.cached_method`,
nor by `@field(cached=True)`, nor by :func:`functools.lru_cache`, nor by
:func:`functools.cached_property`.

Usually it's not an issue, because an exception is usually propagated,
and so there are no duplicate calls anyways. But, just in case, keep this
in mind.

Field metadata
--------------

``web-poet`` allows to store arbitrary information for each field, using
``meta`` keyword argument:

.. code-block:: python

    from web_poet import ItemPage, field

    class MyPage(ItemPage):

        @field(meta={"expensive": True})
        async def my_field(self):
            ...

To retrieve this information, use :func:`web_poet.fields.get_fields_dict`; it
returns a dictionary, where keys are field names, and values are
:class:`web_poet.fields.FieldInfo` instances.

.. code-block:: python

    from web_poet.fields import get_fields_dict

    fields_dict = get_fields_dict(MyPage)
    field_names = fields_dict.keys()
    my_field_meta = fields_dict["my_field"].meta

    print(field_names)  # dict_keys(['my_field'])
    print(my_field_meta)  # {'expensive': True}


Input validation
----------------

:ref:`Input validation <input-validation>`, if used, happens before field
evaluation, and it may override the values of fields, preventing field
evaluation from ever happening. For example:

.. code-block:: python

   class Page(ItemPage[Item]):
       def validate_input(self):
           return Item(foo="bar")

       @field
       def foo(self):
           raise RuntimeError("This exception is never raised")

    assert Page().foo == "bar"

Field evaluation may still happen for a field if the field is used in the
implementation of the ``validate_input`` method. Note, however, that only
synchronous fields can be used from the ``validate_input`` method.
