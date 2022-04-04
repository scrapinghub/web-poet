.. _`advanced-requests`:

===================
Additional Requests
===================

Websites nowadays needs a lot of page interactions to display or load some key
information. In most cases, these are done via AJAX requests. Some examples of these are:

    * Clicking a button on a page to reveal other similar products.
    * Clicking the `"Load More"` button to retrieve more images of a given item.
    * Scrolling to the bottom of the page to load more items `(i.e. infinite scrolling)`.
    * Hovering that reveals a tool-tip containing additional page info.

As such, performing additional requests inside Page Objects are inevitable to
properly extract data for some websites.

.. warning::

    Additional requests made inside a Page Object aren't meant to represent
    the **Crawling Logic** at all. They are simply a low-level way to interact
    with today's websites which relies on a lot of page interactions to display
    its contents.


HttpClient
==========

The main interface for executing additional requests would be :class:`~.HttpClient`.
It also has full support for :mod:`asyncio` enabling developers to perform
the additional requests asynchronously.

Let's see a few quick examples to see how it's being used in action.

A simple ``GET`` request
------------------------

.. code-block:: python

    import attr
    import web_poet


    @attr.define
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
    * We're now using the ``async/await`` syntax.
    * The response is of type :class:`~.HttpResponse`.

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

Thus, additional requests inside the Page Object is typically needed for it:

.. code-block:: python

    import attr
    import web_poet


    @attr.define
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
                ),
            )
            item["related_product_ids"] = self.parse_related_product_ids(response)
            return item

        @staticmethod
        def parse_related_product_ids(response: web_poet.HttpResponse) -> List[str]:
            return response.css("#main .related-products ::attr(product-id)").getall()

Here's the key takeaway in this example:

    * Similar to :class:`~.HttpClient`'s :meth:`~.HttpClient.get` method,
      a :meth:`~.HttpClient.post` method is also available that's
      typically used to submit forms.

Batch requests
--------------

We can also choose to process requests by **batch** instead of sequentially.
Let's modify the example in the previous section to see how it can be done:

.. code-block:: python

    from typing import List

    import attr
    import web_poet


    @attr.define
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

            requests: List[web_poet.Request] = [
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
            return web_poet.Request(
                url="https://www.api.example.com/product-pagination/",
                method="POST",
                headers={
                    'Host': 'www.example.com',
                    'Content-Type': 'application/json; charset=UTF-8',
                },
                body=json.dumps(
                    {
                        "Page": page_num,
                        "ProductID": item["product_id"],
                    }
                ),
            )

        @staticmethod
        def parse_related_product_ids(response: web_poet.HttpResponse) -> List[str]:
            return response.css("#main .related-products ::attr(product-id)").getall()

The key takeaways for this example are:

    * A :class:`~.Request` can be instantiated to represent a Generic HTTP Request.
      It only contains the HTTP Request information for now and isn't executed yet.
      This is useful for creating factory methods to help create them without any
      download execution at all.
    * :class:`~.HttpClient` has a :meth:`~.HttpClient.batch_requests` method that
      can process a list of :class:`~.Request` instances asynchronously together.

        * Note that it can accept different types of :class:`~.Request` that might
          not be related *(e.g. a mixture of* ``GET`` *and* ``POST`` *requests)*.
          This is useful to process them in batch to take advantage of async
          execution.

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

    def request_implementation(r: web_poet.Request) -> web_poet.HttpResponse:
        ...

    from web_poet import request_backend_var
    request_backend_var.set(request_implementation)

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

    def request_implementation(r: web_poet.Request) -> web_poet.HttpResponse:
        ...

    from web_poet import HttpClient
    http_client = HttpClient(request_downloader=request_implementation)
