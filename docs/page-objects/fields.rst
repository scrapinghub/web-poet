.. _fields:

======
Fields
======

A field is a read-only property in a :ref:`page object class <page-objects>`
decorated with :meth:`@field <web_poet.fields.field>` instead of
:class:`@property <property>`.

Each field is named after a key of the :ref:`item <items>` that the page object
class returns. A field uses the :ref:`inputs <inputs>` of its page object class
to return the right value for the matching item key.

For example:

.. code-block:: python

    from typing import Optional

    import attrs
    from web_poet import ItemPage, HttpResponse, field


    @attrs.define
    class MyPage(ItemPage):
        response: HttpResponse

        @field
        def foo(self) -> Optional[str]:
            return self.response.css(".foo").get()

.. _fields-sync-async:

Synchronous and asynchronous fields
===================================

Fields can be either synchronous (``def``) or asynchronous (``async def``).

Asynchronous fields make sense, for example, when sending
:ref:`additional requests <additional-requests>`:

.. code-block:: python

    from typing import Optional

    import attrs
    from web_poet import ItemPage, HttpClient, HttpResponse, field


    @attrs.define
    class MyPage(ItemPage):
        response: HttpResponse
        http: HttpClient

        @field
        def name(self) -> Optional[str]:
            return self.response.css(".name").get()

        @field
        async def price(self) -> Optional[str]:
            resp = await self.http.get("...")
            return resp.json().get("price")

Unlike the values of synchronous fields, the values of asynchronous fields need
to be awaited:

.. code-block:: python

    page = MyPage(...)
    name = page.name
    price = await page.price

Mixing synchronous and asynchronous fields can be messy:

-   You need to know whether a field is synchronous or asynchronous to write
    the right code to read its value.

-   If a field changes from synchronous to asynchronous or vice versa, calls
    that read the field need to be updated.

    Changing from synchronous to asynchronous might be sometimes necessary due
    to website changes (e.g. needing :ref:`additional requests
    <additional-requests>`).

To address these issues, use :func:`~.ensure_awaitable` to read both
synchronous and asynchronous fields with the same code:

.. code-block:: python

    from web_poet.utils import ensure_awaitable

    page = MyPage(...)
    name = await ensure_awaitable(page.name)
    price = await ensure_awaitable(page.price)

.. note:: Using asynchronous fields only also works, but prevents accessing
    other fields from :ref:`field processors <field-processors>`.


.. _inheritance:

Inheritance
===========

To create a page object class that is very similar to another, subclassing the
former page object class is often a good approach to maximize code reuse.

In a subclass of a :ref:`page object class <page-objects>` you can
:ref:`reimplement fields <reimplement-field>`, :ref:`add fields <add-field>`,
:ref:`remove fields <remove-field>`, or :ref:`rename fields <rename-field>`.

.. _reimplement-field:

Reimplementing a field
----------------------

Reimplementing a field when subclassing a :ref:`page object class
<page-objects>` should be straightforward:

.. code-block:: python

    import attrs
    from web_poet import field, ensure_awaitable

    from my_library import BasePage

    @attrs.define
    class CustomPage(BasePage):

        @field
        async def foo(self) -> str:
            base_foo = await ensure_awaitable(super().foo)
            return f"{base_foo} (modified)"


.. _add-field:

Adding a field
--------------

To add a new field to a :ref:`page object class <page-objects>` when
subclassing:

#.  Define a new :ref:`item class <items>` that includes the new field, for
    example a subclass of the item class returned by the original page object
    class.

#.  In your new page object class, subclass both the original page object class
    and :class:`~.Returns`, the latter including the new item class between
    brackets.

#.  Implement the extraction code for the new :ref:`field <fields>` in the new
    page object class.

For example:

.. code-block:: python

    import attrs
    from web_poet import field, Returns

    from my_library import BasePage, BaseItem

    @attrs.define
    class CustomItem(BaseItem):
        new_field: str

    @attrs.define
    class CustomPage(BasePage, Returns[CustomItem]):

        @field
        def new_field(self) -> str:
            ...


.. _remove-field:

Removing a field
----------------

To remove a field from a :ref:`page object class <page-objects>` when
subclassing:

#.  Define a new :ref:`item class <items>` that defines all fields but the one
    being removed.

#.  In your new page object class, subclass the original page object class,
    :class:`~.Returns` with the new item class between brackets, and set
    ``skip_nonitem_fields=True``.

    When building an item, page object class fields without a matching item
    class field will now be ignored, rather than raising an exception.

Your new page object class will still define the field, but the resulting item
will not.

For example:

.. code-block:: python

    import attrs
    from web_poet import Returns

    from my_library import BasePage

    @attrs.define
    class CustomItem:
        kept_field: str

    @attrs.define
    class CustomPage(BasePage, Returns[CustomItem], skip_nonitem_fields=True):
        pass

Alternatively, you can consider :ref:`composition <composition>` for removing
fields. Composition is more verbose than subclassing, because you need to
define every field in your page object class, but it can catch some mismatches
between page object class fields and item class fields that would otherwise be
hidden by ``skip_nonitem_fields``.


.. _rename-field:

Renaming a field
----------------

To rename a field from a :ref:`page object class <page-objects>` when
subclassing:

#.  Define a new :ref:`item class <items>` that defines all fields, including
    the renamed field.

#.  In your new page object class, subclass the original page object class,
    :class:`~.Returns` with the new item class between brackets, and set
    ``skip_nonitem_fields=True``.

    When building an item, page object class fields without a matching item
    class field will now be ignored, rather than raising an exception.

#.  Define a field for the new field name that returns the value from the old
    field name.

Your new page object class will still define the old field name, but the
resulting item will not.

For example:

.. code-block:: python

    import attrs
    from web_poet import Returns

    from my_library import BasePage

    @attrs.define
    class CustomItem:
        new_field: str

    @attrs.define
    class CustomPage(BasePage, Returns[CustomItem], skip_nonitem_fields=True):

        @field
        async def new_field(self) -> str:
            return ensure_awaitable(self.old_field)

Alternatively, you can consider :ref:`composition <composition>` for renaming
fields. Composition is more verbose than subclassing, because you need to
define every field in your page object class, but it can catch some mismatches
between page object class fields and item class fields that would otherwise be
hidden by ``skip_nonitem_fields``.


.. _composition:

Composition
===========

You can reuse a page object class from another page object class using
composition instead of :ref:`inheritance <inheritance>` by using the original
page object class as a dependency in a brand new page object class returning a
brand new item class.

This is a good approach when you want to reuse code but the page object classes
are very different, or when you want to remove or rename fields without relying
on ``skip_nonitem_fields``.

For example:

.. code-block:: python

    import attrs
    from web_poet import ItemPage, field, ensure_awaitable

    from my_library import BasePage

    @attrs.define
    class CustomItem:
        name: str

    @attrs.define
    class CustomPage(ItemPage[CustomItem]):
        base: BasePage

        @field
        async def name(self) -> str:
            name = await ensure_awaitable(self.base.name)
            brand = await ensure_awaitable(self.base.brand)
            return f"{brand}: {name}"

Instead of a page object, it is possible to declare the :ref:`item <items>` it
returns as a dependency in your new page object class. For example:

.. code-block:: python

    import attrs
    from web_poet import ItemPage, field

    from my_library import BaseItem

    @attrs.define
    class CustomItem:
        name: str

    @attrs.define
    class CustomPage(ItemPage[CustomItem]):
        base: BaseItem

        @field
        def name(self) -> str:
            return f"{self.base.brand}: {self.base.name}"


This gives you the flexibility to use :ref:`rules <rules>` to set the page
object class to use when building the item. Also, item fields can be read from
synchronous methods even if the source page object fields were
:ref:`asynchronous <fields-sync-async>`.

On the other hand, all fields of the source page object class will always be
called to build the entire item, which may be a waste of resources if you only
need to access some of the item fields.


.. _field-processors:

Field processors
================

It's often needed to clean or process field values using reusable functions.
:meth:`@field <web_poet.fields.field>` takes an optional ``out`` argument with
a list of such functions. They will be applied to the field value before
returning it:

.. code-block:: python

    from web_poet import ItemPage, HttpResponse, field

    def clean_tabs(s: str) -> str:
        return s.replace('\t', ' ')

    def add_brand(s: str, page: ItemPage) -> str:
        return f"{page.brand} - {s}"

    class MyPage(ItemPage):
        response: HttpResponse

        @field(out=[clean_tabs, str.strip, add_brand])
        def name(self) -> str:
            return self.response.css(".name ::text").get() or ""

        @field(cached=True)
        def brand(self) -> str:
            return self.response.css(".brand ::text").get() or ""

.. _processor-page:

Accessing other fields from field processors
--------------------------------------------

If a processor takes an argument named ``page``, that argument will contain the
page object instance. This allows processing a field differently based on the
values of other fields.

Be careful of circular references. Accessing a field runs its processors; if
two fields reference each other, :class:`RecursionError` will be raised.

You should enable :ref:`caching <field-caching>` for fields accessed in
processors, to avoid unnecessary recomputation.

Processors can be applied to asynchronous fields, but processor functions must
be synchronous. As a result, only values of synchronous fields can be accessed
from processors through the ``page`` argument.

.. _default-processors:

Default processors
------------------

In addition to the ``out`` argument of :meth:`@field <web_poet.fields.field>`,
you can define processors at the page object class level by defining a nested
class named ``Processors``:

.. code-block:: python

    import attrs
    from web_poet import ItemPage, HttpResponse, field

    def clean_tabs(s: str) -> str:
        return s.replace('\t', ' ')

    @attrs.define
    class MyPage(ItemPage):
        response: HttpResponse

        class Processors:
            name = [clean_tabs, str.strip]

        @field
        def name(self) -> str:
            return self.response.css(".name ::text").get() or ""

If ``Processors`` contains an attribute with the same name as a field, the
value of that attribute is used as a list of default processors for the field,
to be used if the ``out`` argument of :meth:`@field <web_poet.fields.field>` is
not defined.

You can also reuse and extend the processors defined in a base class by
explicitly accessing or subclassing the ``Processors`` class:

.. code-block:: python

    import attrs
    from web_poet import ItemPage, HttpResponse, field

    def clean_tabs(s: str) -> str:
        return s.replace('\t', ' ')

    @attrs.define
    class MyPage(ItemPage):
        response: HttpResponse

        class Processors:
            name = [str.strip]

        @field
        def name(self) -> str:
            return self.response.css(".name ::text").get() or ""

    class MyPage2(MyPage):
        class Processors(MyPage.Processors):
            # name uses the processors in MyPage.Processors.name
            # description now also uses them and also clean_tabs
            description = MyPage.Processors.name + [clean_tabs]

        @field
        def description(self) -> str:
            return self.response.css(".description ::text").get() or ""

        # brand uses the same processors as name
        @field(out=MyPage.Processors.name)
        def brand(self) -> str:
            return self.response.css(".brand ::text").get() or ""

.. _default-processors-nested:

Processors for nested fields
----------------------------

Some item fields contain nested items (e.g. a product can contain a list of
variants) and it's useful to have processors for fields of these nested items.

You can use the same logic for them as for normal fields if you define an
extractor class that produces these nested items. Such classes should inherit
from :class:`~.Extractor`.

In the simplest cases you need to pass a selector to them:

.. code-block:: python

    from typing import Any, Dict, List

    import attrs
    from parsel import Selector
    from web_poet import Extractor, ItemPage, HttpResponse, field

    @attrs.define
    class MyPage(ItemPage):
        response: HttpResponse

        @field
        async def variants(self) -> List[Dict[str, Any]]:
            variants = []
            for color_sel in self.response.css(".color"):
                variant = await VariantExtractor(color_sel).to_item()
                variants.append(variant)
            return variants

    @attrs.define
    class VariantExtractor(Extractor):
        sel: Selector

        @field(out=[str.strip])
        def color(self) -> str:
            return self.sel.css(".name::text").get() or ""

In such cases you can also use :class:`~.SelectorExtractor` as a shortcut that
provides ``css()`` and ``xpath()``:

.. code-block:: python

    class VariantExtractor(SelectorExtractor):
        @field(out=[str.strip])
        def color(self) -> str:
            return self.css(".name::text").get() or ""

You can also pass other data in addition to, or instead of, selectors, such as
dictionaries with some data:

.. code-block:: python

    @attrs.define
    class VariantExtractor(Extractor):
        variant_data: dict

        @field(out=[str.strip])
        def color(self) -> str:
            return self.variant_data.get("color") or ""


.. _field-caching:

Field caching
=============

When writing extraction code for Page Objects, it's common that several
attributes reuse some computation. For example, you might need to do
an additional request to get an API response, and then fill several
attributes from this response:

.. code-block:: python

    from typing import Dict, Optional

    from web_poet import ItemPage, HttpResponse, HttpClient, validates_input

    class MyPage(ItemPage):
        response: HttpResponse
        http: HttpClient

        @validates_input
        async def to_item(self) -> Dict[str, Optional[str]]:
            api_url = self.response.css("...").get()
            api_response = await self.http.get(api_url).json()
            return {
                'name': self.response.css(".name ::text").get(),
                'price': api_response.get("price"),
                'sku': api_response.get("sku"),
            }

When converting such Page Objects to use fields, be careful not to make an
API call (or some other heavy computation) multiple times. You can do it by
extracting the heavy operation to a method, and caching the results:

.. code-block:: python

    from typing import Dict

    from web_poet import ItemPage, HttpResponse, HttpClient, field, cached_method

    class MyPage(ItemPage):
        response: HttpResponse
        http: HttpClient

        @cached_method
        async def api_response(self) -> Dict[str, str]:
            api_url = self.response.css("...").get()
            return await self.http.get(api_url).json()

        @field
        def name(self) -> str:
            return self.response.css(".name ::text").get() or ""

        @field
        async def price(self) -> str:
            api_response = await self.api_response()
            return api_response.get("price") or ""

        @field
        async def sku(self) -> str:
            api_response = await self.api_response()
            return api_response.get("sku") or ""

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
---------------------------------------------------------

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

Exception caching
-----------------

Note that exceptions are not cached - neither by :func:`~.cached_method`,
nor by `@field(cached=True)`, nor by :func:`functools.lru_cache`, nor by
:func:`functools.cached_property`.

Usually it's not an issue, because an exception is usually propagated,
and so there are no duplicate calls anyways. But, just in case, keep this
in mind.

Field metadata
==============

``web-poet`` allows to store arbitrary information for each field using the
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
================

:ref:`Input validation <input-validation>`, if used, happens before field
evaluation, and it may override the values of fields, preventing field
evaluation from ever happening. For example:

.. code-block:: python

   class Page(ItemPage[Item]):
       def validate_input(self) -> Item:
           return Item(foo="bar")

       @field
       def foo(self):
           raise RuntimeError("This exception is never raised")

    assert Page().foo == "bar"

Field evaluation may still happen for a field if the field is used in the
implementation of the ``validate_input`` method. Note, however, that only
synchronous fields can be used from the ``validate_input`` method.
