=========
Changelog
=========

TBD
---

* New ``ApplyRule`` class created by the ``@handle_urls`` decorator:

  * This is nearly identical with ``OverrideRule`` except that it's accepting
    a ``to_return`` parameter which signifies the data container class that
    the Page Object returns.
  * Passing a string to ``for_patterns`` would auto-convert it into
    ``url_matcher.Patterns``.

* Modify the call signature of ``handle_urls``:

    * New ``to_return`` parameter which signifies the data container class that
      the Page Object returns. This behaves exactly the same with ``overrides``
      but it's more consistent with the attribute names of ``ApplyRules`` that
      it creates.
    * New ``instead_of`` parameter which does the same thing with ``overrides``.
    * The old ``overrides`` parameter is not required anymore as it's set for
      deprecation.

Deprecations:

* The ``overrides`` parameter from ``@handle_urls`` is now deprecated.
  Use the ``instead_of`` parameter instead.
* ``OverrideRule`` is now deprecated. Use ``ApplyRule`` instead.
* The ``from_override_rules`` method of ``PageObjectRegistry`` is now deprecated.
  Use ``from_apply_rules`` instead.
* The ``web_poet.overrides`` is deprecated. Use ``web_poet.rules`` instead.
* The ``PageObjectRegistry.get_overrides`` is deprecated.
  Use ``PageObjectRegistry.get_rules`` instead.
* The ``PageObjectRegistry.search_overrides`` is deprecated.
  Use ``PageObjectRegistry.search_rules`` instead.

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
