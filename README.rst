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

.. intro starts

``web-poet`` is a Python 3.7+ implementation of the `page object pattern`_ for
web scraping. It enables writing portable, reusable web data extraction code.

.. _page object pattern: https://martinfowler.com/bliki/PageObject.html

.. intro ends

See the documentation_.

.. _documentation: https://web-poet.readthedocs.io

Installation
============

.. install starts

To install web-poet, run:

.. code-block:: bash

    pip install web-poet

.. install ends


Developing
==========

Setup your local Python environment via:

1. `pip install -r requirements-dev.txt`
2. `pre-commit install`

Now everytime you perform a `git commit`, these tools will run against the
staged files:

* `black`
* `isort`
* `flake8`

You can also directly invoke `pre-commit run --all-files` or `tox -e linters`
to run them without performing a commit.
