.. _additional-requests:

===================
Additional requests
===================

Some websites require page interactions to load some information, such as
clicking a button, scrolling down or hovering on some element. These
interactions usually trigger background requests that are then loaded using
JavaScript.

To extract such data, reproduce those requests using :class:`~.HttpClient`.
Include :class:`~.HttpClient` among the :ref:`inputs <inputs>` of your
:ref:`page object <page-objects>`, and use an asynchronous :ref:`field
<fields-sync-async>` or method to call one of its methods.

For example, simulating a click on a button that loads product images could
look like:

.. code-block:: python

    import attrs
    from web_poet import HttpClient, HttpError, field
    from zyte_common_items import Image, ProductPage


    @attrs.define
    class MyProductPage(ProductPage]):
        http: HttpClient

        @field
        def productId(self):
            return self.css("::attr(product-id)").get()

        @field
        async def images(self):
            url = f"https://api.example.com/v2/images?id={self.productId}"
            try:
                response = await self.http.get(url)
            except HttpError:
                return []
            else:
                urls = response.css(".product-images img::attr(src)").getall()
                return [Image(url=url) for url in urls]

.. warning::

    :class:`~.HttpClient` should only be used to handle the type of scenarios
    mentioned above. Using :class:`~.HttpClient` for crawling logic would
    defeat :ref:`the purpose of web-poet <overview>`.


Making a request
================

:class:`~.HttpClient` provides multiple asynchronous request methods, such as:

.. code-block:: python

    http.get(url)
    http.post(url)
    http.request(url, method="...")
    http.execute(HttpRequest(url, method="..."))

Request methods also accept custom headers and body, for example:

.. code-block:: python

    http.post(
        url,
        headers={"Content-Type": "application/json;charset=UTF-8"},
        body=json.dumps({"foo": "bar"}).encode("utf-8"),
    )

Request methods may either raise an :class:`~.HttpError` or return an
:class:`~.HttpResponse`. See :ref:`httpresponse`.

.. note::

    :class:`~.HttpClient` methods are expected to follow any redirection except
    when the request method is ``HEAD``. This means that the
    :class:`~.HttpResponse` that you get is already the end of any redirection
    trail.


Concurrent requests
===================

To send multiple requests concurrently, use :meth:`HttpClient.batch_execute
<.HttpClient.batch_execute>`, which accepts any number of
:class:`~.HttpRequest` instances as input, and returns :class:`~.HttpResponse`
instances (and :class:`~.HttpError` instances when using
``return_exceptions=True``) in the input order. For example:

.. code-block:: python

    import attrs
    from web_poet import HttpClient, HttpError, HttpRequest, field
    from zyte_common_items import Image, ProductPage, ProductVariant


    @attrs.define
    class MyProductPage(ProductPage):
        http: HttpClient

        max_variants = 10

        @field
        def productId(self):
            return self.css("::attr(product-id)").get()

        @field
        async def variants(self):
            requests = [
                HttpRequest(f"https://example.com/api/variant/{self.productId}/{index}")
                for index in range(self.max_variants)
            ]
            responses = await self.http.batch_execute(*requests, return_exceptions=True)
            return [
                ProductVariant(color=response.css("::attr(color)").get())
                for response in responses
                if not isinstance(response, HttpError)
            ]

You can alternatively use :mod:`asyncio` together with :class:`~.HttpClient` to
handle multiple requests. For example, you can use :func:`asyncio.as_completed`
to process the first response from a group of requests as early as possible.


Error handling
==============

:class:`~.HttpClient` methods may raise an exception of type
:class:`~.HttpError` or a subclass.

If the response HTTP status code (:attr:`response.status
<.HttpResponse.status>`) is 400 or higher, :class:`~.HttpResponseError` is
raised. In case of connection errors, TLS errors and similar,
:class:`~.HttpRequestError` is raised.

:class:`~.HttpError` provides access to the offending
:attr:`~.HttpError.request`, and :class:`~.HttpResponseError` also provides
access to the offending :attr:`~.HttpResponseError.response`.


.. _retries-additional-requests:

Retrying additional requests
============================

:ref:`Input validation <input-validation>` allows retrying all inputs from a
page object. To retry only additional requests, you must handle retries on your
own.

Your code is responsible for retrying additional requests until good response
data is received, or until some maximum number of retries is exceeded.

It is up to you to decide what the maximum number of retries should be for a
given additional request, based on your experience with the target website.

It is also up to you to decide how to implement retries of additional requests.

One option would be tenacity_. For example, to try an additional request 3
times before giving up:

.. _tenacity: https://tenacity.readthedocs.io/en/latest/index.html

.. code-block:: python

    import attrs
    from tenacity import retry, stop_after_attempt
    from web_poet import HttpClient, HttpError, field
    from zyte_common_items import ProductPage


    @attrs.define
    class MyProductPage(ProductPage):
        http: HttpClient

        @field
        def productId(self):
            return self.css("::attr(product-id)").get()

        @retry(stop=stop_after_attempt(3))
        async def get_images(self):
            return self.http.get(f"https://api.example.com/v2/images?id={self.productId}")

        @field
        async def images(self):
            try:
                response = await self.get_images()
            except HttpError:
                return []
            else:
                urls = response.css(".product-images img::attr(src)").getall()
                return [Image(url=url) for url in urls]

If the reason your additional request fails is outdated or missing data from
page object input, do not try to reproduce the request for that input as an
additional request. :ref:`Request fresh input instead <retries-input>`.