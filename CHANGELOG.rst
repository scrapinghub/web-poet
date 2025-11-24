=========
Changelog
=========

0.21.0 (unreleased)
-------------------

* Added :class:`~web_poet.pages.BrowserPage` page object class to work with
  :class:`~web_poet.page_inputs.browser.BrowserResponse`.

0.20.0 (2025-10-28)
-------------------

* Added support for Python 3.14.

* Added support for :class:`~.BrowserResponse`, :class:`~.AnyResponse` and
  :class:`~.BrowserHtml` dependencies to the :ref:`testing framework
  <web-poet-testing>`.

* Explicitly re-export public names.

0.19.2 (2025-08-22)
-------------------

* Fixed runtime resolving of type annotations for some types.

0.19.1 (2025-08-13)
-------------------

* Improved type annotations.

0.19.0 (2025-06-06)
-------------------

* Removed some deprecated code:

  * The ``web_poet.overrides`` module is removed.
  * The ``ItemWebPage``, ``OverrideRule`` and ``PageObjectRegistry`` classes
    are removed.
  * The ``from_override_rules()`` class method and the ``get_overrides()`` and
    ``search_overrides()`` methods of :class:`~web_poet.rules.RulesRegistry`
    are removed.
  * The ``overrides`` parameter of
    :meth:`~web_poet.rules.RulesRegistry.handle_urls` is removed.
  * The ``RequestUrl`` and ``ResponseUrl`` classes can no longer be imported
    from ``web_poet.page_inputs.http``.

* :ref:`Tests <web-poet-testing>` now support items with
  :class:`~web_poet.page_inputs.url.RequestUrl` and
  :class:`~web_poet.page_inputs.url.ResponseUrl` objects.

* Improved the :ref:`pytest plugin <web-poet-testing-pytest>`:

    * Pytest ≥ 7.0.0 is now required.
    * Tests within a test case can now be run individually.
    * Tests are now compatible with `vscode-python`_.

    .. _vscode-python: https://github.com/microsoft/vscode-python

* Fixed an error of :func:`~web_poet.pages.is_injectable` with
  :class:`~types.GenericAlias` on Python ≤ 3.10.

0.18.0 (2025-01-30)
-------------------

* Removed support for Python 3.8, added support for Python 3.13.
* The minimum required version of :doc:`url-matcher <url-matcher:index>`
  changed from ``0.2.0`` to ``0.4.0``.
* ``type(None)`` is no longer considered injectable.
* Added :meth:`RulesRegistry.top_rules_for_item()
  <web_poet.rules.RulesRegistry.top_rules_for_item>`.

0.17.1 (2024-10-11)
-------------------

* :attr:`web_poet.mixins.SelectableMixin.selector` is now created with the
  ``base_url`` value set to ``self.url`` if this attribute exists.
* Added a mention of the :doc:`form2request library <form2request:index>` to
  the :class:`~.HttpRequest` documentation.
* CI improvements.

0.17.0 (2024-03-04)
-------------------

* Now requires ``andi >= 0.5.0``.
* Package requirements that were unversioned now have minimum versions
  specified.
* Added support for Python 3.12.
* Added support for ``typing.Annotated`` dependencies to the serialization and
  testing code.
* Documentation improvements.
* CI improvements.

0.16.0 (2024-01-23)
-------------------

* Added new :class:`~.AnyResponse` which holds either :class:`~.BrowserResponse`,
  or :class:`~.HttpResponse`.
* Documentation improvements.

0.15.1 (2023-11-21)
-------------------

* ``HttpRequestHeaders`` now has a ``from_bytes_dict`` class method, like
  ``HttpResponseHeaders``.

0.15.0 (2023-09-11)
-------------------

* A new dependency, :class:`~.Stats`, has been added. It allows storing
  key-value data pairs for different purposes. See :ref:`stats`.

0.14.0 (2023-08-03)
-------------------

* Dropped Python 3.7 support.
* Now requires ``packaging >= 20.0``.
* Fixed detection of the :class:`~.Returns` base class.
* Improved docs.
* Updated type hints.
* Updated CI tools.

0.13.1 (2023-05-30)
-------------------

* Fixed an issue with :class:`~.HttpClient` which happens when a response with
  a non-standard status code is received.

0.13.0 (2023-05-30)
-------------------

* A new dependency :class:`~.BrowserResponse` has been added. It contains a
  browser-rendered page URL, status code and HTML.
* The :ref:`rules` documentation section has been rewritten.

0.12.0 (2023-05-05)
-------------------

* The :ref:`testing framework <web-poet-testing>` now allows defining a
  :ref:`custom item adapter <web-poet-testing-adapters>`.
* We have made a backward-incompatible change on test fixture serialization:
  the ``type_name`` field of exceptions has been renamed to ``import_path``.
* Fixed built-in Python types, e.g. ``int``, not working as :ref:`field
  processors <field-processors>`.

0.11.0 (2023-04-24)
-------------------

* JMESPath_ support is now available: you can use :meth:`.WebPage.jmespath` and
  :meth:`.HttpResponse.jmespath` to run queries on JSON responses.
* The testing framework now supports page objects that raise exceptions from
  the ``to_item`` method.

.. _JMESPath: https://jmespath.org/

0.10.0 (2023-04-19)
-------------------

* New class :class:`~.Extractor` can be used for easier extraction of nested
  fields (see :ref:`default-processors-nested`).
* Exceptions raised while getting a response for an additional request are now
  saved in :ref:`test fixtures <web-poet-testing-additional-requests>`.
* Multiple documentation improvements and fixes.
* Add a ``twine check`` CI check.

0.9.0 (2023-03-30)
------------------

* Standardized :ref:`input validation <input-validation>`.
* :ref:`Field processors <field-processors>` can now also be defined through a
  nested ``Processors`` class, so that field redefinitions in subclasses can
  inherit them. See :ref:`default-processors`.
* :ref:`Field processors <field-processors>` can now opt in to receive the page
  object whose field is being read.
* :class:`web_poet.fields.FieldsMixin` now keeps fields from all base classes
  when using multiple inheritance.
* Fixed the documentation build.


0.8.1 (2023-03-03)
------------------

* Fix the error when calling :meth:`.to_item() <web_poet.pages.ItemPage.to_item>`,
  :func:`item_from_fields_sync() <web_poet.fields.item_from_fields_sync>`, or
  :func:`item_from_fields() <web_poet.fields.item_from_fields>` on page objects
  defined as slotted attrs classes, while setting ``skip_nonitem_fields=True``.


0.8.0 (2023-02-23)
------------------

This release contains many improvements to the web-poet testing framework,
as well as some other improvements and bug fixes.

Backward-incompatible changes:

* :func:`~.cached_method` no longer caches exceptions for ``async def`` methods.
  This makes the behavior the same for sync and async methods, and also makes
  it consistent with Python's stdlib caching (i.e. :func:`functools.lru_cache`,
  :func:`functools.cached_property`).
* The testing framework now uses the ``HttpResponse-info.json`` file name instead
  of ``HttpResponse-other.json`` to store information about HttpResponse
  instances. To make tests generated with older web-poet work, rename
  these files on disk.

Testing framework improvements:

* Improved test reporting: better diffs and error messages.
* By default, the pytest plugin now generates a test per item attribute
  (see :ref:`web-poet-testing-pytest`). There is also an option
  (``--web-poet-test-per-item``) to run a test per item instead.
* Page objects with the :class:`~.HttpClient` dependency are now supported
  (see :ref:`web-poet-testing-additional-requests`).
* Page objects with the :class:`~.PageParams` dependency are now supported.
* Added a new ``python -m web_poet.testing rerun`` command
  (see :ref:`web-poet-testing-tdd`).
* Fixed support for nested (indirect) dependencies in page objects.
  Previously they were not handled properly by the testing
  framework.
* Non-ASCII output is now stored without escaping in the test fixtures,
  for better readability.

Other changes:

* Testing and CI fixes.
* Fixed a packaging issue: ``tests`` and ``tests_extra`` packages were
  installed, not just ``web_poet``.


0.7.2 (2023-02-01)
------------------

* Restore the minimum version of ``itemadapter`` from 0.7.1 to 0.7.0, and
  prevent a similar issue from happening again in the future.


0.7.1 (2023-02-01)
------------------

* Updated the :ref:`tutorial <tutorial>` to cover recent features and focus on
  best practices. Also, a new module was added, :mod:`web_poet.example`, that
  allows using page objects while following the tutorial.

* :ref:`web-poet-testing` now covers :ref:`Git LFS <git-lfs>` and
  :ref:`scrapy-poet <web-poet-testing-scrapy-poet>`, and recommends
  ``python -m pytest`` instead of ``pytest``.

* Improved the warning message when duplicate ``ApplyRule`` objects are found.

* ``HttpResponse-other.json`` content is now indented for better readability.

* Improved test coverage for :ref:`fields <fields>`.


0.7.0 (2023-01-18)
------------------

* Add :ref:`a framework for creating tests and running them with pytest
  <web-poet-testing>`.

* Support implementing fields in mixin classes.

* Introduce new methods for :class:`web_poet.rules.RulesRegistry`:

    * :meth:`web_poet.rules.RulesRegistry.add_rule`
    * :meth:`web_poet.rules.RulesRegistry.overrides_for`
    * :meth:`web_poet.rules.RulesRegistry.page_cls_for_item`

* Improved the performance of :meth:`web_poet.rules.RulesRegistry.search` where
  passing a single parameter of either ``instead_of`` or ``to_return`` results
  in *O(1)* look-up time instead of *O(N)*. Additionally, having either
  ``instead_of`` or ``to_return`` present in multi-parameter search calls would
  filter the initial candidate results resulting in a faster search.

* Support :ref:`page object dependency serialization <dep-serialization>`.

* Add new dependencies used in testing and serialization code: ``andi``,
  ``python-dateutil``, and ``time-machine``. Also ``backports.zoneinfo`` on
  non-Windows platforms when the Python version is older than 3.9.


0.6.0 (2022-11-08)
------------------

In this release, the ``@handle_urls`` decorator gets an overhaul; it's not
required anymore to pass another Page Object class to
``@handle_urls("...", overrides=...)``.

Also, the ``@web_poet.field`` decorator gets support for output processing
functions, via the ``out`` argument.

Full list of changes:

* **Backwards incompatible** ``PageObjectRegistry`` is no longer supporting
  dict-like access.

* Official support for Python 3.11.

* New ``@web_poet.field(out=[...])`` argument which allows to set output
  processing functions for web-poet fields.

* The ``web_poet.overrides`` module is deprecated and replaced with
  ``web_poet.rules``.

* The ``@handle_urls`` decorator is now creating ``ApplyRule`` instances
  instead of ``OverrideRule`` instances; ``OverrideRule`` is deprecated.
  ``ApplyRule`` is similar to ``OverrideRule``, but has the following differences:

    * ``ApplyRule`` accepts a ``to_return`` parameter, which should be the data
      container (item) class that the Page Object returns.
    * Passing a string to ``for_patterns`` would auto-convert it into
      ``url_matcher.Patterns``.
    * All arguments are now keyword-only except for ``for_patterns``.

* New signature and behavior of ``handle_urls``:

    * The ``overrides`` parameter is made optional and renamed to
      ``instead_of``.
    * If defined, the item class declared in a subclass of
      ``web_poet.ItemPage`` is used as the ``to_return`` parameter of
      ``ApplyRule``.
    * Multiple ``handle_urls`` annotations are allowed.

* ``PageObjectRegistry`` is replaced with ``RulesRegistry``; its API is changed:

    * **backwards incompatible** dict-like API is removed;
    * **backwards incompatible** *O(1)* lookups using
      ``.search(use=PagObject)`` has become *O(N)*;
    * ``search_overrides`` method is renamed to ``search``;
    * ``get_overrides`` method is renamed to ``get_rules``;
    * ``from_override_rules`` method is deprecated;
      use ``RulesRegistry(rules=...)`` instead.

* Typing improvements.
* Documentation, test, and warning message improvements.

Deprecations:

* The ``web_poet.overrides`` module is deprecated. Use ``web_poet.rules`` instead.
* The ``overrides`` parameter from ``@handle_urls`` is now deprecated.
  Use the ``instead_of`` parameter instead.
* The ``OverrideRule`` class is now deprecated. Use ``ApplyRule`` instead.
* ``PageObjectRegistry`` is now deprecated. Use ``RulesRegistry`` instead.
* The ``from_override_rules`` method of ``PageObjectRegistry`` is now deprecated.
  Use ``RulesRegistry(rules=...)`` instead.
* The ``PageObjectRegistry.get_overrides`` method is deprecated.
  Use ``PageObjectRegistry.get_rules`` instead.
* The ``PageObjectRegistry.search_overrides`` method is deprecated.
  Use ``PageObjectRegistry.search`` instead.

0.5.1 (2022-09-23)
------------------

* The BOM encoding from the response body is now read before the response
  headers when deriving the response encoding.
* Minor typing improvements.

0.5.0 (2022-09-21)
------------------

Web-poet now includes a mini-framework for organizing extraction code
as Page Object properties::

    import attrs
    from web_poet import field, ItemPage

    @attrs.define
    class MyItem:
        foo: str
        bar: list[str]


    class MyPage(ItemPage[MyItem]):
        @field
        def foo(self):
            return "..."

        @field
        def bar(self):
            return ["...", "..."]

**Backwards incompatible changes**:

* ``web_poet.ItemPage`` is no longer an abstract base class which requires
  ``to_item`` method to be implemented. Instead, it provides a default
  ``async def to_item`` method implementation which uses fields marked as
  ``web_poet.field`` to create an item. This change shouldn't affect the
  user code in a backwards incompatible way, but it might affect typing.

Deprecations:

* ``web_poet.ItemWebPage`` is deprecated. Use ``web_poet.WebPage`` instead.

Other changes:

* web-poet is declared as PEP 561 package which provides typing information;
  mypy is going to use it by default.
* Documentation, test, typing and CI improvements.

0.4.0 (2022-07-26)
------------------

* New ``HttpResponse.urljoin`` method, which take page's base url in account.
* New ``HttpRequest.urljoin`` method.
* standardized ``web_poet.exceptions.Retry`` exception, which allows
  to initiate a retry from the Page Object, e.g. based on page content.
* Documentation improvements.

0.3.0 (2022-06-14)
------------------

* Backwards Incompatible Change:

    * ``web_poet.requests.request_backend_var``
      is renamed to ``web_poet.requests.request_downloader_var``.

* Documentation and CI improvements.

0.2.0 (2022-06-10)
------------------

* Backward Incompatible Change:

    * ``ResponseData`` is replaced with ``HttpResponse``.

      ``HttpResponse`` exposes methods useful for web scraping
      (such as xpath and css selectors, json loading),
      and handles web page encoding detection. There are also new
      types like ``HttpResponseBody`` and ``HttpResponseHeaders``.

* Added support for performing additional requests using
  ``web_poet.HttpClient``.
* Introduced ``web_poet.BrowserHtml`` dependency
* Introduced ``web_poet.PageParams`` to pass arbitrary information
  inside a Page Object.
* Added ``web_poet.handle_urls`` decorator, which allows to declare which
  websites should be handled by the page objects. Lower-level
  ``PageObjectRegistry`` class is also available.
* removed support for Python 3.6
* added support for Python 3.10

0.1.1 (2021-06-02)
------------------

* ``base_url`` and ``urljoin`` shortcuts

0.1.0 (2020-07-18)
------------------

* Documentation
* WebPage, ItemPage, ItemWebPage, Injectable and ResponseData are available
  as top-level imports (e.g. ``web_poet.ItemPage``)

0.0.1 (2020-04-27)
------------------

Initial release.
