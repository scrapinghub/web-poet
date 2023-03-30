.. _page-objects:

============
Page objects
============

A page object is a code wrapper for a webpage, or for a part of a webpage, that
implements the logic to parse the raw webpage data into structured data.

To use web-poet, :ref:`define page object classes <page-object-classes>` for
your target websites, and :ref:`get the output item <output-item>` using a
:ref:`web-poet framework <frameworks>`.

.. _page-object-classes:

Defining a page object class
============================

A page object class is a Python class that:

-   Subclasses :class:`~web_poet.pages.Injectable` or is registered or
    decorated with :class:`Injectable.register
    <web_poet.pages.Injectable.register>`.

    .. note:: :class:`~web_poet.pages.Injectable` is the bare minimum a class
              must inherit to be considered a page object class. However, in
              practice, most page objects should inherit from
              :class:`~web_poet.pages.ItemPage` instead to enjoy most web-poet
              features, like :ref:`fields <fields>` or :ref:`input validation
              <input-validation>`.

-   Declares :ref:`typed input parameters <inputs>` in its ``__init__`` method.

-   Implements a ``to_item`` method, which can be synchronous or asynchronous,
    and returns the webpage content as an :ref:`item <items>`.

For example:

.. literalinclude:: page.py


Minimizing boilerplate
----------------------

There are a few ways for you to minimize boilerplate when defining a page
object class.

For example, you can use attrs_ to remove the need for a custom ``__init__``
method:

.. _attrs: https://www.attrs.org/en/stable/index.html

.. literalinclude:: attrs.py

Also, it is often best to subclass :class:`~web_poet.pages.ItemPage`, which
subclasses :class:`~web_poet.pages.Injectable` and provides an implementation of the
``to_item`` method based on :ref:`declared fields <fields>`:

.. literalinclude:: itempage.py

If your page object class needs :class:`~web_poet.page_inputs.HttpResponse` as
input, there is also :class:`~web_poet.pages.WebPage`, an
:class:`~web_poet.pages.ItemPage` subclass that declares an
:class:`~web_poet.page_inputs.HttpResponse` input and provides helper methods
to use it:

.. literalinclude:: webpage.py


.. _output-item:

Getting the output item
=======================

You should :ref:`include your page object classes into a page object
registry <rules-intro>`, e.g. decorate them with :func:`~.handle_urls`:

.. literalinclude:: register.py

Then, provided your page object class code is imported (see
:func:`~web_poet.rules.consume_modules`), your :ref:`framework <frameworks>`
can build the output item after you provide the required input, such as the
target URL and the desired :ref:`output item class <items>`, as :ref:`shown in
the tutorial <tutorial-create-page-object>`.

Your framework chooses the right page object class based on your input
parameters, downloads the required data, builds a page object, and calls the
``to_item`` method of that page object. All transparently to you.

Getting a page object
---------------------

Alternatively, frameworks can return a page object instead of an item, and you
can call ``to_item`` yourself.

However, there are drawbacks to this approach:

-   How you call ``to_item`` depends on whether the method is synchronous or
    asynchronous:

    -   If the ``to_item`` method is synchronous:

        .. code-block:: python

           item = foo_page.to_item()

    -   If the ``to_item`` method is asynchronous:

        .. code-block:: python

           item = await foo_page.to_item()

    This also means that, if the underlying page object class ever switches its
    implementation from synchronous to asynchronous or the other way around,
    your code will stop working.

-   ``to_item`` may raise a :exc:`~web_poet.exceptions.core.Retry` exception
    which, depending on your :ref:`framework <frameworks>`, may not be handled
    automatically when getting a page object instead of an item.


Building a page object manually
-------------------------------

While not recommended, it is possible to create a page object from a page
object class passing its inputs as parameters. For example, to manually create
an instance of the ``FooPage`` page object class defined above:

.. literalinclude:: raw-create.py
