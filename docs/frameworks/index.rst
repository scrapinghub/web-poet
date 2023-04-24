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

A web-poet framework must support building a :ref:`page object <page-objects>`
given a page object class.

It must be able to build :ref:`input objects <inputs>` for a page object based
on type hints on the page object class, i.e. dependency injection, and
additional input data required by those input objects, such as a target URL or
a dictionary of :ref:`page parameters <page-params>`.

You can implement dependency injection with the andi_ library, which handles
signature inspection, :data:`~typing.Optional` and :data:`~typing.Union`
annotations, as well as indirect dependencies. For practical examples, see the
source code of scrapy-poet_ and of the :mod:`web_poet.example` module.

.. _andi: https://github.com/scrapinghub/andi
.. _scrapy-poet: https://github.com/scrapinghub/scrapy-poet


Additional features
===================

To provide a better experience to your users, consider extending your web-poet
framework further to:

-   Support as many input classes from the :mod:`web_poet.page_inputs`
    module as possible.

-   Support returning a :ref:`page object <page-objects>` given a target URL
    and a desired :ref:`output item type <items>`, determining the right
    :ref:`page object class <page-object-classes>` to use based on :ref:`rules
    <framework-rules>`.

-   Allow users to request an :ref:`output item <items>` directly, instead of
    requesting a page object just to call its ``to_item`` method.

    If you do, consider supporting both synchronous and asynchronous
    definitions of the ``to_item`` method, e.g. using
    :func:`~.ensure_awaitable`.

-   Support :ref:`additional requests <framework-additional-requests>`.

-   Support :ref:`retries <framework-retries>`.

-   Let users set their own :class:`~web_poet.rules.RulesRegistry` object.
