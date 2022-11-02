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
targetting one of the webpage layouts you have found, it is entirely up to you.

Ask yourself: Is supporting all webpage layout differences making your page
object class implementation only a few lines of code longer, or is it making it
an unmaintainable bowl of spagetti code?


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


Switch page object classes
--------------------------

Sometimes it is impossible to know, based on the target URL, which webpage
layout you are getting. For example, during `A/B testing`_, you could get a
random webpage layout on every request.

.. _A/B testing: https://en.wikipedia.org/wiki/A/B_testing

For these scenarios, we recommend that you create a special “switch” page
object class, and use it to switch to the right page object class at run time
based on the input you receive.

Your switch page object class should:

#.  Request all the inputs that the candidate page object classes may need.

    For example, if there are 2 candidate page object classes, and 1 of them
    requires browser HTML as input, while the other one requires an HTTP
    response, your switch page object class must request both.

    If combining different inputs is a problem, consider refactoring the
    candidate page object classes to require similar inputs.

#.  On its :meth:`~web_poet.pages.ItemPage.to_item` method:

    #.  Determine, based on the inputs, which candidate page object class to
        use.

    #.  Create an instance of the selected candidade page object class with the
        necessary input, call its :meth:`~web_poet.pages.ItemPage.to_item`
        method, and return its result.

You may use :class:`~web_poet.pages.SwitchPage` as a base class for your switch
page object class, so you only need to implement the
:class:`~web_poet.pages.SwitchPage.switch` method that determines which
candidate page object class to use. For example:

.. code-block:: python

    import attrs
    from web_poet import handle_urls, HttpResponse, Injectable, ItemPage, SwitchPage


    @attrs.define
    class Header:
        text: str


    @attrs.define
    class H1Page(ItemPage[Header]):
        response: HttpResponse

        @field
        def text(self) -> str:
            return self.response.css("h1::text").get()


    @attrs.define
    class H2Page(ItemPage[Header]):
        response: HttpResponse

        @field
        def text(self) -> str:
            return self.response.css("h2::text").get()


    @handle_urls("example.com")
    @attrs.define
    class HeaderSwitchPage(SwitchPage[Header]):
        response: HttpResponse

        async def switch(self) -> Injectable:
            if self.response.css("h1::text"):
                return H1Page
            return H2Page
