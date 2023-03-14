.. _spec:

=======================
Framework specification
=======================

The role of web-poet is to define a standard on how to write the extraction
logic for a webpage, and allow it to be reused in different web scraping
frameworks.

:ref:`Page objects <page-objects>` should be flexible enough to be used with:

* synchronous or asynchronous frameworks, callback-based and
  ``async def / await`` based,
* single-node and distributed systems,
* different underlying HTTP implementations - or without HTTP support
  at all, etc.

To support web-poet in a web scraping framework, you need to:

-   Support returning a :ref:`page object <page-objects>` based on a given
    target URL and a desired :ref:`output item type <items>`.

    To do that:

    -   Use ``web_poet.default_registry`` to determine the right :ref:`page
        object class <page-object-classes>` to use.

        Optionally, let users indicate their own
        :class:`~web_poet.rules.RulesRegistry` object.

    -   Support building :ref:`input objects <inputs>` based on type hints,
        i.e. dependency injection.

        You must support all input classes from the :mod:`web_poet.page_inputs`
        module.

        You can use the andi_ library for that. For practical examples, see the
        source code of scrapy-poet_ and of the :mod:`web_poet.example` module.

        .. _andi: https://github.com/scrapinghub/andi
        .. _scrapy-poet: https://github.com/scrapinghub/scrapy-poet

        In addition to signature inspection, andi_ it also handles
        :class:`~typing.Optional` and :class:`~typing.Union` annotations, and
        indirect dependencies.

-   Support returning an :ref:`output item <items>` directly, instead of
    requiring users to call the ``to_item`` method on their own.

    Mind that ``to_item`` may be a synchronous or asynchronous method, and you
    must support both scenarios.

-   Follow the specifications for the handling of :ref:`additional requests
    <framework-additional-requests>` and :ref:`retries <framework-retries>`.
