.. _input-validation:

================
Input validation
================

Sometimes the data that your page object receives as input may be invalid.

You can define a ``validate_input`` method in a page object class to check its
input data and determine how to handle invalid input.

``validate_input`` is called on the first execution of ``ItemPage.to_item()``
or the first access to a :ref:`field <fields>`. In both cases validation
happens early; in the case of fields, it happens before field evaluation.

``validate_input`` is a synchronous method that expects no parameters, and its
outcome may be any of the following:

-   Return ``None``, indicating that the input is valid.

.. _retries-input:

-   Raise :exc:`~web_poet.exceptions.Retry`, indicating that the input
    looks like the result of a temporary issue, and that trying to fetch
    similar input again may result in valid input.

    See also :ref:`retries-additional-requests`.

-   Raise :exc:`~web_poet.exceptions.UseFallback`, indicating that the
    page object does not support the input, and that an alternative parsing
    implementation should be tried instead.

    For example, imagine you have a page object for website commerce.example,
    and that commerce.example is built with a popular e-commerce web framework.
    You could have a generic page object for products of websites using that
    framework, ``FrameworkProductPage``, and a more specific page object for
    commerce.example, ``EcommerceExampleProductPage``. If
    ``EcommerceExampleProductPage`` cannot parse a product page, but it looks
    like it might be a valid product page, you would raise
    :exc:`~web_poet.exceptions.UseFallback` to try to parse the same product
    page with ``FrameworkProductPage``, in case it works.

    .. note:: web-poet does not dictate how to define or use an alternative
              parsing implementation as fallback. It is up to web-poet
              frameworks to choose how they implement fallback handling.

-   Return an item to override the output of the ``to_item`` method and of
    fields.

    For input not matching the expected type of data, returning an item that
    indicates so is recommended.

    For example, if your page object parses an e-commerce product, and the
    input data corresponds to a list of products rather than a single product,
    you could return a product item that somehow indicates that it is not a
    valid product item, such as ``Product(is_valid=False)``.

For example:

.. code-block:: python

   def validate_input(self):
       if self.css('.product-id::text') is not None:
           return
       if self.css('.http-503-error'):
           raise Retry()
       if self.css('.product'):
           raise UseFallback()
       if self.css('.product-list'):
           return Product(is_valid=False)

You may use fields in your implementation of the ``validate_input`` method, but
only synchronous fields are supported. For example:

.. code-block:: python

   class Page(WebPage[Item]):
       def validate_input(self):
           if not self.name:
               raise UseFallback()

       @field(cached=True)
       def name(self):
           return self.css(".product-name ::text")

.. tip:: :ref:`Cache fields <field-caching>` used in the ``validate_input``
         method, so that when they are used from ``to_item`` they are not
         evaluated again.

If you implement a custom ``to_item`` method, as long as you are inheriting
from :class:`~web_poet.pages.ItemPage`, you can enable input validation
decorating your custom ``to_item`` method it with
:func:`web_poet.util.validate_input`:

.. code-block:: python

    from web_poet import validate_input

    class Page(ItemPage[Item]):
        @validate_input
        async def to_item(self):
            ...

:exc:`~web_poet.exceptions.Retry` and :exc:`~web_poet.exceptions.UseFallback`
may also be raised from the ``to_item`` method. This could come in handy, for
example, if after you execute some asynchronous code, such as an
:ref:`additional request <additional-requests>`, you find out that you need to
retry the original request or use a fallback.


Input Validation Exceptions
===========================

.. autoexception:: web_poet.exceptions.PageObjectAction

.. autoexception:: web_poet.exceptions.Retry

.. autoexception:: web_poet.exceptions.UseFallback
