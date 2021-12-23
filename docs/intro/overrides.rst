.. _`intro-overrides`:

Overrides
=========

Overrides contains mapping rules to associate which URLs a particular
Page Object would be used. The URL matching rules is handled by another library
called `url-matcher <https://url-matcher.readthedocs.io>`_.

Using such matching rules establishes the core concept of Overrides wherein
its able to use specific Page Objects in lieu of the original one.

This enables ``web-poet`` to be used effectively by other frameworks like 
`scrapy-poet <https://scrapy-poet.readthedocs.io>`_.

Example Use Case
----------------

Let's explore an example use case for the Overrides concept.

Suppose we're using Page Objects for our broadcrawl project which explores
eCommerce websites to discover product pages. It wouldn't be entirely possible
for us to create parsers for all websites since we don't know which sites we're
going to crawl beforehand.

However, we could at least create a generic Page Object to support parsing of
some fields in well-known locations of product information like ``<title>``.
This enables our broadcrawler to at least parse some useful information. Let's
call such Page Object to be ``GenericProductPage``.

Assuming that one of our project requirements is to fully support parsing of the
`top 3 eCommerce websites`, then we'd need to create a Page Object for each one
to parse more specific fields.

Here's where the Overrides concept comes in:

    1. The ``GenericProductPage`` is used to parse all eCommerce product pages
       `by default`.
    2. Whenever one of our declared URL rules matches with a given page URL,
       then the Page Object associated with that rule `overrides (or replaces)`
       the default ``GenericProductPage``.

This enables us to fine tune our parsing logic `(which are abstracted away for
each Page Object)` depending on the page we're parsing.

Let's see this in action by creating Page Objects below.


Creating Overrides
------------------

Let's take a look at how the following code is structured:

.. code-block:: python

    from web_poet import handle_urls
    from web_poet.pages import ItemWebPage

    class GenericProductPage(ItemWebPage):
        def to_item(self):
            return {"product title": self.css("title::text").get()}

    @handle_urls("example.com", overrides=GenericProductPage)
    class ExampleProductPage(ItemWebPage):
        def to_item(self):
            ...  # more specific parsing

    @handle_urls("anotherexample.com", overrides=GenericProductPage, exclude="/digital-goods/")
    class AnotherExampleProductPage(ItemWebPage):
        def to_item(self):
            ...  # more specific parsing

    @handle_urls(["dualexample.com", "dualexample.net"], overrides=GenericProductPage)
    class DualExampleProductPage(ItemWebPage):
        def to_item(self):
            ...  # more specific parsing

The code above declares that:

    - For sites that matches the ``example.com`` pattern, ``ExampleProductPage``
      would be used instead of ``GenericProductPage``.
    - The same is true for ``YetAnotherExampleProductPage`` where it is used
      instead of ``GenericProductPage`` for two URLs: ``dualexample.com`` and
      ``dualexample.net``.
    - However, ``AnotherExampleProductPage`` is only used instead of ``GenericProductPage``
      when we're parsing pages from ``anotherexample.com`` which doesn't contain
      ``/digital-goods/`` in its URL path.

The override mechanism that ``web-poet`` offers could still be further
customized. You can read some of the specific parameters and alternative ways
to organize the rules via the :ref:`Overrides API section <api-overrides>`.

To demonstrate another alternative way to declare the Override rules, see the
code example below:

.. code-block:: python

    from web_poet.pages import ItemWebPage
    from web_poet import PageObjectRegistry

    primary_registry = PageObjectRegistry()
    secondary_registry = PageObjectRegistry()

    class GenericProductPage(ItemWebPage):
        def to_item(self):
            return {"product title": self.css("title::text").get()}

    @primary_registry.handle_urls("example.com", overrides=GenericProductPage)
    class ExampleProductPage(ItemWebPage):
        def to_item(self):
            ...  # more specific parsing

    @secondary_registry.handle_urls("anotherexample.com", overrides=GenericProductPage, exclude="/digital-goods/")
    class AnotherExampleProductPage(ItemWebPage):
        def to_item(self):
            ...  # more specific parsing

    @primary_registry.handle_urls(["dualexample.com", "dualexample.net"], overrides=GenericProductPage)
    @secondary_registry.handle_urls(["dualexample.com", "dualexample.net"], overrides=GenericProductPage)
    class DualExampleProductPage(ItemWebPage):
        def to_item(self):

If you need more control over the Registry, you could instantiate your very
own :class:`~.PageObjectRegistry` and use its ``@handle_urls`` to annotate and
register the rules. This might benefit you in certain project use cases where you
need more organizational control over your rules.


Viewing all available Overrides
-------------------------------

A convenience function is available discover and retrieve all rules from your
project. Make sure to check out :ref:`Overrides API section <api-overrides>`
to see the other functionalities.

.. code-block::

    from web_poet import default_registry

    # Retrieves all rules that were registered in the registry
    rules = default_registry.get_overrides() 

    # Or, we could also filter out the rules by the module they were defined in
    rules = default_registry.get_overrides_from_module("my_project.page_objects")

    print(len(rules))  # 3
    print(rules[0])  # OverrideRule(for_patterns=Patterns(include=['example.com'], exclude=[], priority=500), use=<class 'my_project.page_objects.ExampleProductPage'>, instead_of=<class 'my_project.page_objects.GenericProductPage'>, meta={})

.. note::

    Notice in the code sample above where we could filter out the Override rules
    per module via :meth:`~.PageObjectRegistry.get_overrides_from_module`. This
    could also offer another alternative way to organize your Page Object rules
    using only the ``default_registry``. There's no need to declare multiple
    :class:`~.PageObjectRegistry` instances and use multiple annotations.

A handy CLI tool is also available at your disposal to quickly see the available
Override rules in a given module in your project. For example, invoking something
like ``web_poet my_project.page_objects`` would produce the following:

.. code-block::

    Use this                                              instead of                                  for the URL patterns                    except for the patterns      with priority  meta
    ----------------------------------------------------  ------------------------------------------  --------------------------------------  -------------------------  ---------------  ------
    my_project.page_objects.ExampleProductPage            my_project.page_objects.GenericProductPage  ['example.com']                         []                                     500  {}
    my_project.page_objects.AnotherExampleProductPage     my_project.page_objects.GenericProductPage  ['anotherexample.com']                  ['/digital-goods/']                    500  {}
    my_project.page_objects.DualExampleProductPage        my_project.page_objects.GenericProductPage  ['dualexample.com', 'dualexample.net']  []                                     500  {}
