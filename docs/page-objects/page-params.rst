.. _page-params:

=================
Using page params
=================

In some cases, :ref:`page object classes <page-objects>` might require or allow
parameters from the calling code, e.g. to change their behavior or make
optimizations.

To support parameters, add :class:`~.PageParams` to your :ref:`inputs
<inputs>`:

.. code-block:: python

    import attrs
    from web_poet import PageParams, WebPage


    @attrs.define
    class MyPage(WebPage):
        page_params: PageParams

In your page object class, you can read parameters from a :class:`~.PageParams`
object as you would from a :class:`dict`:

.. code-block:: python

    foo = self.page_params["foo"]
    bar = self.page_params.get("bar", "default")

The way the calling code sets those parameters depends on your :ref:`web-poet
framework <frameworks>`.

Example: Controlling item values
================================

.. code-block:: python

    import attrs
    import web_poet
    from web_poet import validates_input


    @attrs.define
    class ProductPage(web_poet.WebPage):
        page_params: web_poet.PageParams

        default_tax_rate = 0.10

        @validates_input
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
            tax_rate = self.page_params.get("tax_rate", self.default_tax_rate)
            item["price_with_tax"] = item["price"] * (1 + tax_rate)


From the example above, we were able to provide an optional information regarding
the **tax rate** of the product. This could be useful when trying to support
the different tax rates for each state or territory. However, since we're treating
the **tax_rate** as optional information, notice that we also have a the
``default_tax_rate`` as a backup value just in case it's not available.


Example: Controlling page object behavior
=========================================

Let's try an example wherein :class:`~.PageParams` is able to control how
:ref:`additional requests <additional-requests>` are being used. Specifically,
we are going to use :class:`~.PageParams` to control the number of pages
visited.

.. code-block:: python

    from typing import List

    import attrs
    import web_poet
    from web_poet import validates_input


    @attrs.define
    class ProductPage(web_poet.WebPage):
        http: web_poet.HttpClient
        page_params: web_poet.PageParams

        default_max_pages = 5

        @validates_input
        async def to_item(self):
            return {"product_urls": await self.get_product_urls()}

        async def get_product_urls(self) -> List[str]:
            # Simulates scrolling to the bottom of the page to load the next
            # set of items in an "Infinite Scrolling" category list page.
            max_pages = self.page_params.get("max_pages", self.default_max_pages)
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
info. Take note that a ``default_max_pages`` value is also present in the page
object class in case the :class:`~.PageParams` instance did not provide it.
