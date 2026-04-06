.. _simple_framework:

================
Simple framework
================

:mod:`web_poet.simple_framework` is a simple, built-in :ref:`web-poet framework
<frameworks>` for simple use cases.

It is designed to be easy to use for quick proof-of-concepts, simple scripts,
and for generating test fixtures. It can also serve as a reference
implementation for framework authors.

Limitations
===========

The main limitation of the simple framework is that it is not a complete
scraping framework like :doc:`Scrapy <scrapy:index>`, which can support
web-poet thanks to :doc:`scrapy-poet <scrapy-poet:index>`.

As a web-poet framework, the simple framework also lacks support for
:ref:`custom input classes <custom-inputs>`, :exc:`~web_poet.exceptions.Retry`
and :exc:`~web_poet.exceptions.UseFallback`.

Installation
============

To use :mod:`web_poet.simple_framework`, install the ``simple_framework``
extra:

.. code-block:: bash

    pip install web-poet[simple_framework]

For :ref:`browser support <simple-browser>`, you also need to `install at least
1 browser with Playwright
<https://playwright.dev/python/docs/browsers#install-browsers>`__. For example,
to install the main browsers:

.. code-block:: bash

    playwright install

Basic use
=========

.. code-block:: python

    from web_poet import consume_modules
    from web_poet.simple_framework import get_item, get_page
    from web_poet.utils import ensure_awaitable

    # Load your page objects.
    consume_modules("myproject.pages")

    # Get an item directly.
    item = await get_item("http://example.com/book/1", Book)

    # Or, if you prefer, get a page object first.
    page = await get_page("http://example.com/book/1", BookPage)
    item = await ensure_awaitable(page.to_item())

.. _simple-browser:

Browser
=======

The simple framework can use `Playwright
<https://playwright.dev/python/docs/library>`_ to resolve browser dependencies
like :class:`~web_poet.page_inputs.browser.BrowserHtml` or
:class:`~web_poet.page_inputs.browser.BrowserResponse`.

Chromium is used by default. You can override that with the ``default_browser``
parameter of :func:`~web_poet.simple_framework.get_item`. Page objects can also
annotate their browser dependencies with
:func:`~web_poet.simple_framework.browser` to specify which browser they
require. For example:

.. code-block:: python

    from typing import Annotated

    from web_poet import WebPage, Item
    from web_poet.page_inputs.browser import BrowserResponse
    from web_poet.simple_framework import browser


    class MyPageObject(WebPage[Item]):
        response = Annotated[BrowserResponse, browser("firefox")]

Stats
=====

The simple framework supports :class:`~web_poet.page_inputs.stats.Stats`. You
can pass an an object that implements the
:class:`~web_poet.page_inputs.stats.StatCollector` interface when calling
:func:`~web_poet.simple_framework.get_item` or
:func:`~web_poet.simple_framework.get_page` to collect stats across multiple
calls. For example:

.. code-block:: python

    from web_poet.page_inputs.stats import DictStatCollector
    from web_poet.simple_framework import get_item

    stats = DictStatCollector()
    item1 = await get_item("http://example.com/book/1", Book, stats=stats)
    item2 = await get_item("http://example.com/book/2", Book, stats=stats)
