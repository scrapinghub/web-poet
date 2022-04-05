.. _`advanced-requests`:

===================
Additional Requests
===================

Websites nowadays needs a lot of page interactions to display or load some key
information. In most cases, these are done via AJAX requests. Some examples of these are:

    * Clicking a button on a page to reveal other similar products.
    * Clicking the `"Load More"` button to retrieve more images of a given item.
    * Scrolling to the bottom of the page to load more items `(i.e. infinite scrolling)`.
    * Hovering on a certain webpage element that reveals a tool-tip containing
      additional page info.

As such, performing additional requests inside Page Objects are inevitable to
properly extract data for some websites.

.. warning::

    Additional requests made inside a Page Object aren't meant to represent
    the **Crawling Logic** at all. They are simply a low-level way to interact
    with today's websites which relies on a lot of page interactions to display
    its contents.


HttpRequest
===========

Additional requests are defined using a simple data container that represents
a generic HTTP Request: :class:`~.HttpRequest`. Here's an example:

.. code-block:: python

    import json
    import web_poet

    request = web_poet.HttpRequest(
        url="https://www.api.example.com/product-pagination/",
        method="POST",
        headers={
            "Host": "www.example.com",
            "Content-Type": "application/json; charset=UTF-8",
        },
        body=json.dumps(
            {
                "Page": page_num,
                "ProductID": product_id,
            }
        ).encode("utf-8"),
    )

    print(request.url)     # https://www.api.example.com/product-pagination/
    print(request.method)  # POST

    print(type(request.headers)  # <class 'web_poet.requests.HttpRequestHeaders'>
    print(request.headers)       # <HttpRequestHeaders('Host': 'www.example.com', 'Content-Type': 'application/json; charset=UTF-8')>
    print(request.headers.get("content-type"))    # application/json; charset=UTF-8
    print(request.headers.get("does-not-exist"))  # None

    print(type(request.body))  # <class 'web_poet.requests.HttpRequestBody'>
    print(request.body)        # b'{"Page": 1, "ProductID": 123}'

There are a few things to take note here:

    * ``url`` and ``method`` are simply **strings**.
    * ``headers`` is represented by the :class:`~.HttpRequestHeaders` class which
      resembles a ``dict``-like interface. It supports case-insensitive header-key
      lookups as well as multi-key storage.

        * See :external:py:class:`multidict.CIMultiDict` for the set of features
          since :class:`~.HttpRequestHeaders` simply subclasses from it.

    * ``body`` is represented by the :class:`~.HttpRequestBody` class which is
      simply a subclass of the ``bytes`` class. Using the ``body`` param of
      :class:`~.HttpRequest` needs to have an input argument in ``bytes``. In our
      code example, we've converted it from ``str`` to ``bytes`` using the ``encode()``
      string method.

Most of the time though, what you'll be defining would be ``GET`` requests. Thus,
it's perfectly fine to define them as:

.. code-block:: python

    import web_poet

    request = web_poet.HttpRequest("https://api.example.com/product-info?id=123")

    print(request.url)     # https://api.example.com/product-info?id=123
    print(request.method)  # GET

    print(type(request.headers)  # <class 'web_poet.requests.HttpRequestHeaders'>
    print(request.headers)       # <HttpRequestHeaders()>
    print(request.headers.get("content-type"))    # None
    print(request.headers.get("does-not-exist"))  # None

    print(type(request.body))  # <class 'web_poet.requests.HttpRequestBody'>
    print(request.body)        # b''

The key take aways are:

    * The default value of ``method`` is ``GET``.
    * ``headers`` still holds :class:`~.HttpRequestHeaders` which doesn't contain
      anything.
    * The same is true for ``body`` holding an empty :class:`~.HttpRequestBody`.

Now that we know how :class:`~.HttpRequest` are structured, defining them doesn't
execute the actual requests at all. In order to do so, we'll need to feed it into
the :class:`~.HttpClient` which is defined in the next section.


HttpClient
==========

The main interface for executing additional requests would be :class:`~.HttpClient`.
It also has full support for :mod:`asyncio` enabling developers to perform 
additional requests asynchronously using ``asyncio.gather()``, ``asyncio.wait()``,
etc. This means that ``asyncio`` could be used anywhere inside the Page Object,
including the ``to_item()`` method.

In the previous section, we've explored how :class:`~.HttpRequest` are defined.
Fortunately, the :meth:`~.HttpClient.request`, :meth:`~.HttpClient.get`, and
:meth:`~.HttpClient.post` methods of :class:`~.HttpClient` already defines the
:class:`~.HttpRequest` and executes it as well. The only time you'll need to create
:class:`~.HttpRequest` manually is via the :meth:`~.HttpClient.batch_requests`
method which is described in this section: :ref:`batch-request-example`.

Let's see a few quick examples to see how to execute additional requests using
the :class:`~.HttpClient`.

A simple ``GET`` request
------------------------

.. code-block:: python

    import attrs
    import web_poet


    @attrs.define
    class ProductPage(web_poet.ItemWebPage):
        http_client: web_poet.HttpClient

        async def to_item(self):
            item = {
                "url": self.url,
                "name": self.css("#main h3.name ::text").get(),
                "product_id": self.css("#product ::attr(product-id)").get(),
            }

            # Simulates clicking on a button that says "View All Images"
            response: web_poet.HttpResponse = await self.http_client.get(
                f"https://api.example.com/v2/images?id={item['product_id']}"
            )
            item["images"] = response.css(".product-images img::attr(src)").getall()
            return item

There are a few things to take note in this example:

    * A ``GET`` request can be done via :class:`~.HttpClient`'s
      :meth:`~.HttpClient.get` method.
    * We're now using the ``async/await`` syntax inside the ``to_item()`` method.
    * The response from the additional request is of type :class:`~.HttpResponse`.

As the example suggests, we're performing an additional request that allows us
to extract more images in a product page that might not otherwise be possible.
This is because in order to do so, an additional button needs to be clicked
which fetches the complete set of product images via AJAX.

.. _`request-post-example`:

A ``POST`` request with `header` and `body`
-------------------------------------------

Let's see another example which needs ``headers`` and ``body`` data to process
additional requests.

In this example, we'll paginate related items in a carousel. These are
usually lazily loaded by the website to reduce the amount of information
rendered in the DOM that might not otherwise be viewed by all users anyway.

Thus, additional requests inside the Page Object are typically needed for it:

.. code-block:: python

    import attrs
    import web_poet


    @attrs.define
    class ProductPage(web_poet.ItemWebPage):
        http_client: web_poet.HttpClient

        async def to_item(self):
            item = {
                "url": self.url,
                "name": self.css("#main h3.name ::text").get(),
                "product_id": self.css("#product ::attr(product-id)").get(),
                "related_product_ids": self.parse_related_product_ids(self),
            }

            # Simulates "scrolling" through a carousel that loads related product items
            response: web_poet.HttpResponse = await self.http_client.post(
                url="https://www.api.example.com/related-products/",
                headers={
                    'Host': 'www.example.com',
                    'Content-Type': 'application/json; charset=UTF-8',
                },
                body=json.dumps(
                    {
                        "Page": 2,
                        "ProductID": item["product_id"],
                    }
                ).encode("utf-8"),
            )
            item["related_product_ids"].extend(self.parse_related_product_ids(response))
            return item

        @staticmethod
        def parse_related_product_ids(response_page) -> List[str]:
            return response_page.css("#main .related-products ::attr(product-id)").getall()

Here's the key takeaway in this example:

    * Similar to :class:`~.HttpClient`'s :meth:`~.HttpClient.get` method,
      a :meth:`~.HttpClient.post` method is also available that's
      typically used to submit forms.

.. _`batch-request-example`:

Batch requests
--------------

We can also choose to process requests by **batch** instead of sequentially or 
one by one. The :meth:`~.HttpClient.batch_requests` method can be used for this
which accepts an arbitrary number of :class:`~.HttpRequest` instances.

Let's modify the example in the previous section to see how it can be done.

The difference for this code example from the previous section is that we're
increasing the pagination from only the **2nd page** into the **10th page**.
Instead of calling a single :meth:`~.HttpClient.post` method, we're creating a
list of :class:`~.HttpRequest` to be executed in batch using the
:meth:`~.HttpClient.batch_requests` method.

.. code-block:: python

    from typing import List

    import attrs
    import web_poet


    @attrs.define
    class ProductPage(web_poet.ItemWebPage):
        http_client: web_poet.HttpClient

        default_pagination_limit = 10

        async def to_item(self):
            item = {
                "url": self.url,
                "name": self.css("#main h3.name ::text").get(),
                "product_id": self.css("#product ::attr(product-id)").get(),
                "related_product_ids": self.parse_related_product_ids(self),
            }

            requests: List[web_poet.HttpRequest] = [
                self.create_request(page_num=page_num)
                for page_num in range(2, default_pagination_limit)
            ]
            responses: List[web_poet.HttpResponse] = await self.http_client.batch_requests(*requests)
            related_product_ids = [
                product_id
                for response in responses
                for product_id in self.parse_related_product_ids(response)
            ]

            item["related_product_ids"].extend(related_product_ids)
            return item

        def create_request(self, page_num=2):
            # Simulates "scrolling" through a carousel that loads related product items
            return web_poet.HttpRequest(
                url="https://www.api.example.com/product-pagination/",
                method="POST",
                headers={
                    "Host": "www.example.com",
                    "Content-Type": "application/json; charset=UTF-8",
                },
                body=json.dumps(
                    {
                        "Page": page_num,
                        "ProductID": item["product_id"],
                    }
                ).encode("utf-8"),
            )

        @staticmethod
        def parse_related_product_ids(response_page) -> List[str]:
            return response_page.css("#main .related-products ::attr(product-id)").getall()

The key takeaways for this example are:

    * An :class:`~.HttpRequest` can be instantiated to represent a Generic HTTP Request.
      It only contains the HTTP Request information for now and isn't executed yet.
      This is useful for creating factory methods to help create requests without any
      download execution at all.
    * :class:`~.HttpClient` has a :meth:`~.HttpClient.batch_requests` method that
      can process a list of :class:`~.HttpRequest` instances asynchronously together.

.. tip::

    The :meth:`~.HttpClient.batch_requests` method can accept different varieties
    of :class:`~.HttpRequest` that might not be related with one another. For
    example, it could be a mixture of ``GET`` and ``POST`` requests or even
    representing requests for various parts of the page altogether.

    Processing the additional requests in batch is useful since it takes advantage
    of async execution which could be faster in certain cases `(assuming you're
    allowed to perform HTTP requests in parallel)`.

    Nonetheless, you can still use the :meth:`~.HttpClient.batch_requests` method
    to execute a single :class:`~.HttpRequest` instance.

.. _advanced-downloader-impl:

Downloader Implementation
=========================

Please note that on its own, :class:`~.HttpClient` doesn't do anything. It doesn't
know how to execute the request on its own. Thus, for frameworks or projects
wanting to use additional requests in Page Objects, they need to set the
implementation of how to download :class:`~.Request`.

For more info on this, kindly read the API Specifications for :class:`~.HttpClient`.

In any case, frameworks that wish to support **web-poet** could provide the
HTTP downloader implementation in two ways:

.. _setup-contextvars:

1. Context Variable
-------------------

:mod:`contextvars` is natively supported in :mod:`asyncio` in order to set and
access context-aware values. This means that the framework using **web-poet**
can easily assign the implementation using the readily available :mod:`contextvars`
instance named ``web_poet.request_backend_var``.

This can be set using:

.. code-block:: python

    import attrs
    import web_poet

    def request_implementation(req: web_poet.HttpRequest) -> web_poet.HttpResponse:
        ...


    def create_http_client():
        return web_poet.HttpClient()


    @attrs.define
    class SomePage(web_poet.ItemWebPage):
        http_client: web_poet.HttpClient

        async def to_item(self):
            ...

    # Once this is set, the ``request_implementation`` will become available to
    # all instances of HttpClient unless a ``request_downloader`` is injected
    # to it (see #2 Dependency Injection example below).
    web_poet.request_backend_var.set(request_implementation)

    # Assume that it's constructed with the necessary arguments taken somewhere.
    response = web_poet.HttpResponse(...)

    page = SomePage(response=response, http_client=create_http_client())
    item = page.to_item()

Setting this up would allow access to the request implementation in a
:class:`~.HttpClient` instance which uses it by default.

.. warning::

    If no value for ``web_poet.request_backend_var`` was set, then a
    :class:`~.RequestBackendError` is raised. However, no exception would
    be raised if **option 2** below is used.


2. Dependency Injection
-----------------------

The framework using **web-poet** might be using other libraries which doesn't
have a full support to :mod:`contextvars` `(e.g. Twisted)`. With that, an
alternative approach would be to supply the request implementation when creating
an :class:`~.HttpClient` instance:

.. code-block:: python

    import attrs
    import web_poet

    def request_implementation(req: web_poet.HttpRequest) -> web_poet.HttpResponse:
        ...

    def create_http_client():
        return web_poet.HttpClient(request_downloader=request_implementation)


    @attrs.define
    class SomePage(web_poet.ItemWebPage):
        http_client: web_poet.HttpClient

        async def to_item(self):
            ...

    # Assume that it's constructed with the necessary arguments taken somewhere.
    response = web_poet.HttpResponse(...)

    page = SomePage(response=response, http_client=create_http_client())
    item = page.to_item()

From the code sample above, we can see that every time an :class:`~.HttpClient`
is created for Page Objects needing an ``http_client``, the specific **request
implementation** from a given framework is injected to it.
