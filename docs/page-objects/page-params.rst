.. _page-params:

=================
Using page params
=================

In some cases, Page Objects might require additional information to be passed to
them. Such information can dictate the behavior of the Page Object or affect its
data entirely depending on the needs of the developer.

If you can recall from the previous basic tutorials, one essential requirement of
Page Objects that inherit from :class:`~.WebPage` would
be :class:`~.HttpResponse`. This holds the HTTP response information that the
Page Object is trying to represent.

In order to standardize how to pass arbitrary information inside Page Objects,
we'll need to use :class:`~.PageParams` similar on how we use
:class:`~.HttpResponse` as a requirement to instantiate Page Objects:

.. code-block:: python

    import attrs
    import web_poet

    @attrs.define
    class SomePage(web_poet.WebPage):
        # The HttpResponse attribute is inherited from WebPage
        page_params: web_poet.PageParams

    # Assume that it's constructed with the necessary arguments taken somewhere.
    response = web_poet.HttpResponse(...)

    # It uses Python's dict interface.
    page_params = web_poet.PageParams({"arbitrary_value": 1234, "cool": True})

    page = SomePage(response=response, page_params=page_params)

However, similar with :class:`~.HttpResponse`, developers using
:class:`~.PageParams` shouldn't care about how they are being passed into Page
Objects. This will depend on the framework that would use **web-poet**.

Let's checkout some examples on how to use it inside a Page Object.

Controlling item values
-----------------------

.. code-block:: python

    import attrs
    import web_poet


    @attrs.define
    class ProductPage(web_poet.WebPage):
        page_params: web_poet.PageParams

        default_tax_rate = 0.10

        def to_item(self):
            item = {
                "url": self.url,
                "name": self.css("#main h3.name ::text").get(),
                "price": self.css("#main .price ::text").get(),
            }
            self.calculate_price_with_tax(item)
            return item

        @staticmethod
        def calculate_price_with_tax(item):
            tax_rate = self.page_params.get("tax_rate") or self.default_tax_rate
            item["price_with_tax"] = item["price"] * (1 + tax_rate)


From the example above, we were able to provide an optional information regarding
the **tax rate** of the product. This could be useful when trying to support
the different tax rates for each state or territory. However, since we're treating
the **tax_rate** as optional information, notice that we also have a the
``default_tax_rate`` as a backup value just in case it's not available.


Controlling Page Object behavior
--------------------------------

Let's try an example wherein :class:`~.PageParams` is able to control how
:ref:`additional-requests` are being used. Specifically, we are going to use
:class:`~.PageParams` to control the number of paginations being made.

.. code-block:: python

    from typing import List

    import attrs
    import web_poet


    @attrs.define
    class ProductPage(web_poet.WebPage):
        http: web_poet.HttpClient
        page_params: web_poet.PageParams

        default_max_pages = 5

        async def to_item(self):
            return {"product_urls": await self.get_product_urls()}

        async def get_product_urls(self) -> List[str]:
            # Simulates scrolling to the bottom of the page to load the next
            # set of items in an "Infinite Scrolling" category list page.
            max_pages = self.page_params.get("max_pages") or self.default_max_pages
            requests = [
                self.create_next_page_request(page_num)
                for page_num in range(2, max_pages + 1)
            ]
            responses = await http.batch_execute(*requests)
            return [
                url
                for response in responses
                for product_urls in self.parse_product_urls(response)
                for url in product_urls
            ]

        @staticmethod
        def create_next_page_request(page_num):
            next_page_url = f"https://example.com/category/products?page={page_num}"
            return web_poet.Request(url=next_page_url)

        @staticmethod
        def parse_product_urls(response: web_poet.HttpResponse):
            return response.css("#main .products a.link ::attr(href)").getall()

From the example above, we can see how :class:`~.PageParams` is able to
arbitrarily limit the pagination behavior by passing an optional **max_pages**
info. Take note that a ``default_max_pages`` value is also present in the Page
Object in case the :class:`~.PageParams` instance did not provide it.
