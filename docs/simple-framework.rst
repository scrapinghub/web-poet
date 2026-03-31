.. _simple_framework:

================
Simple framework
================

:mod:`web_poet.simple_framework` is a simple, built-in :ref:`web-poet framework
<frameworks>` for sime use cases.

It is designed to be easy to use for quick proof-of-concepts, simple scripts,
and for generating test fixtures. It can also serve as a reference
implementation for framework authors.

It is not a scraping framework like :doc:`scrapy-poet <scrapy-poet:index>`,
though.

Installation
============

To use :mod:`web_poet.simple_framework`, install the ``simple_framework``
extra:

.. code-block:: bash

    pip install web-poet[simple_framework]

Use
===

.. code-block:: python

    from web_poet import consume_modules
    from web_poet.simple_framework import get_item

    consume_modules("myproject.pages")
    item = get_item("http://example.com/book/1", Book)
