========
web-poet
========

.. image:: https://img.shields.io/pypi/v/web-poet.svg
   :target: https://pypi.python.org/pypi/web-poet
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/web-poet.svg
   :target: https://pypi.python.org/pypi/web-poet
   :alt: Supported Python Versions

.. image:: https://github.com/scrapinghub/web-poet/actions/workflows/test.yml/badge.svg
   :target: https://github.com/scrapinghub/web-poet/actions/workflows/test.yml
   :alt: Build Status

.. image:: https://codecov.io/github/scrapinghub/web-poet/coverage.svg?branch=master
   :target: https://codecov.io/gh/scrapinghub/web-poet
   :alt: Coverage report

.. image:: https://readthedocs.org/projects/web-poet/badge/?version=stable
   :target: https://web-poet.readthedocs.io/en/stable/?badge=stable
   :alt: Documentation Status

``web-poet`` implements Page Object pattern for web scraping.
It defines a standard for writing web data extraction code, which allows
the code to be portable & reusable.

License is BSD 3-clause.

Installation
============

::

    pip install web-poet

It requires Python 3.7+.

Overview
========

web-poet is a library which defines a standard on how to write and organize
web data extraction code.

If web scraping code is written as web-poet Page Objects, it can be reused
in different contexts. For example, such code can be developed in an
`IPython notebook`_, then tested in isolation, and then plugged
into a Scrapy_ spider, or used as a part of some custom aiohttp_-based
web scraping framework.

Currently, the following integrations are available:

* Scrapy, via scrapy-poet_

See Documentation_ for more.

.. _scrapy-poet: https://github.com/scrapinghub/scrapy-poet
.. _Documentation: https://web-poet.readthedocs.io
.. _Scrapy: https://scrapy.org/
.. _aiohttp: https://github.com/aio-libs/aiohttp
.. _IPython notebook: https://jupyter.org/
