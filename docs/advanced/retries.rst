.. _retries:

=======
Retries
=======

The responses of some websites can be unreliable. For example, sometimes
a request can get a response that may only include a part of the data to be
extracted, no data at all, or even data unrelated to your request, but sending
a follow-up, identical request can get you the expected data.

Pages objects are responsible for handling these scenarios, where issues with
response data can only be detected during extraction.

.. _retries-input:

Retrying Page Object Input
==========================

When the bad response data comes from the inputs that your web-poet framework
supplies to your page object, your page object must raise
:exc:`~web_poet.exceptions.core.Retry`:

.. code-block:: python

    from web_poet import ItemWebPage
    from web_poet.exceptions import Retry

    class MyPage(ItemWebPage):

        def to_item(self) -> dict:
            if not self.css('.expected'):
                raise Retry
            return {}

As a result, your web-poet framework will retry the source requests and create
a new instance of your page object with the new inputs.


.. _retries-additional-requests:

Retrying Additional Requests
============================

When the bad response data comes from :ref:`additional requests
<advanced-requests>`, you must handle retries on your own.

The page object code is responsible for retrying additional requests until good
response data is received, or until some maximum number of retries is exceeded.

It is up to you to decide what the maximum number of retries should be for a
given additional request, based on your experience with the target website.

It is also up to you to decide how to implement retries of additional requests.

One option would be tenacity_. For example, to try an additional request 3
times before giving up:

.. _tenacity: https://tenacity.readthedocs.io/en/latest/index.html

.. code-block:: python

    import attrs
    from tenacity import retry, stop_after_attempt
    from web_poet import HttpClient, HttpRequest, ItemWebPage

    @attrs.define
    class MyPage(ItemWebPage):
        http_client: HttpClient

        @retry(stop=stop_after_attempt(3))
        async def get_data(self):
            request = HttpRequest('https://toscrape.com/')
            response = await self.http_client.execute(request)
            if not response.css('.expected'):
                raise ValueError
            return response.css('.data').get()

        async def to_item(self) -> dict:
            try:
                data = await self.get_data()
            except ValueError:
                return {}
            return {'data': data}

If the reason your additional request fails is outdated or missing data from
page object input, do not try to reproduce the request for that input as an
additional request. :ref:`Request fresh input instead <retries-input>`.


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
