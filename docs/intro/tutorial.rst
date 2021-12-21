.. _`intro-tutorial`:

=====================
web-poet on a surface
=====================

In this tutorial, we’ll assume that web-poet is already installed on your
system.

We are going to scrape `books.toscrape.com <http://books.toscrape.com/>`_,
a website that lists books from famous authors.

Creating a Page Object
======================

Let's create a Python file where we'll put our first Page Object implementation.
This Page Object will be responsible for extracting book links from the book
list page on `books.toscrape.com <http://books.toscrape.com/>`_.

.. code-block:: python

    from web_poet.pages import ItemWebPage


    class BookLinksPage(ItemWebPage):

        @property
        def links(self):
            return self.css('.image_container a::attr(href)').getall()

        def to_item(self) -> dict:
            return {
                'links': self.links,
            }

Downloading Response
====================

The ``BookLinksPage`` Page Object requires a :class:`~.ResponseData` with the
book list page content in order to extract the information we need. Let's create
a simple code using :mod:`urllib.request` to download the data.

.. code-block:: python

    import urllib.request


    response = urllib.request.urlopen('http://books.toscrape.com')

Creating Page Input
===================

Now we need to create and populate a :class:`~.ResponseData` instance.

.. code-block:: python

    from web_poet.page_inputs import ResponseData


    response_data = ResponseData(response.url, response.read().decode('utf-8'))
    page = BookLinksPage(response_data)

    print(page.to_item())

Final Result
============

Our simple Python script might look like this:

.. code-block:: python

    import urllib.request

    from web_poet.pages import ItemWebPage
    from web_poet.page_inputs import ResponseData


    class BookLinksPage(ItemWebPage):

        @property
        def links(self):
            return self.css('.image_container a::attr(href)').getall()

        def to_item(self) -> dict:
            return {
                'links': self.links,
            }


    response = urllib.request.urlopen('http://books.toscrape.com')
    response_data = ResponseData(response.url, response.read().decode('utf-8'))
    page = BookLinksPage(response_data)

    print(page.to_item())

And it should output data similar to this:

.. code-block:: python

    {
        'links': [
            'catalogue/a-light-in-the-attic_1000/index.html',
            'catalogue/tipping-the-velvet_999/index.html',
            'catalogue/soumission_998/index.html',
            'catalogue/sharp-objects_997/index.html',
            'catalogue/sapiens-a-brief-history-of-humankind_996/index.html',
            'catalogue/the-requiem-red_995/index.html',
            'catalogue/the-dirty-little-secrets-of-getting-your-dream-job_994/index.html',
            'catalogue/the-coming-woman-a-novel-based-on-the-life-of-the-infamous-feminist-victoria-woodhull_993/index.html',
            'catalogue/the-boys-in-the-boat-nine-americans-and-their-epic-quest-for-gold-at-the-1936-berlin-olympics_992/index.html',
            'catalogue/the-black-maria_991/index.html',
            'catalogue/starving-hearts-triangular-trade-trilogy-1_990/index.html',
            'catalogue/shakespeares-sonnets_989/index.html',
            'catalogue/set-me-free_988/index.html',
            'catalogue/scott-pilgrims-precious-little-life-scott-pilgrim-1_987/index.html',
            'catalogue/rip-it-up-and-start-again_986/index.html',
            'catalogue/our-band-could-be-your-life-scenes-from-the-american-indie-underground-1981-1991_985/index.html',
            'catalogue/olio_984/index.html',
            'catalogue/mesaerion-the-best-science-fiction-stories-1800-1849_983/index.html',
            'catalogue/libertarianism-for-beginners_982/index.html',
            'catalogue/its-only-the-himalayas_981/index.html',
        ]
    }

Next Steps
==========

As you can see, it's possible to use web-poet with built-in libraries such as
:mod:`urllib.request`, but it's also possible to use
:ref:`Scrapy <scrapy:topics-index>` with the help of
`scrapy-poet <https://scrapy-poet.readthedocs.io>`_.

If you want to understand the idea behind web-poet better,
check the :ref:`from-ground-up` tutorial.
