========
web-poet
========

.. image:: https://img.shields.io/pypi/v/web-poet.svg
   :target: https://pypi.python.org/pypi/web-poet
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/web-poet.svg
   :target: https://pypi.python.org/pypi/web-poet
   :alt: Supported Python Versions

.. image:: https://travis-ci.com/scrapinghub/web-poet.svg?branch=master
   :target: https://travis-ci.com/scrapinghub/web-poet
   :alt: Build Status

.. image:: https://codecov.io/github/scrapinghub/web-poet/coverage.svg?branch=master
   :target: https://codecov.io/gh/scrapinghub/web-poet
   :alt: Coverage report

.. image:: https://readthedocs.org/projects/web-poet/badge/?version=latest
   :target: https://web-poet.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

``web-poet`` implements Page Object pattern for web scraping.
It defines a standard for writing web data extraction code, which allows
the code to be portable & reusable.

License is BSD 3-clause.

Installation
============

::

    pip install web-poet

It requires Python 3.6+.

Overview
========

web-poet is a library which defines a standard on how to write and organize
web data extraction code.

If web scraping code is written as web-poet Page Objects, it can be reused
in different contexts. For example, such code can be developed in an
IPython notebook, then tested in isolation, and then plugged
into a Scrapy spider, or used as a part of some custom aiohttp-based
web scraping framework.

Currently the following integrations are available:

* Scrapy, via scrapy-poet_

See Documentation_ for more.

.. _scrapy-poet: https://github.com/scrapinghub/scrapy-poet
.. _Documentation: https://web-poet.readthedocs.io/en/latest/
