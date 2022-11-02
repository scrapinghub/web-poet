========
web-poet
========

.. warning::

    web-poet is in early stages of development; backwards incompatible
    changes are possible.

``web-poet`` implements Page Object pattern for web scraping.
It defines a standard for writing web data extraction code, which allows
the code to be portable & reusable.

The main idea is to separate the extraction logic from all other concerns.
``web-poet`` Page Objects `don't do I/O <https://sans-io.readthedocs.io>`_,
and they're not dependent on any particular framework like Scrapy_.

This allows the code written using ``web-poet`` to be testable and reusable.
For example, one can write a web-poet Page Object in an IPython notebook,
plug it into a Scrapy spider, write tests for them using unittest or pytest,
and then reuse in a simple script which uses ``requests`` library.

To install it, run ``pip install web-poet``. It requires Python 3.7+.
:ref:`license` is BSD 3-clause.

If you want to quickly learn how to write web-poet Page Objects,
see :ref:`intro-tutorial`. To understand better all the ``web-poet`` concepts
and the motivation behind ``web-poet``, start with :ref:`from-ground-up`.

.. toctree::
   :caption: Getting started
   :maxdepth: 1

   intro/tutorial
   intro/from-ground-up

.. toctree::
   :caption: Writing page objects
   :maxdepth: 1

   page-objects/additional-requests
   page-objects/fields
   page-objects/rules
   page-objects/retries
   page-objects/page-params

.. toctree::
   :caption: Writing frameworks
   :maxdepth: 1

   Additional Requests <frameworks/additional-requests>
   Retries <frameworks/retries>

.. toctree::
   :caption: Reference
   :maxdepth: 1

   api-reference
   contributing
   changelog
   license

.. _web-poet: https://github.com/scrapinghub/web-poet
.. _Scrapy: https://scrapy.org/
.. _scrapy-poet: https://github.com/scrapinghub/scrapy-poet

