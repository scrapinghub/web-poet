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

.. _`httprequest-example`:

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
            "Content-Type": "application/json;charset=UTF-8"
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

    print(type(request.headers)  # <class 'web_poet.page_inputs.HttpRequestHeaders'>
    print(request.headers)       # <HttpRequestHeaders('Content-Type': 'application/json;charset=UTF-8')>
    print(request.headers.get("content-type"))    # application/json;charset=UTF-8
    print(request.headers.get("does-not-exist"))  # None

    print(type(request.body))  # <class 'web_poet.page_inputs.HttpRequestBody'>
    print(request.body)        # b'{"Page": 1, "ProductID": 123}'

There are a few things to take note here:

    * ``url`` and ``method`` are simply **strings**.
    * ``headers`` is represented by the :class:`~.HttpRequestHeaders` class which
      resembles a ``dict``-like interface. It supports case-insensitive header-key
      lookups as well as multi-key storage.

        * See :external:py:class:`multidict.CIMultiDict` for the set of features
          since :class:`~.HttpRequestHeaders` simply inherits from it.

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

    print(type(request.headers)  # <class 'web_poet.page_inputs.HttpRequestHeaders'>
    print(request.headers)       # <HttpRequestHeaders()>
    print(request.headers.get("content-type"))    # None
    print(request.headers.get("does-not-exist"))  # None

    print(type(request.body))  # <class 'web_poet.page_inputs.HttpRequestBody'>
    print(request.body)        # b''

The key take aways are:

    * The default value of ``method`` is ``GET``.
    * ``headers`` still holds :class:`~.HttpRequestHeaders` which doesn't contain
      anything.
    * The same is true for ``body`` holding an empty :class:`~.HttpRequestBody`.

Now that we know how :class:`~.HttpRequest` are structured, defining them doesn't
execute the actual requests at all. In order to do so, we'll need to feed it into
the :class:`~.HttpClient` which is defined in the next section (see
:ref:`httpclient` tutorial section).

HttpResponse
============

:class:`~.HttpResponse` is what comes after a :class:`~.HttpRequest` has been
executed. It's typically returned by the methods from :class:`~.HttpClient` (see
:ref:`httpclient` tutorial section) which holds the information regarding the response.
It's also the required input for Page Objects inheriting from the :class:`~.ItemWebPage`
class as explained from the :ref:`from-ground-up` tutorial.

.. note::

    The additional requests are expected to perform redirections except when the
    method is ``HEAD``. This means that the :class:`~.HttpResponse` that you'll
    be receiving is already the end of the redirection trail.

Let's check out an example to see its internals:

.. code-block:: python

    import web_poet

    response = web_poet.HttpResponse(
        url="https://www.api.example.com/product-pagination/",
        body='{"data": "value 👍"}'.encode("utf-8"),
        status=200,
        headers={"Content-Type": "application/json;charset=UTF-8"}
    )

    print(response.url)            # https://www.api.example.com/product-pagination/
    print(type(response.url))      # <class 'str'>

    print(response.body)           # b'{"data": "value \xf0\x9f\x91\x8d"}'
    print(type(response.body))     # <class 'web_poet.page_inputs.HttpResponseBody'>

    print(response.status)         # 200
    print(type(response.status))   # <class 'int'>

    print(response.headers)        # <HttpResponseHeaders('Content-Type': 'application/json;charset=UTF-8')>
    print(type(response.headers))  # <class 'web_poet.page_inputs.HttpResponseHeaders'>
    print(response.headers.get("content-type"))    # application/json;charset=UTF-8
    print(response.headers.get("does-not-exist"))  # None

    # These methods are also available:

    print(response.body.declared_encoding())    # None
    print(response.body.json())                 # {'data': 'value 👍'}

    print(response.headers.declared_encoding()) # utf-8

    print(response.encoding)                    # utf-8
    print(response.text)                        # {"data": "value 👍"}
    print(response.json())                      # {'data': 'value 👍'}

Despite what the example above showcases, you won't be typically defining
:class:`~.HttpResponse` yourself as it's the implementing framework that's
responsible for it (see :ref:`advanced-downloader-impl`). Nonetheless, it's
important to understand its underlying structure in order to better access its
methods.

Here are the key take aways from the example above:

    * The ``url`` and ``status`` are simply **string** and **int** respectively.
    * ``headers`` is represented by the :class:`~.HttpResponseHeaders` class.
      It's similar to :class:`~.HttpRequestHeaders` where it inherits from
      :external:py:class:`multidict.CIMultiDict`, granting it case-insensitive
      header-key lookups as well as multi-key storage.

        * The **encoding** can be derived using the :meth:`~.HttpResponseHeaders.declared_encoding`
          method. In this example, it was retrieved from the ``Content-Type`` header.

    * ``body`` is represented by the :class:`~.HttpResponseBody` class which is
      simply a subclass of the ``bytes`` class. Using the ``body`` param of
      :class:`~.HttpResponse` needs to have an input argument in ``bytes``. In our
      code example, we've converted it from ``str`` to ``bytes`` using the ``encode()``
      string method.

        * Similar to the headers, the **encoding** can be derived using the
          :meth:`~.HttpResponseBody.declared_encoding`. In this case, it returned
          ``None`` since no encoding can be derived from the response body.
        * A :meth:`~.HttpResponseBody.json` method is also available to conveniently
          access decoded contents from JSON responses. It uses the derived **encoding**
          to properly decode the contents like the 👍 emoji.

    * The :class:`~.HttpResponse` class itself also have these convenient methods:

        * The :meth:`~.HttpResponse.encoding` property method returns the proper
          encoding of the response based on the availability of this hierarchy:

            * user-specified encoding (`using the` ``_encoding`` `attribute`)
            * header encodings
            * body encodings

        * Instead of accessing the raw bytes values `(which doesn't represent the
          underlying content properly like the` 👍 `emoji)`, the :meth:`~.HttpResponse.text`
          property method can be used which takes into account the derived **encoding**
          when decoding the bytes value.
        * The :meth:`~.HttpResponse.json` method is available as a shortcut to
          :class:`~.HttpResponseBody`'s :meth:`~.HttpResponseBody.json` method.

We've only explored a JSON response as a result from an additional request. Let's
take a look at another example having an HTML response:

.. code-block:: python

    import web_poet

    response = web_poet.HttpResponse(
        url="https://www.api.example.com/product-pagination/",
        body=(
            '<html>'
            '  <head>'
            '    <title>Some page</title>'
            '    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
            '  </head>'
            '  <body>Sample content 💯</body>'
            '</html>'
        ).encode("utf-8"),
        status=200,
        headers={}
    )

    print(response.headers.declared_encoding()) # None
    print(response.body.declared_encoding())    # utf-8
    print(response.encoding)                    # utf-8

    print(response.body.json())  # JSONDecodeError
    print(response.json())       # JSONDecodeError

    print(type(response.selector))  # <class 'parsel.selector.Selector'>

    print(response.selector.css("body ::text").get())     # Sample content 💯
    print(response.css("body ::text").get())              # Sample content 💯

    print(response.selector.xpath("//body/text()").get()) # Sample content 💯
    print(response.xpath("//body/text()").get())          # Sample content 💯

The key take aways for this example are:

    * The **encoding** is derived from the body inside the ``meta`` tags since the
      ``headers`` is empty for this example.
    * Since we now have an HTML response, using :meth:`~.HttpResponseBody.json`
      method would raise a ``JSONDecodeError`` as a JSON document cannot be
      parsed from it.
    * The :meth:`~.HttpResponse.selector` property method returns an instance of
      :external:py:class:`parsel.selector.Selector` which allows parsing via
      :meth:`~.HttpResponse.css` and :meth:`~.HttpResponse.xpath` calls.

        * At the same time, there's no need to call :meth:`~.HttpResponse.selector`
          each time as the :meth:`~.HttpResponse.css` and :meth:`~.HttpResponse.xpath`
          are already conveniently available.


.. _`httpclient`:

HttpClient
==========

The main interface for executing additional requests would be :class:`~.HttpClient`.
It also has full support for :mod:`asyncio` enabling developers to perform 
additional requests asynchronously using :py:func:`asyncio.gather`,
:py:func:`asyncio.wait`, etc. This means that :mod:`asyncio` could be used anywhere
inside the Page Object, including the :meth:`~.ItemPage.to_item` method.

In the previous section, we've explored how :class:`~.HttpRequest` is defined.
Let's see a few quick examples to see how to execute additional requests using
the :class:`~.HttpClient`.

Executing a HttpRequest instance
--------------------------------

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
            request = web_poet.HttpRequest(f"https://api.example.com/v2/images?id={item['product_id']}")
            response: web_poet.HttpResponse = await self.http_client.execute(request)

            item["images"] = response.css(".product-images img::attr(src)").getall()
            return item

As the example suggests, we're performing an additional request that allows us
to extract more images in a product page that might not be otherwise be possible.
This is because in order to do so, an additional button needs to be clicked
which fetches the complete set of product images via AJAX.

There are a few things to take note of this example:

    * Recall from the :ref:`httprequest-example` tutorial section that the
      default method is ``GET``. Thus, the ``method`` parameter can be omitted
      for simple ``GET`` requests.
    * We're now using the ``async/await`` syntax inside the :meth:`~.ItemPage.to_item`
      method.
    * The response from the additional request is of type :class:`~.HttpResponse`.

.. tip::

    Check out the :ref:`http-batch-request-example` tutorial section to see how
    to execute a group of :class:`~.HttpRequest` in batch.

Fortunately, there are already some quick shortcuts on how to perform single
additional requests using the :meth:`~.HttpClient.request`, :meth:`~.HttpClient.get`,
and :meth:`~.HttpClient.post` methods of :class:`~.HttpClient`. These already
define the :class:`~.HttpRequest` and executes it as well.

.. _`httpclient-get-example`:

A simple ``GET`` request
------------------------

Let's use the example from the previous section and use the :meth:`~.HttpClient.get`
method on it.

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
    * There was no need to instantiate a :class:`~.HttpRequest` since :meth:`~.HttpClient.get`
      already handles it before executing the request.

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
                    "Content-Type": "application/json;charset=UTF-8"
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

Other Single Requests
---------------------

The :meth:`~.HttpClient.get` and :meth:`~.HttpClient.post` methods are merely
quick shortcuts for :meth:`~.HttpClient.request`:

.. code-block:: python

    client = HttpClient()

    url = "https://api.example.com/v1/data"
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    body = b'{"data": "value"}'

    # These are the same:
    client.get(url)
    client.request(url, method="GET")

    # The same goes for these:
    client.post(url, headers=headers, body=body)
    client.request(url, method="POST", headers=headers, body=body)

Thus, apart from the common ``GET`` and ``POST`` HTTP methods, you can use 
:meth:`~.HttpClient.request` for them (`e.g.` ``HEAD``, ``PUT``, ``DELETE``, etc).

.. _`http-batch-request-example`:

Batch requests
--------------

We can also choose to process requests by **batch** instead of sequentially or 
one by one (e.g. using :meth:`~.HttpClient.execute`). The :meth:`~.HttpClient.batch_execute`
method can be used for this which accepts an arbitrary number of :class:`~.HttpRequest`
instances.

Let's modify the example in the previous section to see how it can be done.

The difference for this code example from the previous section is that we're
increasing the pagination from only the **2nd page** into the **10th page**.
Instead of calling a single :meth:`~.HttpClient.post` method, we're creating a
list of :class:`~.HttpRequest` to be executed in batch using the
:meth:`~.HttpClient.batch_execute` method.

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
                self.create_request(item["product_id"], page_num=page_num)
                for page_num in range(2, self.default_pagination_limit)
            ]
            responses: List[web_poet.HttpResponse] = await self.http_client.batch_execute(*requests)
            related_product_ids = [
                id_
                for response in responses
                for product_ids in self.parse_related_product_ids(response)
                for id_ in product_ids
            ]

            item["related_product_ids"].extend(related_product_ids)
            return item

        def create_request(self, product_id, page_num=2):
            # Simulates "scrolling" through a carousel that loads related product items
            return web_poet.HttpRequest(
                url="https://www.api.example.com/product-pagination/",
                method="POST",
                headers={
                    "Content-Type": "application/json;charset=UTF-8"
                },
                body=json.dumps(
                    {
                        "Page": page_num,
                        "ProductID": product_id,
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
    * :class:`~.HttpClient` has a :meth:`~.HttpClient.batch_execute` method that
      can process a list of :class:`~.HttpRequest` instances asynchronously together.

.. tip::

    The :meth:`~.HttpClient.batch_execute` method can accept different varieties
    of :class:`~.HttpRequest` that might not be related with one another. For
    example, it could be a mixture of ``GET`` and ``POST`` requests or even
    representing requests for various parts of the page altogether.

    Processing the additional requests in batch is useful since it takes advantage
    of async execution which could be faster in certain cases `(assuming you're
    allowed to perform HTTP requests in parallel)`.

    Nonetheless, you can still use the :meth:`~.HttpClient.batch_execute` method
    to execute a single :class:`~.HttpRequest` instance.

.. note::

    The :meth:`~.HttpClient.batch_execute` method is a simple wrapper over
    :py:func:`asyncio.gather`. Developers are free to use other functionalities
    available inside :mod:`asyncio` to handle multiple requests.

    For example, :py:func:`asyncio.as_completed` can be used to process the
    first response from a group of requests as early as possible. However, the
    order could be shuffled.


Exception Handling
==================

Overview
--------

Let's have a look at how we could handle exceptions when performing additional
requests inside a Page Objects. For this example, let's improve the code snippet
from the previous subsection named: :ref:`httpclient-get-example`.

.. code-block:: python

    import logging

    import attrs
    import web_poet

    logger = logging.getLogger(__name__)


    @attrs.define
    class ProductPage(web_poet.ItemWebPage):
        http_client: web_poet.HttpClient

        async def to_item(self):
            item = {
                "url": self.url,
                "name": self.css("#main h3.name ::text").get(),
                "product_id": self.css("#product ::attr(product-id)").get(),
            }

            try:
                # Simulates clicking on a button that says "View All Images"
                response: web_poet.HttpResponse = await self.http_client.get(
                    f"https://api.example.com/v2/images?id={item['product_id']}"
                )
            except web_poet.exceptions.HttpRequestError:
                logger.warning(
                    f"Unable to request images for product ID: {item['product_id']}"
                )
            else:
                item["images"] = response.css(".product-images img::attr(src)").getall()

            return item

In this code example, the code became more resilient on cases where it wasn't
possible to retrieve more images using the website's public API. It could be
due to anything like `SSL errors`, `connection errors`, etc.

.. note::

    For now, using :class:`~.HttpClient` to execute requests only raises exceptions
    of type :class:`web_poet.exceptions.http.HttpRequestError` irregardless of how
    the HTTP Downloader is implemented.

    In the future, more specific exceptions which inherits from the base
    :class:`web_poet.exceptions.http.HttpRequestError` exception would be available.
    This should enable developers writing Page Objects to properly identify what
    went wrong and act specifically based on the problem.

Let's take another example when executing requests in batch as opposed to using
single requests via these methods of the :class:`~.HttpClient`: 
:meth:`~.HttpClient.request`, :meth:`~.HttpClient.get`, and :meth:`~.HttpClient.post`.

For this example, let's improve the code snippet from the previous subsection named:
:ref:`http-batch-request-example`.

.. code-block:: python

    import logging
    from typing import List, Union

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
                self.create_request(item["product_id"], page_num=page_num)
                for page_num in range(2, self.default_pagination_limit)
            ]

            try:
                responses: List[web_poet.HttpResponse] = await self.http_client.batch_execute(*requests)
            except web_poet.exceptions.HttpRequestError:
                logger.warning(
                    f"Unable to request for more related products for product ID: {item['product_id']}"
                )
            else:
                related_product_ids = []
                for response in responses:
                    related_product_ids.extend(
                        [
                            id_
                            for product_ids in self.parse_related_product_ids(response)
                            for id_ in product_ids
                        ]
                    )
                item["related_product_ids"].extend(related_product_ids)

            return item

        def create_request(self, product_id, page_num=2):
            # Simulates "scrolling" through a carousel that loads related product items
            return web_poet.HttpRequest(
                url="https://www.api.example.com/product-pagination/",
                method="POST",
                headers={
                    "Content-Type": "application/json;charset=UTF-8"
                },
                body=json.dumps(
                    {
                        "Page": page_num,
                        "ProductID": product_id,
                    }
                ).encode("utf-8"),
            )

        @staticmethod
        def parse_related_product_ids(response_page) -> List[str]:
            return response_page.css("#main .related-products ::attr(product-id)").getall()

Handling exceptions using :meth:`~.HttpClient.batch_execute` remains largely the same.
However, the main difference is that you might be wasting perfectly good responses just
because a single request from the batch ruined it.

An alternative approach would be salvaging good responses altogether. For example, you've
sent out 10 :class:`~.HttpRequest` and only 1 of them had an exception during processing.
You can still get the data from 9 of the :class:`~.HttpResponse` by passing the parameter
``return_exceptions=True`` to :meth:`~.HttpClient.batch_execute`.

This means that any exceptions raised during request execution are returned alongside any
of the successful responses. The return type of :meth:`~.HttpClient.batch_execute` could
be a mixture of :class:`~.HttpResponse` and :class:`web_poet.exceptions.http.HttpRequestError`.

Here's an example:

.. code-block:: python

    # Revised code snippet from the to_item() method

    responses: List[Union[web_poet.HttpResponse, web_poet.exceptions.HttpRequestError]] = (
        await self.http_client.batch_execute(*requests, return_exceptions=True)
    )

    related_product_ids = []
    for i, response in enumerate(responses):
        if isinstance(response, web_poet.exceptions.HttpRequestError):
            logger.warning(
                f"Unable to request related products for product ID '{item['product_id']}' "
                f"using this request: {requests[i]}. Reason: {response}."
            )
            continue
        related_product_ids.extend(
            [
                id_
                for product_ids in self.parse_related_product_ids(response)
                for id_ in product_ids
            ]
        )

    item["related_product_ids"].extend(related_product_ids)
    return item

From the example above, we're now checking the list of responses to see if any
exceptions are included in it. If so, we're simply logging it down and ignoring
it. In this way, perfectly good responses can still be processed through.


Behind the curtains
-------------------

All exceptions that the HTTP Downloader Implementation (see :ref:`advanced-downloader-impl`
doc section) explicitly raises when implementing it for **web-poet** should be
:class:`web_poet.exceptions.http.HttpRequestError` *(or a subclass from it)*. 

For frameworks that implement and use **web-poet**, exceptions that ocurred when
handling the additional requests like `connection errors`, `time outs`, `TLS
errors`, etc should be replaced by :class:`web_poet.exceptions.http.HttpRequestError`
by raising it explicitly. For responses that are successful but don't have a ``200``
**status code**, this exception shouldn't be raised at all. Instead, the
:class:`~.HttpResponse` should simply reflect the response contents as is.

This is to ensure that Page Objects having additional requests using the
:class:`~.HttpClient` is able to work in any type of HTTP downloader implementation.

For example, in Python, the common HTTP libraries have different types of base
exceptions when something has ocurred:

    * `aiohttp.ClientError <https://docs.aiohttp.org/en/v3.8.1/client_reference.html?highlight=exceptions#aiohttp.ClientError>`_
    * `requests.RequestException <https://2.python-requests.org/en/master/api/#requests.RequestException>`_
    * `urllib.error.HTTPError <https://docs.python.org/3/library/urllib.error.html#urllib.error.HTTPError>`_

Imagine if Page Objects are **expected** to work in `different` backend implementations
like the ones above, then it would cause the code to look like:

.. code-block:: python

    import attrs
    import web_poet

    import aiohttp
    import requests
    import urllib


    @attrs.define
    class SomePage(web_poet.ItemWebPage):
        http_client: web_poet.HttpClient

        async def to_item(self):
            try:
                response = await self.http_client.get("...")
            except (aiohttp.ClientError, requests.RequestException, urllib.error.HTTPError):
                # handle the error here

Such code could turn messy in no time especially when the number of HTTP backends
that Page Objects **should support** are steadily increasing. This means that Page
Objects aren't truly portable in different types of frameworks or environments.
Rather, they're only limited to work in the specific framework they're supported.

In order for Page Objects to easily work in different Downloader Implementations,
the framework that implements the HTTP Downloader backend should be able to raise
exceptions from the :mod:`web_poet.exceptions.http` module in lieu of the backend
specific ones `(e.g. aiohttp, requests, urllib, etc.)`.

This makes the code much simpler:

.. code-block:: python

    import attrs
    import web_poet


    @attrs.define
    class SomePage(web_poet.ItemWebPage):
        http_client: web_poet.HttpClient

        async def to_item(self):
            try:
                response = await self.http_client.get("...")
            except web_poet.exceptions.HttpRequestError:
                # handle the error here

.. _advanced-downloader-impl:

Downloader Implementation
=========================

Please note that on its own, :class:`~.HttpClient` doesn't do anything. It doesn't
know how to execute the request on its own. Thus, for frameworks or projects
wanting to use additional requests in Page Objects, they need to set the
implementation on how to execute an :class:`~.HttpRequest`.

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
