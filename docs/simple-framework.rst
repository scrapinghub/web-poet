.. _simple_framework:

================
Simple framework
================

:mod:`web_poet.simple_framework` is a built-in :ref:`web-poet framework
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
    from web_poet.simple_framework import Poet
    from web_poet.utils import ensure_awaitable

    # Load your page objects.
    consume_modules("myproject.pages")

    poet = Poet()

    # Get an item directly.
    item = await poet.get_item("http://example.com/book/1", Book)

    # Or, if you prefer, get a page object first.
    page = await poet.get_page("http://example.com/book/1", BookPage)
    item = await ensure_awaitable(page.to_item())

.. _simple-browser:

Browser
=======

The simple framework can use `Playwright
<https://playwright.dev/python/docs/library>`_ to resolve browser dependencies
like :class:`~web_poet.page_inputs.browser.BrowserHtml` or
:class:`~web_poet.page_inputs.browser.BrowserResponse`.

Chromium is used by default. You can override that by passing
``default_browser`` to :class:`~web_poet.simple_framework.Poet`. Page objects
can also annotate their browser dependencies with
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

The simple framework supports :class:`~web_poet.page_inputs.stats.Stats`.

By default, :class:`~web_poet.simple_framework.Poet` creates a
:class:`~web_poet.page_inputs.stats.DictStatCollector` object, exposes it to
any page object that requests :class:`~web_poet.page_inputs.stats.Stats`, and
exposes that object as the :data:`stats <web_poet.simple_framework.Poet.stats>`
attribute of the poet:

.. code-block:: python

    from web_poet.simple_framework import Poet

    poet = Poet()
    item1 = await poet.get_item("http://example.com/book/1", Book)
    item2 = await poet.get_item("http://example.com/book/2", Book)
    all_stats = poet.stats

:class:`~web_poet.simple_framework.Poet` also supports passing a custom stats
collector:

.. code-block:: python

    from web_poet.page_inputs.stats import StatCollector


    class MyStatCollector(StatCollector): ...


    poet = Poet(stats=MyStatCollector())
