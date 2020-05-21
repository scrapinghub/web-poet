.. _`from-ground-up`:

===========================
web-poet from the ground up
===========================

This tutorial explains the motivation behind web-poet, and its main
concepts. You would learn

* what are the issues which ``web-poet`` addresses, why does the library exist;
* how ``web-poet`` addresses these issues;
* what is a Page Object, and what is a page object input;
* how are libraries like `scrapy-poet`_ implemented, and what are they for.

Reusable web scraping code
==========================

Forget about web-poet for a minute. Let's say you're writing code to scrape
a book web page from `books.toscrape.com <http://books.toscrape.com/>`_:

.. code-block:: python

    import requests
    import parsel


    def extract_book(url):
        """ Extract book information from a book page on
        http://books.toscrape.com website, e.g. from
        http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
        """
        resp = requests.get(url)
        sel = parsel.Selector(resp)
        return {
            'url': resp.url,
            'title': sel.css('h1').get(),
            'description': sel.css('#product_description+ p').get().strip(),
            # ...
        }

    item = extract_book("http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html")

This is sweet & easy, but you realize this code is tightly coupled, and hardly
reusable or testable. So you refactor it, to separate downloading
from the extraction:

.. code-block:: python

    import requests
    import parsel


    def extract_book(response):
        """ Extract book information from a requests.Response obtained
        from a book page on http://books.toscrape.com website, e.g. from
        http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
        """
        sel = parsel.Selector(response.text)
        return {
            'url': response.url,
            'title': sel.css('h1').get(),
            'description': sel.css('#product_description+ p').get().strip(),
            # ...
        }

    def download_and_extract_book(url):
        resp = requests.get(url)
        return extract_book(resp)

    item = download_and_extract_book("http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html")


Much cleaner! It is slightly more code, but extract_book is more
reusable & testable now.

Then your project evolves, and you realize that you'd like to download
web pages using aiohttp_. It means that ``extract_book`` now can't receive
``requests.Response``, it needs to work with ``aiohttp.Response``.
To complicate things, you want to keep ``requests`` support.
There are few options, such as:

.. _aiohttp: https://github.com/aio-libs/aiohttp

* make ``extract_book`` receive Selector instance
* make ``extract_book`` receive url and unicode response body
* make ``extract_book`` receive a Response object which is compatible
  for both libraries.

No problem, let's refactor it further. You may end up with something like that:

.. code-block:: python


    import requests
    import parsel

    # === Extraction code
    def extract_book(url, text):
        """ Extract book information from a book page
        on http://books.toscrape.com website, e.g. from
        http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
        """
        sel = parsel.Selector(text)
        return {
            'url': url,
            'title': sel.css('h1').get(),
            'description': sel.css('#product_description+ p').get().strip(),
            # ...
        }

    # === Framework-specific I/O code
    def download_sync(url):
        resp = requests.get(url)
        return {'url': resp.url, 'text': resp.text}

    async def download_async(session, url):
        async with session.get(url) as resp:
            text = await resp.text()
        return {'url': resp.url, 'text': text}

    # === Usage example
    # the way to get resp_data depends on an HTTP client
    resp_data = download_sync("http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html")

    # but after we got resp_data, usage is the same
    item = extract_book(url=resp_data['url'], text=resp_data['text'])


``extract_book`` function now has all the desired properties: it is
easily testable and reusable, and it works with any method of
downloading data.

The same, but using web-poet
============================

``web-poet`` asks you to organize code in a very similar way. Let's convert
``extract_book`` function to a Page Object, by defining BookPage class:

.. code-block:: python

    import requests
    from web_poet import WebPage, ResponseData


    # === Extraction code
    class BookPage(WebPage):
        """ A book page on http://books.toscrape.com website, e.g.
        http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
        """
        def extract_book(self):
            return {
                'url': self.url,
                'title': self.css('h1').get(),
                'description': self.css('#product_description+ p').get().strip(),
                # ...
            }


    # === Framework-specific I/O code
    def download_sync(url):
        resp = requests.get(url)
        return ResponseData(url=resp.url, html=resp.text)

    async def download_async(session, url):
        async with session.get(url) as resp:
            text = await resp.text()
        return ResponseData(url=resp.url, html=text)

    # === Usage example

    # the way to get resp_data depends on an HTTP client
    resp_data = download_sync("http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html")

    # but after we got resp_data, usage is the same
    book_page = BookPage(response=resp_data)
    item = book_page.extract_book()

Differences from a previous example:

* instead of dicts with "url" and "text" fields, :class:`~.ResponseData`
  instances are used. :class:`~.ResponseData` is a simple structure with
  two fields ("url" and "html"), defined by web-poet;
  it is just a data container which standardizes the field names and
  the meaning of these fields.
* instead of ``extract_book`` function we got ``BookPage`` class,
  which receives response data in its ``__init__`` method - see how it
  is created: ``BookPage(response=resp_data)``.
* ``BookPage`` inherits from :class:`~.WebPage` base class. This base class
  is not doing much: it

     * defines ``__init__`` method which receives :class:`~.ResponseData`, and
     * provides shortcut methods like :meth:`~.WebPage.css`, which work by
       creating parsel.Selector behind the scenes (so that you don't
       need to create a selector in the ``extract_book`` method).

There are pros and cons for using classes vs functions for writing
such extraction code, but the distinction is not that important;
web-poet uses classes at the moment.

to_item() method
================

It is common to have Page Objects for a web page where a single main
data record needs to be extracted (e.g. book information in our example).
``web-poet`` standardizes this, by asking to name a method implementing the
extraction ``to_item``. It also provides the :class:`~.ItemWebPage` base class
and the :class:`ItemPage` mixin, which ensure the ``to_item`` method
is implemented. Let's change the code to follow this standard:

.. code-block:: python

    import requests
    from web_poet import ItemWebPage, ResponseData


    # === Extraction code
    class BookPage(ItemWebPage):
        """ A book page on http://books.toscrape.com website, e.g.
        http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
        """
        def to_item(self):
            return {
                'url': self.url,
                'title': self.css('h1').get(),
                'description': self.css('#product_description+ p').get().strip(),
                # ...
            }

    # ... get resp_data somehow
    book_page = BookPage(response=resp_data)
    item = book_page.to_item()

As the method name is now standardized, the code which creates a Page Object
instance can now work for other Page Objects like that. For example, you can
have ``ToscrapeBookPage`` and ``BamazonBookPage`` classes, and

.. code-block:: python

    def get_item(page_cls: ItemWebPage, resp_data: ResponseData) -> dict:
        page = page_cls(response=resp_data)
        return page.to_item()

would work for both.

But wait. Before the example was converted to ``web-poet``, we were getting
it for free:

.. code-block:: python

    def get_item(extract_func, resp_data: ResponseData) -> dict:
        return extract_func(url=resp_data.url, html=resp_data.html)

No need to agree on ``to_item`` name and have a base class to check that the
method is implemented. Why bother with classes then?

Classes for web scraping code
=============================

A matter of preference. Functions are great, too.
Classes sometimes can make it a easier to organize web scraping code.
For example, we can extract logic for different attributes into properties:

.. code-block:: python

    class BookPage(ItemWebPage):
        """ A book page on http://books.toscrape.com website, e.g.
        http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
        """

        @property
        def title(self):
            return self.css('h1').get()

        @property
        def description(self):
            return self.css('#product_description+ p').get().strip()

        def to_item(self):
            return {
                'url': self.url,
                'title': self.title,
                'description': self.description,
                # ...
            }

You may write some base class to make it nicer - e.g. helper descriptors
to define properties from CSS selectors, and a default ``to_item``
implementation (so, no need to define ``to_item``).
This is currently not implemented in ``web-poet``, but
nothing prevents us from having a DSL like this:

.. code-block:: python

    class BookPage(ItemWebPage):
        title = Css('h1')
        description = Css('#product_description+ p') | Strip()
        url = TakeUrl()

Another, and probably a more important reason to consider classes for the
extraction code, is that sometimes there is no a single "main" method,
but you still want to group the related code.
For example, you may define a "Pagination" page object:

.. code-block:: python

    class Pagination(WebPage):

        def page_urls(self):
            # ...

        def prev_url(self):
            # ...

        def next_url(self):
            # ...

or a Listing page on a web site, where you need to get URLs to individual
pages and pagination URLs:

.. code-block:: python

    class BookListPage(ProductListingPage):
        def item_urls(self):
            return self.css(".product a::attr(href)").getall()

        def page_urls(self):
            return self.css(".paginator a::attr(href)").getall()


Web Scraping Frameworks
=======================

Let's recall the example we started with:

.. code-block:: python

    import requests
    import parsel


    def extract_book(url):
        """ Extract book information from a book page on
        http://books.toscrape.com website, e.g. from
        http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
        """
        resp = requests.get(url)
        sel = parsel.Selector(resp)
        return {
            'url': resp.url,
            'title': sel.css('h1').get(),
            'description': sel.css('#product_description+ p').get().strip(),
            # ...
        }

    item = extract_book("http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html")

And this is what we ended up with:

.. code-block:: python

    import requests
    from web_poet import ItemWebPage, ResponseData


    # === Extraction code
    class BookPage(ItemWebPage):
        """ A book page on http://books.toscrape.com website, e.g.
        http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
        """
        def to_item(self):
            return {
                'url': self.url,
                'title': self.css('h1').get(),
                'description': self.css('#product_description+ p').get().strip(),
                # ...
            }

    # === Framework-specific I/O code
    def download_sync(url):
        resp = requests.get(url)
        return ResponseData(url=resp.url, html=resp.text)

    async def download_async(session, url):
        async with session.get(url) as resp:
            text = await resp.text()
        return ResponseData(url=resp.url, html=text)

    # === Usage example
    def get_item(page_cls: ItemWebPage, resp_data: ResponseData) -> dict:
        page = page_cls(response=resp_data)
        return page.to_item()

    # the way to get resp_data depends on an HTTP client
    resp_data = download_sync("http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html")
    item = get_item(BookPage, resp_data=resp_data)

We created a monster!!! The examples in this tutorial are becoming
longer and longer, harder and harder to understand. What's going on?

To understand better why this is happening, let's check the ``web-poet``
example in more detail. There are 3 main sections:

1. Extraction code
2. Lower-level I/O code
3. "Usage example" - it connects (1) and (2) to get the extracted data.

Extraction code needs to be written for every new web site.
But the I/O code and the "Usage example" can, and should be written only once!

In other words, we've been creating a web scraping framework here, and that's
where most of the complexity is coming from.

In a real world, a developer who needs to extract data from a web page
would only need to write the "extraction" part:

.. code-block:: python

    from web_poet import ItemWebPage

    class BookPage(ItemWebPage):
        """ A book page on http://books.toscrape.com website, e.g.
        http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
        """
        def to_item(self):
            return {
                'url': self.url,
                'title': self.css('h1').get(),
                'description': self.css('#product_description+ p').get().strip(),
                # ...
            }

Then point the framework to the ``BookPage`` class, tell which web page
to process, and that's it.

The role of ``web-poet`` is to define standard on how to write the
extraction logic, and allow it to be reused in different frameworks.
``web-poet`` Page Objects should be flexible enough to be used with

* synchronous or async frameworks, callback-based and
  ``async def / await`` based,
* single node and distributed systems,
* different underlying HTTP implementations - or without HTTP support
  at all, etc.


Page Objects
============

In this document "Page Objects" were casually mentioned a few times, but
what are they?

.. note::
    This term comes from a Page Object design pattern; see a description
    on Martin Fowler's website: https://martinfowler.com/bliki/PageObject.html.
    web-poet page objects are inspired by Martin Fowler's page object,
    but they are not the same.

Essentially, the idea is to create an object which represents a web page
(or a part of web page - see Pagination example), and allows to extract
data from there. Page Object must

1. Define all the inputs needed in its ``__init__`` method.
   Usually these inputs are then stored as attributes.
   For example, ``__init__`` method of :class:`~.WebPage` base class has
   a ``response`` parameter of type :class:`~.ResponseData`, and
   stores it as ``.response`` attribute.
2. Provide methods or properties to extract structured information, using
   the attributes saved in ``__init__``. For example, you may define
   ``.to_item()`` method, and other helper methods; these methods would work
   with ``.response`` attribute, likely through shortcuts like
   ``self.css(...)``.


Page Object Inputs
==================

Here we got to the last, and probably the most complicated and important part
of ``web-poet``. So far we've been passing :class:`~.ResponseData` to
the page objects. But is it enough?

If that'd be enough, there wouldn't be ``web-poet``. We would say "please
write ``def extract(url, html): ...`` functions, and call it a day.

In practice you may need to use other information to extract data from
a web page, not only :class:`~.ResponseData` (which is URL of this page and
its HTTP response body, decoded to unicode). For example, you may want
to

* render a web page in a headless browser like Splash_,
  and use HTML after the rendering (snapshot of a DOM tree);
* query third-party API like AutoExtract_, to extract most of the data
  automatically - a Page Object may just return the result as-is,
  or enrich / post-process it;
* take some state in account, passed e.g. from the crawling code.
* use a combination of inputs: e.g. you may need HTML after
  Headless Chrome rendering + crawling state.

.. _Splash: https://github.com/scrapinghub/splash
.. _AutoExtract: https://scrapinghub.com/automatic-data-extraction-api

The information you need can depend on a web site. For example,
Splash can be required for extracting book information from Bamazon,
while for http://books.toscrape.com you may need HTTP response body
and some crawl state (not really, but let's imagine it is needed).

If we go to the original, non-poetic example, we would have two extract
functions, for Bamazon and for books.toscrape.com:

.. code-block:: python

    # === Extraction code
    def extract_book_toscrape(html, crawl_state):
        # ...

    def extract_book_bamazon(html):
        # ...

    # === Framework-specific I/O code
    def download_sync(url):
        resp = requests.get(url)
        return {'url': resp.url, 'text': resp.text}

    async def download_async(session, url):
        # ...

    # === Usage example
    # The way to get inputs to the extraction function depends
    # on an environment (e.g. an HTTP client or a framework used),
    # but which inputs to compute depends on the extraction function.
    resp_data = download_sync("http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html")
    crawl_state = {"seed": "http://books.toscrape.com/catalogue/category/books/poetry_23/index.html"}

    # How to call the extraction function depends on the extraction function,
    # as arguments are not the same.
    item = extract_book_toscrape(
        html=resp_data['text'],
        crawl_state=crawl_state
    )

Previously we decoupled "Extraction code" section from the
"Framework-specific I/O code" section. But how can we
decouple "Extraction code" from the "Usage example", how do we actually
call the extraction code in a generic way? Is it possible to have a method
like the following?

.. code-block:: python

    def get_item(url, extraction_func):
        # TODO: build kwargs with all the inputs needed
        return extraction_func(**kwargs)

    item = get_item("http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
                    extraction_func=extract_book_toscrape)

It was kind-of decoupled before, as extraction code has been always receiving
"text" and "url":

.. code-block:: python

    def get_item(url, extraction_func):
        resp_data = download_sync(url)
        kwargs = dict(text=resp_data['text'], url=resp_data['url'])
        return extraction_func(**kwargs)

But now it gets complicated:

* Caller code can't pass "url" and "text" arguments always,
  function arguments can vary.
* To call these functions, their arguments need to be created first.
  Some of the possible inputs can be resource-intensive to create
  (e.g. headless browser response); they shouldn't be created, unless asked.
* in case of ``extract_book_toscrape`` "html" should be downloaded directly;
  in case of ``extract_book_bamazon`` output of a headless browser
  (Splash in particular) is expected.

Ideally, we would like to

1. Write extraction code which defines the inputs it needs
   (such as "body of HTTP response", "Chrome DOM tree snapshot",
   "crawl state"). The extraction code shouldn't fetch these inputs itself,
   it should receive them, for better testability and reusability.
2. Be able to create the inputs in different ways. For example, for tests it
   can be static data, in Scrapy necessary HTTP requests can be made through
   Scrapy, and in simple scripts data can be fetched using ``requests``
   library.
3. Figure out automatically which inputs the extraction code needs.
   Create (maybe fetch) them in a way specific for an environment -
   e.g. using Scrapy if a page object is used with Scrapy. Call the
   extraction code, passing it all the input data needed.

``web-poet``'s approach for this is the following:

1. Page Objects define which inputs they need by using type annotations
   in ``__init__`` methods. For example, :class:`~.WebPage` asks for
   ``response`` argument of a type :class:`~.ResponseData` in its
   ``__init__`` method.

   .. code-block:: python

        class WebPage(Injectable):
            def __init__(self, response: ResponseData):
                self.response = ResponseData
                super().__init__()

   What to pass is specified as a type annotation. Argument name doesn't
   matter.

2. It is a responsibility of a framework (caller) to inspect a Page Object,
   figure out what it needs, create all necessary inputs, and
   create the instance.
   For example, web-poet + Scrapy integration package (scrapy-poet_)
   may inspect a WebPage subclass you defined, figure out it needs
   :class:`~.ResponseData` and nothing else, fetch scrapy's TextResponse,
   create ``ResponseData`` instance from it, and finally create your
   Page Object instance.

.. note::

    If it sounds like Dependency Injection, you're right.

To help developing such frameworks there is an andi_ library, which allows
to inspect function signatures and create a plan on how to satisfy the
dependencies. For example, scrapy-poet_ uses andi_.

``web-poet`` is not using andi_ on its own; ``web-poet``'s role
is mostly to standardize things + provide some helpers to write the
extraction code easier.

``web-poet``'s goal is to standardize:

1. A list of possible inputs for the page objects. This helps with
   reusability of extraction code across different environments. For example,
   if you want to support extraction from raw HTTP response bodies, you
   need to figure out how to populate :class:`~.ResponseData` in the
   given environment, and that's all.

   Users are free to define their own inputs, but they may be less portable
   across environments.

   Currently only :class:`~.ResponseData` is defined in web-poet.

2. Interface for the Page Object itself. This allows to have a code which can
   instantiate and use a Page Object without knowing about its
   implementation upfront. ``web-poet`` requires you to use a base class,
   and defines the semantics of ``to_item()`` method.


.. _scrapy-poet: https://github.com/scrapinghub/scrapy-poet
.. _andi: https://github.com/scrapinghub/andi

Summary
=======

First, congratulations for making it through this document!

A take-away from this tutorial:

1. ``web-poet`` does very little on its own. Almost nothing, really.
   An important thing about ``web-poet`` is that if defines a standard
   for writing web scraping code.

   All these Page Objects are just Python classes, which receive some
   static data in ``__init__`` methods, and maybe provide some methods to
   extract the data.

2. ``web-poet`` prescribes certain things and limits what you can do,
   but not too much, and as a return you're getting better testability
   and reusability of your code.

3. Basic ``web-poet`` usage looks similar to how one could have had
   refactored the extraction code anyways.

