.. _framework-retries:

==================
Supporting Retries
==================

Web-poet frameworks must catch :exc:`~web_poet.exceptions.core.Retry`
exceptions raised from the :meth:`~web_poet.pages.ItemPage.to_item` method of a
page object.

When :exc:`~web_poet.exceptions.core.Retry` is caught:

#.  The original request whose response was fed into the page object must be
    retried.

#.  A new page object must be created, of the same type as the original page
    object, and with the same input, except for the response data, which must
    be the new response.

The :meth:`~web_poet.pages.ItemPage.to_item` method of the new page object may
raise :exc:`~web_poet.exceptions.core.Retry` again. Web-poet frameworks must
allow multiple retries of page objects, repeating the
:exc:`~web_poet.exceptions.core.Retry`-capturing logic.

However, web-poet frameworks are also encouraged to limit the amount of retries
per page object. When retries are exceeded for a given page object, the page
object output is ignored. At the moment, web-poet does not enforce any specific
maximum number of retries on web-poet frameworks.
