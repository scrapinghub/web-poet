=======
web-poet
=======

.. image:: https://img.shields.io/pypi/v/web-poet.svg
   :target: https://pypi.python.org/pypi/web-poet
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/web-poet.svg
   :target: https://pypi.python.org/pypi/web-poet
   :alt: Supported Python Versions

.. image:: https://travis-ci.org/victor-torres/web-poet.svg?branch=master
   :target: https://travis-ci.org/victor-torres/web-poet
   :alt: Build Status

.. image:: https://codecov.io/github/victor-torres/web-poet/coverage.svg?branch=master
   :target: https://codecov.io/gh/victor-torres/web-poet
   :alt: Coverage report

.. warning::
    Current status is "experimental".

``web-poet`` implements Page Object pattern for web scraping.

License is BSD 3-clause.

Installation
============

::

    pip install web-poet

Usage
=====

Check the following script that uses ``urllib.request`` to query data from
`books.toscrape.com`_.

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

Output should be similar to this:

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

.. _`books.toscrape.com`: http://books.toscrape.com
