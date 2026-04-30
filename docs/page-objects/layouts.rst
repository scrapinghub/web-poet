.. _layouts:

=======
Layouts
=======

Some websites serve multiple layouts for the same type of page.

For example, a product page may have different layouts for different product
categories, and web-sites sometimes undergo A-B tests where the same page can
have multiple variations.

In these cases, a good approach is to define one :ref:`page object
<page-objects>` per layout, and then define a main page object that picks the
right layout for the current response.

To avoid writing field-forwarding boilerplate in the main page object, use the
:func:`~web_poet.layout_switch` decorator.

Basic usage
===========

With :func:`~web_poet.layout_switch`, your main page object:

- declares layout page objects as :ref:`inputs <inputs>`, and
- defines a switch method that returns the selected layout page object.

For example:

.. literalinclude:: code-examples/layouts.py

Field forwarding rules
======================

By default, :func:`~web_poet.layout_switch` forwards fields based on the output
item type field names.

This means that for item classes with declared fields (for example attrs,
dataclasses, or pydantic models), the forwarded field set matches the item
schema.

For each forwarded field:

- if the selected layout defines the field, that layout field is used, and
- if the selected layout does not define the field, a same-name field in the
  main page object is used as fallback.

For output item types that do not expose field names (for example ``dict``),
pass layout classes explicitly:

.. code-block:: python

    @layout_switch(layouts=[ProductLayoutA, ProductLayoutB])
    @attrs.define
    class ProductPage(ItemPage[dict]): ...

When ``layouts`` is provided, :func:`~web_poet.layout_switch` forwards the
union of fields defined across those layout classes.
