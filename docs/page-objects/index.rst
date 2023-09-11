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

-   Subclasses :class:`~web_poet.pages.ItemPage`.

-   Declares :ref:`typed input parameters <inputs>` in its ``__init__`` method.

-   Uses :ref:`fields <fields>`.

    Alternatively, you can implement a ``to_item`` method, which can be
    synchronous or asynchronous, and returns the webpage content as an
    :ref:`item <items>`.

For example:

.. literalinclude:: code-examples/itempage.py

.. note:: ``MyItem`` in the code examples of this page is a placeholder for an
          :ref:`item class <items>`.


Minimizing boilerplate
----------------------

There are a few ways for you to minimize boilerplate when defining a page
object class.

For example, you can use attrs_ to remove the need for a custom ``__init__``
method:

.. _attrs: https://www.attrs.org/en/stable/index.html

.. literalinclude:: code-examples/attrs.py

If your page object class needs
:class:`~web_poet.page_inputs.http.HttpResponse` as input, there is also
:class:`~web_poet.pages.WebPage`, an :class:`~web_poet.pages.ItemPage` subclass
that declares an :class:`~web_poet.page_inputs.http.HttpResponse` input and
provides helper methods to use it:

.. literalinclude:: code-examples/webpage.py


.. _output-item:

Getting the output item
=======================

You should :ref:`include your page object classes into a page object
registry <rules>`, e.g. decorate them with :func:`~.handle_urls`:

.. literalinclude:: code-examples/register.py

Then, provided your page object class code is imported (see
:func:`~web_poet.rules.consume_modules`), your :ref:`framework <frameworks>`
can build the output item after you provide the target URL and the desired
:ref:`output item class <items>`, as :ref:`shown in the tutorial
<tutorial-create-page-object>`.

Your framework chooses the right page object class based on your input
parameters, downloads the required data, builds a page object, and calls the
``to_item`` method of that page object.

Note that, while the examples above use :class:`dict` as an output item for
simplicity, using less generic :ref:`item classes <items>` is recommended. That
way, you can use different page object classes, with different output items,
for the same website.

Getting a page object
---------------------

Alternatively, frameworks can return a page object instead of an item, and you
can call ``to_item`` yourself.

However, there are drawbacks to this approach:

-   ``to_item`` can be synchronous or asynchronous, so you need to use
    :func:`~web_poet.utils.ensure_awaitable`:

    .. code-block:: python

       from web_poet.utils import ensure_awaitable

       item = await ensure_awaitable(foo_page.to_item())

-   ``to_item`` may raise certain exceptions, like
    :exc:`~web_poet.exceptions.core.Retry` or
    :exc:`~web_poet.exceptions.core.UseFallback`, which, depending on your
    :ref:`framework <frameworks>`, may not be handled automatically when
    getting a page object instead of an item.


Building a page object manually
-------------------------------

It is possible to create a page object from a page object class passing its
inputs as parameters. For example, to manually create an instance of the
``FooPage`` page object class defined above:

.. literalinclude:: code-examples/raw-create.py

However, your code will break if the page object class changes its :ref:`inputs
<inputs>`. Building page objects using :ref:`frameworks  <frameworks>` prevents
that.
