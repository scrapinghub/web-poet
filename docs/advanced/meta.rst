.. _`advanced-meta`:

============================
Passing information via Meta
============================

In some cases, Page Objects might require additional information to be passed to
them. Such information can dictate the behavior of the Page Object or affect its
data entirely depending on the needs of the developer.

If you can recall from the previous basic tutorials, one essential requirement of
Page Objects that inherit from :class:`~.WebPage` or :class:`~.ItemWebPage` would
be :class:`~.ResponseData`. This holds the HTTP response information that the
Page Object is trying to represent.

In order to standardize how to pass arbitrary information inside Page Objects,
we'll need to use :class:`~.Meta` similar on how we use :class:`~.ResponseData`
as a requirement to instantiate Page Objects:

.. code-block:: python

    import attr
    import web_poet

    @attr.define
    class SomePage(web_poet.ItemWebPage):
        # ResponseData is inherited from ItemWebPage
        meta: web_poet.Meta

    response = web_poet.ResponseData(...)
    meta = web_poet.Meta("arbitrary_value": 1234, "cool": True)

    page = SomePage(response=response, meta=meta)

However, similar with :class:`~.ResponseData`, developers using :class:`~.Meta`
shouldn't care about how they are being passed into Page Objects. This will
depend on the framework that would use **web-poet**.

Let's checkout some examples on how to use it inside a Page Object.

Controlling item values
-----------------------

.. code-block:: python

    import attr
    import web_poet


    @attr.define
    class ProductPage(web_poet.ItemWebPage):
        meta: web_poet.Meta

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
            tax_rate = self.meta.get("tax_rate") or self.default_tax_rate
            item["price_with_tax"] = item["price"] * (1 + tax_rate)


From the example above, we were able to provide an optional information regarding
the **tax rate** of the product. This could be useful when trying to support
the different tax rates for each state or territory. However, since we're treating
the **tax_rate** as optional information, notice that we also have a the
``default_tax_rate`` as a backup value just in case it's not available.


Controlling Page Object behavior
--------------------------------

Let's try an example wherein :class:`~.Meta` is able to control how 
:ref:`advanced-requests` are being used. Specifically, we are going to use
:class:`~.Meta` to control the number of paginations being made.

.. code-block:: python

    from typing import List

    import attr
    import web_poet


    @attr.define
    class ProductPage(web_poet.ItemWebPage):
        http_client: web_poet.HttpClient
        meta: web_poet.Meta

        default_max_pages = 5

        async def to_item(self):
            return {"product_urls": await self.get_product_urls()}

        async def get_product_urls(self) -> List[str]:
            # Simulates scrolling to the bottom of the page to load the next
            # set of items in an "Infinite Scrolling" category list page.
            max_pages = self.meta.get("max_pages") or self.default_max_pages
            requests = [
                self.create_next_page_request(page_num)
                for page_num in range(2, max_pages + 1)
            ]
            responses = await http_client.batch_requests(*requests)
            pages = [self] + list(map(web_poet.WebPage, responses))
            return [
                product_url
                for page in pages
                for product_url in self.parse_product_urls(page)
            ]

        @staticmethod
        def create_next_page_request(page_num):
            next_page_url = f"https://example.com/category/products?page={page_num}"
            return web_poet.Request(url=next_page_url)

        @staticmethod
        def parse_product_urls(page):
            return page.css("#main .products a.link ::attr(href)").getall()

From the example above, we can see how :class:`~.Meta` is able to arbitrarily
limit the pagination behavior by passing an optional **max_pages** info. Take
note that a ``default_max_pages`` value is also present in the Page Object in
case the :class:`~.Meta` instance did not provide it.

Value Restrictions
------------------

From the examples above, you may notice that we can access :class:`~.Meta` with
a ``dict`` interface since it's simply a subclass of it. However, :class:`~.Meta`
posses some extendable features on top of being a ``dict``.

Specifically, :class:`~.Meta` is able to restrict any value passed based on its
type. For example, if any of these values are passed, then a ``ValueError`` is
raised:

    * module
    * class
    * method or function
    * generator
    * coroutine or awaitable
    * traceback
    * frame

This is to ensure that frameworks using **web-poet** are able safely use values
passed into :class:`~.Meta` as they could be passed via CLI, web forms, HTTP API
calls, etc.
