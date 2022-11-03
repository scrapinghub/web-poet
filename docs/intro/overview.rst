========
Overview
========

A good web scraping framework helps you keep your code maintainable by, among
other things, enabling and encouraging `separation of concerns`_.

.. _separation of concerns: https://en.wikipedia.org/wiki/Separation_of_concerns

For example, Scrapy_ lets you implement different aspects of web scraping, like
ban avoidance or data delivery, into separate components.

.. _Scrapy: https://scrapy.org/

However, there are 2 core aspects of web scraping that can be hard to decouple:
*crawling*, i.e. visiting URLs, and *parsing*, i.e. extracting data.

web-poet lets you :ref:`write data extraction code <page-objects>` that:

-   Makes your web scraping code easier to maintain, since your data extraction
    and crawling code are no longer intertwined and can be maintained
    separately.

-   Can be reused with different versions of your crawling code, i.e. with
    different crawling strategies.

-   Can be executed independently of your crawling code, enabling easier
    debugging and easier automated testing.

-   Can be used with any Python web scraping framework or library that
    implements the :ref:`web-poet specification <frameworks>`, either directly
    or through a third-party plugin.
