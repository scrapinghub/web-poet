.. _spec:

=======================
Framework specification
=======================

Learn how to build a :ref:`web-poet framework <frameworks>`.

Design principles
=================

:ref:`Page objects <page-objects>` should be flexible enough to be used with:

* synchronous or asynchronous code, callback-based and ``async def / await``
  based,
* single-node and distributed systems,
* different underlying HTTP implementations - or without HTTP support
  at all, etc.


Minimum requirements
====================

A web-poet framework must meet the following minimum requirements:

-   Support returning a :ref:`page object <page-objects>` given a target URL
    and a desired :ref:`output item type <items>`, using
    ``web_poet.default_registry`` to determine the right :ref:`page
    object class <page-object-classes>` to use.

-   Support building :ref:`input objects <inputs>` based on type hints, i.e.
    dependency injection.

    You can use the andi_ library for that. For practical examples, see the
    source code of scrapy-poet_ and of the :mod:`web_poet.example` module.

    .. _andi: https://github.com/scrapinghub/andi
    .. _scrapy-poet: https://github.com/scrapinghub/scrapy-poet

    In addition to signature inspection, andi_ also handles
    :class:`~typing.Optional` and :class:`~typing.Union` annotations, as well
    as indirect dependencies.


Additional features
===================

To provide a better experience to your users, consider extending your web-poet
framework further to:

-   Support as many input classes from the :mod:`web_poet.page_inputs`
    module as possible.

-   Allow users to request an :ref:`output item <items>` directly, instead of
    requesting a page object just to call its ``to_item`` method.

    If you do, consider supporting both synchronous and asynchronous
    definitions of the ``to_item`` method, e.g. using
    :func:`~.ensure_awaitable`.

-   Support :ref:`additional requests <framework-additional-requests>`.

-   Support :ref:`retries <framework-retries>`.

-   Let users set their own :class:`~web_poet.rules.RulesRegistry` object.
