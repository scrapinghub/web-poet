.. _framework:

==================
Built-in framework
==================

:mod:`web_poet.framework` is a built-in :ref:`web-poet framework <frameworks>`
for simple use cases.

It is designed to be easy to use for quick proof-of-concepts, simple scripts,
and for generating test fixtures. It can also serve as a reference
implementation for framework authors.

Limitations
===========

The main limitation of the built-in framework is that it is not a complete
scraping framework like :doc:`Scrapy <scrapy:index>`, which can support
web-poet thanks to :doc:`scrapy-poet <scrapy-poet:index>`.

As a web-poet framework, the built-in framework also lacks support for
:ref:`custom input classes <custom-inputs>`, :exc:`~web_poet.exceptions.Retry`
and :exc:`~web_poet.exceptions.UseFallback`.

Installation
============

To use :mod:`web_poet.framework`, install the ``framework`` extra:

.. code-block:: bash

    pip install web-poet[framework]

For :ref:`browser support <framework-browser>`, you also need to `install at
least 1 browser with Playwright
<https://playwright.dev/python/docs/browsers#install-browsers>`__. For example,
to install the main browsers:

.. code-block:: bash

    playwright install

Basic use
=========

.. code-block:: python

    from dataclasses import dataclass
    from web_poet import WebPage
    from web_poet.framework import Framework
    from web_poet.utils import ensure_awaitable


    @dataclass
    class Book:
        title: str


    class BookPage(WebPage[Book]):
        @field
        def title(self) -> str:
            return self.response.css("h1::text").get()


    framework = Framework()
    item = await framework.get_item("https://books.example.com/book/1", BookPage)

    # Or, if you prefer, get a page object first.
    page = await framework.get_page("https://books.example.com/book/1", BookPage)
    item = await ensure_awaitable(page.to_item())

Choosing a page object class automatically
==========================================

If you decorate your page object classes with :func:`~web_poet.handle_urls` and
make sure they are imported, e.g. with :func:`~web_poet.consume_modules`, you
can pass :meth:`~web_poet.framework.Framework.get_item` an item class, and let
it determine which page object class to use:

.. code-block:: python

    from dataclasses import dataclass
    from web_poet import WebPage, handle_urls
    from web_poet.framework import Framework


    @dataclass
    class Book:
        title: str


    @handle_urls("books.example.com")
    class BookPage(WebPage[Book]):
        @field
        def title(self) -> str:
            return self.response.css("h1::text").get()


    framework = Framework()
    item = await framework.get_item("https://books.example.com/book/1", Book)

.. _framework-browser:

Browser
=======

The built-in framework can use `Playwright
<https://playwright.dev/python/docs/library>`_ to resolve browser dependencies
like :class:`~web_poet.page_inputs.browser.BrowserHtml` or
:class:`~web_poet.page_inputs.browser.BrowserResponse`.

Chromium is used by default. You can override that by passing
``default_browser`` to :class:`~web_poet.framework.Framework`. Page objects can also
annotate their browser dependencies with :func:`~web_poet.framework.browser` to
specify which browser they require. For example:

.. code-block:: python

    from typing import Annotated

    from web_poet import WebPage, Item
    from web_poet.page_inputs.browser import BrowserResponse
    from web_poet.framework import browser


    class MyPageObject(WebPage[Item]):
        response = Annotated[BrowserResponse, browser("firefox")]

Stats
=====

The built-in framework supports :class:`~web_poet.page_inputs.stats.Stats`.

By default, :class:`~web_poet.framework.Framework` creates a
:class:`~web_poet.page_inputs.stats.DictStatCollector` object, exposes it to
any page object that requests :class:`~web_poet.page_inputs.stats.Stats`, and
exposes that object as the :data:`stats <web_poet.framework.Framework.stats>`
attribute of the framework:

.. code-block:: python

    from web_poet.framework import Framework

    framework = Framework()
    item1 = await framework.get_item("http://example.com/book/1", BookPage)
    item2 = await framework.get_item("http://example.com/book/2", BookPage)
    all_stats = framework.stats

:class:`~web_poet.framework.Framework` also supports passing a custom stats
collector:

.. code-block:: python

    from web_poet.page_inputs.stats import StatCollector


    class MyStatCollector(StatCollector): ...


    framework = Framework(stats=MyStatCollector())
