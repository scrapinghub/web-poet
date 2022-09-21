=========
Changelog
=========

0.5.0 (TBD)
-----------

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
