=========
Changelog
=========

TBR
------------------

* Added support for performing additional requests using
  ``web_poet.HttpClient``.
* Introduced ``web_poet.PageParams`` to pass arbitrary information
  inside a Page Object.
* added a ``PageObjectRegistry`` class which has the  ``handle_urls`` decorator
  to conveniently declare and collect ``OverrideRule``.
* removed support for Python 3.6
* added support for Python 3.10
* Backward Incompatible Change:

    * ``ResponseData`` is now ``HttpResponse`` which has a new
      specific attribute types like ``HttpResponseBody`` and
      ``HttpResponseHeaders``.

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
