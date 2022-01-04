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

.. code-block:: python

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

Organizing Page Object Overrides
--------------------------------

After tackling the two (2) different approaches from the previous chapters on how
to declare overrides, we can now explore how to organize them in our projects.
Although it's mostly up to the developer which override declaration method to
use. Yet, we'll present some approaches depending on the situation.

To put this thought into action, let's suppose we are tasked to create a Page
Object Project with overrides for eCommerce websites.

Package-based Approach
~~~~~~~~~~~~~~~~~~~~~~

Using the **package-based** approach, we might organize them into something like:

.. code-block::

    my_page_obj_project
    ├── cool_gadget_site
    |   ├── us
    |   |   ├── __init__.py
    |   |   ├── products.py
    |   |   └── product_listings.py
    |   ├── fr
    |   |   ├── __init__.py
    |   |   ├── products.py
    |   |   └── product_listings.py
    |   └── __init__.py
    └── furniture_shop
        ├── __init__.py
        ├── products.py
        └── product_listings.py

Assuming that we've declared the Page Objects in each of the modules to use the
``default_registry`` like:

.. code-block:: python

    # my_page_obj_project/cool_gadget_site/us/products.py

    from web_poet import handle_urls  # remember that this uses the default_registry
    from web_poet.pages import ItemWebPage

    @handle_urls("coolgadgetsite.com", overrides=GenericProductPage)
    class CoolGadgetUsSiteProductPage(ItemWebPage):
        def to_item(self):
            ... # parsers here

Then we could easily retrieve all Page Objects per subpackage or module like this:

.. code-block:: python

    from web_poet import default_registry

    # We can do it per website.
    rules = default_registry.get_overrides_from_module("my_page_obj_project.cool_gadget_site")
    rules = default_registry.get_overrides_from_module("my_page_obj_project.furniture_site")

    # It can also drill down to the country domains on a given site.
    rules = default_registry.get_overrides_from_module("my_page_obj_project.cool_gadget_site.us")
    rules = default_registry.get_overrides_from_module("my_page_obj_project.cool_gadget_site.fr")

    # or even drill down further to the specific module.
    rules = default_registry.get_overrides_from_module("my_page_obj_project.cool_gadget_site.us.products")
    rules = default_registry.get_overrides_from_module("my_page_obj_project.cool_gadget_site.us.product_listings")

    # Or simply all of Override rules ever declared.
    rules = default_registry.get_overrides()

Multiple Registry Approach
~~~~~~~~~~~~~~~~~~~~~~~~~~

The **package-based** approach heavily relies on how the developer organizes the
files into intuitive hierarchies depending on the nature of the project. There
might be cases that for some reason, a developer would want to use a **flat 
hierarchy** like this:

.. code-block::

    my_page_obj_project
    ├── __init__.py
    ├── cool_gadget_site_us_products.py
    ├── cool_gadget_site_us_product_listings.py
    ├── cool_gadget_site_fr_products.py
    ├── cool_gadget_site_fr_product_listings.py
    ├── furniture_shop_products.py
    └── furniture_shop_product_listings.py

As such, calling ``default_registry.get_overrides_from_module()`` would not work
on projects with a **flat hierarchy**. Thus, we can organize them using our own
instances of the :class:`~.PageObjectRegistry` instead:

.. code-block:: python

    # my_page_obj_project/__init__.py

    from web_poet import PageObjectRegistry

    cool_gadget_registry = PageObjectRegistry()
    cool_gadget_us_registry = PageObjectRegistry()
    cool_gadget_fr_registry = PageObjectRegistry()
    furniture_shop_registry = PageObjectRegistry()

After declaring the :class:`~.PageObjectRegistry` instances, they can be imported
in each of the Page Object packages like so:

.. code-block:: python

    # my_page_obj_project/cool_gadget_site_us_products.py

    from . import cool_gadget_registry, cool_gadget_us_registry
    from web_poet.pages import ItemWebPage

    @cool_gadget_registry.handle_urls("coolgadgetsite.com", overrides=GenericProductPage)
    @cool_gadget_us_registry.handle_urls("coolgadgetsite.com", overrides=GenericProductPage)
    class CoolGadgetSiteProductPage(ItemWebPage):
        def to_item(self):
            ... # parsers here

Retrieving the rules would simply be:

.. code-block:: python

    from my_page_obj_project import (
        cool_gadget_registry,
        cool_gadget_us_registry,
        cool_gadget_fr_registry,
        furniture_shop_registry,
    )

    rules = cool_gadget_registry.get_overrides()
    rules = cool_gadget_us_registry.get_overrides()
    rules = cool_gadget_fr_registry.get_overrides()
    rules = furniture_shop_registry.get_overrides()

Developers can create as much :class:`~.PageObjectRegistry` instances as they want
in order to satisfy their organization and classification needs.

Mixed Approach
~~~~~~~~~~~~~~

Developers are free to choose whichever approach would best fit their particular
use case. They can even mix both approach together to handle some particular
cases.

For instance, going back to our **package-based** approach organized as:

.. code-block::

    my_page_obj_project
    ├── cool_gadget_site
    |   ├── us
    |   |   ├── __init__.py
    |   |   ├── products.py
    |   |   └── product_listings.py
    |   ├── fr
    |   |   ├── __init__.py
    |   |   ├── products.py
    |   |   └── product_listings.py
    |   └── __init__.py
    └── furniture_shop
        ├── __init__.py
        ├── products.py
        └── product_listings.py

Suppose we'd want to get all the rules for all of the listings, then one way to
retrieve such rules would be:

.. code-block:: python

    from web_poet import default_registry

    product_listing_rules = [
        default_registry.get_overrides_from_module("my_page_obj_project.cool_gadget_site.us.product_listings")
        + default_registry.get_overrides_from_module("my_page_obj_project.cool_gadget_site.fr.product_listings")
        + default_registry.get_overrides_from_module("my_page_obj_project.furniture_shop.product_listings")
    ]

On the other hand, we can also create another :class:`~.PageObjectRegistry` instance
that we'll be using aside from the ``default_registry`` to help us better organize
our Override Rules.

.. code-block:: python

    # my_page_obj_project/__init__.py

    from web_poet import PageObjectRegistry

    product_listings_registry = PageObjectRegistry()

Using the additional registry instance above, we'll use it to provide another
annotation for the Page Objects in each of the ``product_listings.py`` module.
For example:

.. code-block:: python

    # my_page_obj_project/cool_gadget_site_us_product_listings.py

    from . import product_listings_registry
    from web_poet import handle_urls  # remember that this uses the default_registry
    from web_poet.pages import ItemWebPage

    @product_listings_registry.handle_urls("coolgadgetsite.com", overrides=GenericProductPage)
    @handle_urls("coolgadgetsite.com", overrides=GenericProductPage)
    class CoolGadgetSiteProductPage(ItemWebPage):
        def to_item(self):
            ... # parsers here

Retrieving all of the Product Listing Override rules would simply be:

.. code-block:: python

    from my_page_obj_project import product_listings_registry

    # Getting all of the override rules for product listings.
    rules = product_listings_registry.get_overrides()

    # We can also filter it down further on a per site basis if needed.
    rules = product_listings_registry.get_overrides_from_module("my_page_obj_project.cool_gadget_site")
