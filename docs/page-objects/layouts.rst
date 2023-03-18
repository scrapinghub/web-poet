.. _layouts:

===============
Webpage layouts
===============

Different webpages may show the same *type* of page, but different *data*. For
example, in an e-commerce website there are usually many product detail pages,
each showing data from a different product.

The code that those webpages have in common is their **webpage layout**.

Coding for webpage layouts
==========================

Webpage layouts should inform how you organize your data extraction code.

A good practice to keep your code maintainable is to have a separate :ref:`page
object class <page-objects>` per webpage layout.

Trying to support multiple webpage layouts with the same page object class can
make your class hard to maintain.


Identifying webpage layouts
===========================

There is no precise way to determine whether 2 webpages have the same or a
different webpage layout. You must decide based on what you know, and be ready
to adapt if things change.

It is also often difficult to identify webpage layouts before you start writing
extraction code. Completely different webpage layouts can have the same look,
and very similar webpage layouts can look completely different.

It can be a good starting point to assume that, for a given combination of
data type and website, there is going to be a single webpage layout. For
example, assume that all product pages of a given e-commerce website will have
the same webpage layout.

Then, as you write a :ref:`page object class <page-objects>` for that webpage
layout, you may find out more, and adapt.

When the same piece of information must be extracted from a different place for
different webpages, that is a sign that you may be dealing with more than 1
webpage layout. For example, if on some webpages the product name is in an
``h1`` element, but on some webpages it is in an ``h2`` element, chances are
there are at least 2 different webpage layouts.

However, whether you continue to work as if everything uses the same webpage
layout, or you split your page object class into 2 page object classes, each
targeting one of the webpage layouts you have found, it is entirely up to you.

Ask yourself: Is supporting all webpage layout differences making your page
object class implementation only a few lines of code longer, or is it making it
an unmaintainable bowl of spaghetti code?


Mapping webpage layouts
=======================

Once you have written a :ref:`page object class <page-objects>` for a webpage
layout, you need to make it so that your page object class is used for webpages
that use that webpage layout.

URL patterns
------------

Webpage layouts are often associated to specific URL patterns. For example, all
the product detail pages of an e-commerce website usually have similar URLs,
such as ``https://example.com/product/<product ID>``.

When that is the case, you can :ref:`associate your page object class to the
corresponding URL pattern <rules-intro>`.


.. _multi-layout:

Multi-layout page object classes
--------------------------------

Sometimes it is impossible to know, based on the target URL, which webpage
layout you are getting. For example, during `A/B testing`_, you could get a
random webpage layout on every request.

.. _A/B testing: https://en.wikipedia.org/wiki/A/B_testing

For these scenarios, we recommend that you create different page object classes
for the different layouts that you may get, and then write a special
“multi-layout” page object class, and use it to select the right page object
class at run time based on the input you receive.

Your multi-layout page object class should:

#.  Declare attributes for the input that you will need to determine which page
    object class to use.

    For example, declare an :class:`HttpResponse` attribute to select a page
    object class based on the response content:

    .. code-block:: python

       class MyMultiLayoutPage(ItemPage):
           response: HttpResponse
           ...

#.  Declare an attribute for every page object class that you may use depending
    on which webpage layout you get from the target website.

    They all should return the same type of :ref:`item <item-classes>` as your
    multi-layout page object class.

    For example:

    .. code-block:: python

       class MyItem:
           ...

       @attrs.define
       class MyPage1(ItemPage[MyItem]):
           ...

       @attrs.define
       class MyPage2(ItemPage[MyItem]):
           ...

       @attrs.define
       class MyMultiLayoutPage(ItemPage[MyItem]):
           ...
           page1: MyPage1
           page2: MyPage2

    Note that all inputs of all those page object classes will be resolved and
    requested along with the input of your multi-layout page object class.

    For example, given:

    .. code-block:: python

       @attrs.define
       class MyPage1(ItemPage):
           response: HttpResponse

       @attrs.define
       class MyPage2(ItemPage):
           response: BrowserHtml

       @attrs.define
       class MyMultiLayoutPage(ItemPage):
           response: HttpResponse
           page1: MyPage1
           page2: MyPage2

    Using ``MyMultiLayoutPage`` causes the use of both ``HttpResponse`` and
    ``BrowserHtml``, because ``MyMultiLayoutPage`` requires ``MyPage2``, and
    ``MyPage2`` requires ``BrowserHtml``.

    If combining different inputs is a problem, consider refactoring your page
    object classes to require similar inputs.

#.  On its :meth:`~web_poet.pages.ItemPage.to_item` method:

    #.  Determine, based on inputs, which page object to use.

    #.  Return the output of the :meth:`~web_poet.pages.ItemPage.to_item`
        method of that page object.

    For example:

    .. code-block:: python

       @attrs.define
       class MyMultiLayoutPage(ItemPage[MyItem]):
           response: HttpResponse
           page1: MyPage1
           page2: MyPage2

           async def to_item(self) -> MyItem:
               if self.response.css(".foo"):
                   page_object = self.page1
               else:
                   page_object = self.page2
               return await page_object.to_item()

You may use :class:`~web_poet.pages.MultiLayoutPage` as a base class for your
multi-layout page object class, so you only need to implement the
:class:`~web_poet.pages.MultiLayoutPage.get_layout` method that determines
which page object to use. For example:

.. code-block:: python

   from typing import Optional

   import attrs
   from web_poet import handle_urls, HttpResponse, ItemPage, MultiLayoutPage, WebPage


   @attrs.define
   class Header:
       text: str


   class H1Page(WebPage[Header]):

       @field
       def text(self) -> Optional[str]:
           return self.css("h1::text").get()


   class H2Page(WebPage[Header]):

       @field
       def text(self) -> Optional[str]:
           return self.css("h2::text").get()


   @handle_urls("example.com")
   @attrs.define
   class HeaderMultiLayoutPage(MultiLayoutPage[Header]):
       response: HttpResponse
       h1: H1Page
       h2: H2Page

       async def get_layout(self) -> ItemPage[Header]:
           if self.response.css("h1::text"):
               return self.h1
           return self.h2

.. note:: If you use :func:`~web_poet.handle_urls` both for your multi-layout
          page object class and for any of the page object classes that it
          uses, you may need to :ref:`grant your multi-layout page object class
          a higher priority <rules-priority-resolution>`.
