.. _intro-tutorial:
.. _page-objects:

========
Tutorial
========

In this tutorial you will learn to use web-poet as you write web data
extraction code for book detail pages from `books.toscrape.com`_.

.. _books.toscrape.com: http://books.toscrape.com/

To follow this tutorial you must first be familiar with Python_ and
:ref:`install web-poet <install>`.

.. _Python: https://docs.python.org/


Create a project folder
=======================

web-poet does not limit how you structure your web-poet web data extraction
code, beyond the limitations of Python itself.

However, in this tutorial you will use a specific project folder structure
designed with web-poet best practices in mind. Consider using the same project
folder structure in all your web-poet projects.

First create your project folder: ``tutorial-project``.

Within ``tutorial-project``, create:

-   A ``run.py`` file, a file specific to this tutorial where you will put code
    to test the execution of your web data extraction code.

-   A ``tutorial`` folder, where you will place your web data extraction code.

Within ``tutorial-project/tutorial``, create:

-   An ``__init__.py`` file, so that the ``tutorial`` folder becomes an
    importable Python module.

-   An ``items.py`` file, where you will define item classes to store extracted
    data.

-   A ``pages`` folder, where you will define your page object classes.

Within ``tutorial-project/tutorial/pages``, create:

-   An ``__init__.py`` file.

-   A ``books_toscrape_com.py`` file, for page object class code targeting
    `books.toscrape.com`_.

Your project folder should look as follows:

.. code-block:: text

    tutorial-project/
        run.py
        tutorial/
            __init__.py
            items.py
            pages/
                __init__.py
                books_toscrape_com.py


Create an item class
====================

While it is possible to store the extracted data in a Python dictionary, it is
a good practice to create an item class that:

-   Defines the specific attributes that you aim to extract, triggering an
    exception if you extract unintended attributes or fail to extract expected
    attributes.

-   Allows defining default values for some attributes.

web-poet uses itemadapter_ for item class support, which means that any kind of
item class can be used. In this tutorial, you will use attrs_ to define your
item class.

.. _attrs: https://www.attrs.org/en/stable/
.. _itemadapter: https://github.com/scrapy/itemadapter

Copy the following code into ``tutorial-project/tutorial/items.py``:

.. literalinclude:: /../tutorial-project/tutorial/items.py
   :language: python
   :lines: 1-6

This code defines a ``Book`` item class, with a single, required, string
``title`` attribute to store the book title.

``Book`` is a minimal class designed specifically for this tutorial. In real
web-poet projects, you will usually define item classes with many more
attributes.

Also mind that, while in this tutorial you use ``Book`` only for data from 1
website, `books.toscrape.com`_, item classes are usually meant to be usable for
many different websites that provide data with a similar data schema.


Create a page object class
==========================

To write web data extraction code with web-poet, you write :ref:`page object
classes <page-objects>`, Python classes that define how to extract data from a
given type of input, usually some type of webpage from a specific website.

In this tutorial you will write a page object class for webpages of
`books.toscrape.com`_ that show details about a book, such as these:

-   http://books.toscrape.com/catalogue/the-exiled_247/index.html
-   http://books.toscrape.com/catalogue/when-we-collided_955/index.html
-   http://books.toscrape.com/catalogue/set-me-free_988/index.html

Copy the following code into
``tutorial-project/tutorial/pages/books_toscrape_com.py``:

.. literalinclude:: /../tutorial-project/tutorial/pages/books_toscrape_com.py
   :language: python
   :lines: 1-14

In the code above:

-   You define a page object class named ``BookPage`` by subclassing
    :class:`~web_poet.pages.WebPage`.

    It is possible to create a page object class subclassing instead the
    simpler :class:`~web_poet.pages.ItemPage` class, but
    :class:`~web_poet.pages.WebPage`:

    -   Indicates that your page object class requires an HTTP response as
        input, which gets stored in the
        :attr:`~web_poet.pages.WebPage.response` attribute of your page object
        class.

    -   Provides attributes like :attr:`~web_poet.pages.WebPage.html` and
        :attr:`~web_poet.pages.WebPage.url`, and methods like
        :meth:`~web_poet.pages.WebPage.css`,
        :meth:`~web_poet.pages.WebPage.urljoin`, and
        :meth:`~web_poet.pages.WebPage.xpath`, that make it easier to write
        web data extraction code.

-   ``BookPage`` declares ``Book`` as its return type.

    :class:`~web_poet.pages.WebPage`, like its parent class
    :class:`~web_poet.pages.ItemPage`, is a :ref:`generic class <generics>`
    that accepts a type parameter. Unlike most generic classes, however, the
    specified type parameter is used for more than type hinting: it determines
    the item class that is used to store the data that fields return.

-   ``BookPage`` is decorated with :meth:`~web_poet.overrides.handle_urls`,
    which indicates for which URLs ``BookPage`` is intended to work.

-   ``BookPage`` defines a field named ``title``.

    :ref:`Fields <fields>` are methods of page object classes, preferably async
    methods, decorated with the :meth:`~web_poet.fields.field` decorator.
    Fields define the logic to extract a specific piece of information from the
    input of your page object class.

    ``BookPage.title`` extracts the title of a book from a book details
    webpage. Specifically, it extracts the text from the first ``h1`` element
    on the input HTTP response.

    Here ``title`` is not an arbitrary name, it was chosen specifically to
    match ``Book.title``, so that during web data extraction the value that
    ``BookPage.title`` returns gets mapped to ``Book.title``.


Use your page object class
==========================

Now that you have a page object class defined, it is time to use it.

First, install requests_, which is required by ``web_poet.example``.

.. _requests: https://requests.readthedocs.io/en/latest/user/install/

Then copy the following code into
``tutorial-project/run.py``:

.. literalinclude:: /../tutorial-project/run.py
   :language: python
   :lines: 1-5, 7-8

Execute that code:

..  code-block:: bash

    python tutorial-project/run.py

And the ``print(item)`` statement should output the following:

.. code-block:: python

   Book(title='The Exiled')

In this tutorial you use ``web_poet.example.get_item``, which is a simple,
incomplete implementation of the web-poet standard, built specifically for this
tutorial, for demonstration purposes. In real projects, use instead an actual
web-poet framework, like `scrapy-poet`_.

``web_poet.example.get_item`` serves to illustrate the power of web-poet. Once
you have defined your page object class, a web-poet framework only needs 2
inputs from you: the URL from which you want to extract data, and the import
path of the Python modules where you define your page object classes.

Your web-poet framework can take care of everything else:

#.  It matches the input URL to ``BookPage`` based on the URL pattern that you
    defined with the :meth:`~web_poet.overrides.handle_urls` decorator.

#.  It inspects the inputs declared by ``BookPage``, and builds an instance of
    ``BookPage`` with the required inputs.

    ``BookPage`` is a :class:`~web_poet.pages.WebPage` subclass, and
    :class:`~web_poet.pages.WebPage` declares an attribute named ``response``
    of type :class:`~web_poet.page_inputs.HttpResponse`. Your web-poet
    framework sees this, and creates an
    :class:`~web_poet.page_inputs.HttpResponse` object from the input URL as a
    result, by downloading the URL response, and assigns that object to the
    ``response`` attribute of a new ``BookPage`` object.

#.  It builds the output item, ``Book(title='The Exiled')``, using the
    :meth:`~web_poet.pages.ItemPage.to_item` method of ``BookPage``, inherited
    from :class:`~web_poet.pages.ItemPage`, which in turn uses all fields of
    ``BookPage`` to create an instance of ``Book``, which you declared as the
    return type of ``BookPage``.

.. _scrapy-poet: https://scrapy-poet.readthedocs.io


Extend and override your code
=============================

To continue this tutorial, you will need extended versions of ``Book`` and
``BookPage``, with additional fields. However, rather than editing the existing
``Book`` and ``BookPage`` classes, you will see how you can instead create new
classes that inherit them.

Append the following code to ``tutorial-project/tutorial/items.py``:

.. literalinclude:: /../tutorial-project/tutorial/items.py
   :language: python
   :lines: 9-15

The code above defines a new item class, ``CategorizedBook``, that inherits the
``title`` attribute from ``Book`` and defines 2 more attributes: ``category``
and ``category_rank``.

Append the following code to
``tutorial-project/tutorial/pages/books_toscrape_com.py``:

.. literalinclude:: /../tutorial-project/tutorial/pages/books_toscrape_com.py
   :language: python
   :lines: 19, 22-30, 32, 36-39

In the code above:

-   You define a new page object class: ``CategorizedBookPage``.

-   ``CategorizedBookPage`` subclasses ``BookPage``, inheriting its ``title``
    field, and defining a new one: ``category``.

    ``CategorizedBookPage`` does *not* define a ``category_rank`` field
    yet, you will add it later on. For now, the default value defined in
    ``CategorizedBook`` for ``category_rank``, ``None``, will be used.

-   ``CategorizedBookPage`` indicates that it returns a ``CaterogizedBook``
    object.

    :class:`~web_poet.pages.WebPage` is a :ref:`generic class <generics>`,
    which is why we could use ``WebPage[Book]`` in the definition of
    ``BookPage`` to indicate ``Book`` as the output type of ``BookPage``.
    However, ``BookPage`` is not a generic class, so something like
    ``BookPage[CategorizedBook]`` would not work.

    So instead you use :class:`~web_poet.pages.Returns`, a special, generic
    class that you can inherit to re-define the output type of your page object
    subclasses.

-   ``CategorizedBookPage`` uses the same
    :meth:`~web_poet.overrides.handle_urls` decorator parameters as
    ``BookPage``, except that it sets ``priority`` to ``1000``.

    The ``priority`` parameter is ``500`` by default, so the priority of
    ``BookPage`` is ``500``. By using a higher value than that of ``BookPage``,
    you ensure that, when a URL matches both page object classes,
    ``CategorizedBookPage`` is always used.

    A ``priority`` of ``501`` would have had the same effect. Using a
    significantly higher value is a good practice, to leave room between both
    values in case you ever need to define page object classes that have a
    priority between those 2 priority values.

If you execute the ``tutorial-project/run.py`` script again now:

..  code-block:: bash

    python tutorial-project/run.py

You can see in the new output that your new classes have been used:

.. code-block:: python

   CategorizedBook(title='The Exiled', category='Mystery', category_rank=None)


Use additional requests
=======================

To extract data about an item, sometimes the HTTP response to a single URL is
not enough. Sometimes, you need additional HTTP responses to get all the data
that you want. That is the case with the ``category_rank`` attribute.

The ``category_rank`` attribute indicates the position in which a book appears
in the list of books of the category of that book. For example,
`The Exiled`_ is 24th in the Mystery_ category, so the value of
``category_rank`` should be ``24`` for that book.

.. _The Exiled: http://books.toscrape.com/catalogue/the-exiled_247/index.html
.. _Mystery: https://books.toscrape.com/catalogue/category/books/mystery_3/

However, there is no indication of this value in the book details page. To get
this value, you need to visit the URL of the category of the book whose
data you are extracting, find the entry of that book within the grid of books
of the category, and record in which position you found it. And categories with
more than 20 books are split into multiple pages, so you may need more than 1
additional request for some books.

Extend ``CategorizedBookPage`` in ``tutorial-project/tutorial/items.py`` as
follows:

.. literalinclude:: /../tutorial-project/tutorial/pages/books_toscrape_com.py
   :language: python
   :lines: 17-18, 20, 22-33, 35-42, 46-59
   :emphasize-lines: 1-3, 13, 15-16, 22-37

In the code above:

-   You declare a new input in ``CategorizedBookPage``, ``http``, of type
    :class:`~web_poet.page_inputs.client.HttpClient`.

    You also add the ``@attrs.define`` decorator to ``CategorizedBookPage``, as
    it is required when adding new required attributes to subclasses of attrs_
    classes.

-   You define the ``category_rank`` field so that it uses the ``http``
    input object to send additional requests to find the position of the
    current book within its category.

    Specifically:

    #.  You extract the category URL from the book details page.

    #.  You visit that category URL, and you iterate over the listed books
        until you find one with the same URL as the current book.

        If you find a match, you return the position at which you found the
        book.

    #.  If there is no match, and there is a next page, you repeat the previous
        step with the URL of that next page as the category URL.

    #.  If at some point there are no more “next” pages and you have not yet
        found the book, you return ``None``.

When you execute ``tutorial-project/run.py`` now, ``category_rank`` has
the expected value:

.. code-block:: python

   CategorizedBook(title='The Exiled', category='Mystery', category_rank=24)


Use parameters
==============

You may notice that the execution takes longer now. That is because
``CategorizedBookPage`` now requires 2 or more requests, to find the value of
the ``category_rank`` attribute.

If you use ``CategorizedBookPage`` as part of a web data extraction project
that targets a single book URL, it cannot be helped. If you want to extract the
``category_rank`` attribute, you need those additional requests. Your only
option to avoid additional requests is to stop extracting the ``category_rank``
attribute.

However, if your web data extraction project is targeting all book URLs from
one or more categories by visiting those category URLs, extracting book URLs
from them, and then using ``CategorizedBookPage`` with those book URLs as
input, there is something you can change to save many requests: keep track of
the positions where you find books as you visit their categories, and pass that
position to ``CategorizedBookPage`` as additional input.

Extend ``CategorizedBookPage`` in ``tutorial-project/tutorial/items.py`` as
follows:

.. literalinclude:: /../tutorial-project/tutorial/pages/books_toscrape_com.py
   :language: python
   :lines: 17-18, 21-59
   :emphasize-lines: 3, 16, 25-27

In the code above, you declare a new input in ``CategorizedBookPage``,
``page_params``, of type :class:`~web_poet.page_inputs.page_params.PageParams`.
It is a dictionary of parameters that you may receive from the code using your
page object class.

In the ``category_rank`` field, you check if you have received a parameter also
called ``category_rank``, and if so, you return that value instead of using
additional requests to find the value.

You can now update your ``tutorial-project/run.py`` script to pass that
parameter to ``get_item``:

.. literalinclude:: /../tutorial-project/run.py
   :language: python
   :emphasize-lines: 6

When you execute ``tutorial-project/run.py`` now, execution should take less
time, but the result should be the same as before:

.. code-block:: python

   CategorizedBook(title='The Exiled', category='Mystery', category_rank=24)

Only that now the value of ``category_rank`` comes from
``tutorial-project/run.py``, and not from additional requests sent by
``CategorizedBookPage``.
