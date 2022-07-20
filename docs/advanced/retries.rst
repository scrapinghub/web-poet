.. _retries:

=======
Retries
=======

The webpages of some websites can be unreliable. For example, sometimes
a request can get a response that may only include a part of the data to be
extracted, or no data at all, but sending a follow-up, identical request can
get you the expected data.

You can write your page object so that it raises
:exc:`~web_poet.exceptions.core.Retry` when it detects missing data that may become
available after a request retry:

.. code-block:: python

    from web_poet import ItemWebPage
    from web_poet.exceptions import Retry

    class MyPage(ItemWebPage):

        def is_bad_response(self):
            return not self.css('.expected-element')

        def to_item(self) -> dict:
            if self.is_bad_response():
                raise Retry
            return {}

.. _framework-retries:

Framework Expectations
======================

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
