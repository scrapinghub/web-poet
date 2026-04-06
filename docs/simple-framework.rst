.. _simple_framework:

================
Simple framework
================

:mod:`web_poet.simple_framework` is a simple, built-in :ref:`web-poet framework
<frameworks>` for sime use cases.

It is designed to be easy to use for quick proof-of-concepts, simple scripts,
and for generating test fixtures. It can also serve as a reference
implementation for framework authors.

It is not a complete scraping framework like :doc:`scrapy <scrapy:index>`,
though, which supports web-poet with :doc:`scrapy-poet <scrapy-poet:index>`.

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

Browser support
===============

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
