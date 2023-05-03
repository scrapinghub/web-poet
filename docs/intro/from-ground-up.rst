.. _from-ground-up:

==================
From the ground up
==================

Learn why and how web-poet came to be as you transform a simple, rigid starting
web scraping code snippet into maintainable, reusable web-poet code.

Writing reusable parsing code
=============================

Imagine you are writing code to scrape a book web page from
`books.toscrape.com <http://books.toscrape.com/>`_, and you implement a
``scrape`` function like this:

.. code-block:: python

    import requests
    from parsel import Selector


    def scrape(url: str) -> dict:
        response = requests.get(url)
        selector = Selector(response.text)
        return {
            "url": response.url,
            "title": selector.css("h1").get(),
        }

    item = scrape("http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html")

This ``scrape`` function is simple, but it has a big issue: it only supports
downloading the specified URL using the requests_ library. What if you want to
use aiohttp_, for concurrency support? What if you want to run ``scrape`` with
a local snapshot of a URL response, to write an automated test for ``scrape``
that does not rely on a network connection?

.. _aiohttp: https://github.com/aio-libs/aiohttp
.. _requests: https://requests.readthedocs.io/en/latest/

The first step towards addressing this issue is to split your ``scrape``
function into 2 separate functions, ``download`` and ``parse``:

.. code-block:: python

    import requests
    from parsel import Selector


    def parse(response: requests.Response) -> dict:
        selector = Selector(response.text)
        return {
            "url": response.url,
            "title": selector.css("h1").get(),
        }

    def download(url: str) -> requests.Response:
        return requests.get(url)

    url = "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    response = download(url)
    item = parse(response)

Now that ``download`` and ``parse`` are separate functions, you can replace
``download`` with an alternative implementation that uses aiohttp_, or that
reads from local files.

There is still an issue, though: ``parse`` expects an instance of
`requests.Response`_. Any alternative implementation of ``download`` would need
to create a response object of the same type, forcing a dependency on
requests_ even if downloads are handled with a different library.

.. _requests.Response: https://requests.readthedocs.io/en/latest/api/#requests.Response

So you need to change the input of the ``parse`` function into something that
will not tie you to a specific download library. One option is to create your
own, download-independent ``Response`` class, to store the response data that
any download function should be able to provide:

.. code-block:: python

    import requests
    from dataclasses import dataclass
    from parsel import Selector


    @dataclass
    class Response:
        url: str
        text: str


    def parse(response: Response) -> dict:
        selector = Selector(response.text)
        return {
            "url": response.url,
            "title": selector.css("h1").get(),
        }


    def download(url: str) -> Response:
        response = requests.get(url)
        return Response(url=response.url, text=response.text)


    url = "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    response = download(url)
    item = parse(response)


The ``parse`` function is no longer tied to any specific download library, and
alternative versions of the ``download`` function can be implemented with other
libraries.


Parsing with web-poet
=====================

web-poet asks you to organize your code in a very similar way. Let’s convert
the ``parse`` function into a :ref:`web-poet page object class
<page-object-classes>`:

.. code-block:: python

    import requests
    from web_poet import Injectable, HttpResponse


    class BookPage(Injectable):
        def __init__(self, response: HttpResponse):
            self.response = response

        def to_item(self) -> dict:
            return {
                "url": self.response.url,
                "title": self.response.css("h1").get(),
            }


    def download(url: str) -> Response:
        response = requests.get(url)
        return HttpResponse(
            url=response.url,
            body=response.content,
            headers=response.headers,
        )


    url = "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    response = download(url)
    book_page = BookPage(response=response)
    item = book_page.to_item()


Differences from a previous example:

-   web-poet provides a standard :class:`~.HttpResponse` class, with helper
    methods like :meth:`~.HttpResponse.css`.

    Note how headers are passed when creating an :class:`~.HttpResponse`
    instance. This is needed to properly decode the body (which is ``bytes``)
    as text using web browser rules. It involves checking the
    ``Content-Encoding``  header, HTML meta tags, BOM markers in the body, etc.

-   Instead of the ``parse`` function we've got a ``BookPage`` class, which
    inherits from the :class:`~.Injectable` base class, receives response data
    in its ``__init__`` method, and returns the extracted item in the
    ``to_item()`` method. ``to_item`` is a standard method name used by
    ``web-poet``.

Receiving a ``response`` argument in ``__init__`` is very common for page
objects, so ``web-poet`` provides a shortcut for it: inherit from
:class:`~.WebPage`, which provides this ``__init__`` method implementation. You
can then refactor your ``BookPage`` class as follows:

.. code-block:: python

    from web_poet import WebPage

    class BookPage(WebPage):
        def to_item(self) -> dict:
            return {
                "url": self.response.url,
                "title": self.response.css("h1").get(),
            }

:class:`~.WebPage` even provides shortcuts for some response attributes and
methods:

.. code-block:: python

    from web_poet import WebPage

    class BookPage(WebPage):
        def to_item(self) -> dict:
            return {
                "url": self.url,
                "title": self.css("h1").get(),
            }

At this point you may be wondering why web-poet requires you to write a class
with a ``to_item`` method rather than a function. The answer is flexibility.

For example, the use of a class instead of a function makes :ref:`fields
<fields>` possible, which make parsing code easier to read:

.. code-block:: python

    from web_poet import WebPage, field


    class BookPage(WebPage):
        @field
        def url(self):
            return self.url

        @field
        def title(self):
            return self.css("h1").get()

Using fields also makes it unnecessary to define ``to_item()`` manually, and
allows reading individual fields when you don't need the complete ``to_item()``
output.

.. note::
    The ``BookPage.to_item()`` method is ``async`` in the example above. See
    :ref:`fields` for more information.

Using classes also makes it easy, for example, to implement dependency
injection, which is how web-poet builds :ref:`inputs <inputs>`.


Downloading with web-poet
=========================

What about the implementation of the ``download`` function? How would you
implement that in web-poet? Well, ideally, you wouldn’t.

To parse data from a web page using web-poet, you would only need to write the
parsing part, e.g. the ``BookPage`` :ref:`page object class
<page-object-classes>` above.

Then, you let a :ref:`web-poet framework <frameworks>` handle the download part
for you. You pass that framework the URL of a web page to parse, and either a
page object class (the ``BookPage`` class here) or an :ref:`item class
<items>`, and that's it:

.. code-block:: python

    item = some_framework.get(url, BookPage)

web-poet does *not* provide any framework, beyond :ref:`an example one featured
in the tutorial <tutorial-create-page-object>` and not intended for production.
The role of web-poet is to define a specification on how to write parsing logic
so that it can be reused with different frameworks.

:ref:`Page object classes <page-object-classes>` should be flexible enough to
be used with very different frameworks, including:

-   synchronous or asynchronous frameworks

-   asynchronous frameworks based on callbacks or based on coroutines_
    (``async def / await`` syntax)

    .. _coroutines: https://docs.python.org/3/library/asyncio-task.html

-   single-node and distributed systems

-   different underlying HTTP implementations, or even implementations with no
    HTTP support at all
