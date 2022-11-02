========
web-poet
========

.. warning:: web-poet is in early stages of development; backward-incompatible
             changes are possible.

.. include:: ../README.rst
   :start-after: intro starts
   :end-before: intro ends

web-poet provides :ref:`an API and best practices to write web data extraction
code <page-objects>`, and :ref:`a specification to write implementations for
that API <frameworks>`, like scrapy-poet_.

.. _scrapy-poet: https://scrapy-poet.readthedocs.io

The main idea is to separate the extraction logic from all other concerns.
``web-poet`` Page Objects `don't do I/O <https://sans-io.readthedocs.io>`_,
and they're not dependent on any particular framework like Scrapy_.

If web scraping code is written as web-poet Page Objects, it can be reused
in different contexts. For example, such code can be developed in an
`IPython notebook`_, then tested in isolation, and then plugged
into a Scrapy_ spider, or used as a part of some custom aiohttp_-based
web scraping framework.

.. _aiohttp: https://github.com/aio-libs/aiohttp
.. _IPython notebook: https://jupyter.org/
.. _Scrapy: https://scrapy.org/

.. include:: ../README.rst
   :start-after: install starts
   :end-before: install ends

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
