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

This enables us to conveniently declare which Page Object would be used for a
given webpage `(based on a page's URL pattern)`.

Let's see this in action by declaring the Overrides in the Page Objects below.


Creating Overrides
------------------

Using Default Registry
~~~~~~~~~~~~~~~~~~~~~~

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


    @handle_urls(["dualexample.com/shop/?product=*", "dualexample.net/store/?pid=*"], overrides=GenericProductPage)
    class DualExampleProductPage(ItemWebPage):
        def to_item(self):
            ...  # more specific parsing

The code above declares that:

    - For sites that match the ``example.com`` pattern, ``ExampleProductPage``
      would be used instead of ``GenericProductPage``.
    - The same is true for ``DualExampleProductPage`` where it is used
      instead of ``GenericProductPage`` for two URL patterns which works as:

      - :sub:`(match) https://www.dualexample.com/shop/electronics/?product=123`
      - :sub:`(match) https://www.dualexample.com/shop/books/paperback/?product=849`
      - :sub:`(NO match) https://www.dualexample.com/on-sale/books/?product=923`
      - :sub:`(match) https://www.dualexample.net/store/kitchen/?pid=776`
      - :sub:`(match) https://www.dualexample.net/store/?pid=892`
      - :sub:`(NO match) https://www.dualexample.net/new-offers/fitness/?pid=892`

    - On the other hand, ``AnotherExampleProductPage`` is only used instead of
      ``GenericProductPage`` when we're parsing pages from ``anotherexample.com``
      that doesn't contain ``/digital-goods/`` in its URL path.

.. tip::

    The URL patterns declared in the :func:`web_poet.handle_urls` can still be
    further customized. You can read some of the specific parameters and
    alternative ways in the API section <api-overrides> of
    :func:`web_poet.handle_urls`.

Using Multiple Registries
~~~~~~~~~~~~~~~~~~~~~~~~~

To demonstrate another alternative way to declare the Override rules, see the
code example below:

.. code-block:: python

    from web_poet import handle_urls, PageObjectRegistry
    from web_poet.pages import ItemWebPage


    clothes_registry = PageObjectRegistry(name="clothes")


    class GenericProductPage(ItemWebPage):
        def to_item(self):
            return {"product title": self.css("title::text").get()}


    @handle_urls(["dualexample.com/shop/?product=*", "dualexample.net/store/?pid=*"], overrides=GenericProductPage)
    @clothes_registry.handle_urls("dualexample.com/shop/?category=clothes&product=*", overrides=GenericProductPage)
    class DualExampleProductPage(ItemWebPage):
        def to_item(self):
            ...  # more specific parsing

In the example above, we're splitting the Page Objects into two separate Registries.
If you may notice, ``DualExampleProductPage`` is being declared into both of them
but with a different URL pattern.

If you need more control over the Registry, you could instantiate your very
own :class:`~.PageObjectRegistry` and use its ``@handle_urls`` to annotate and
register the rules. This might benefit you in certain project use cases where you
need more organizational control over your rules.

Such an approach could be useful especially when you're publishing your Page
Objects as an external dependency. Other projects may use it and could import
a specific Registry containing the URL rules that they may need.

Viewing all available Overrides
-------------------------------

A convenience function is available discover and retrieve all :class:`~.OverrideRule`
from your project. Make sure to check out the :meth:`~.PageObjectRegistry.get_overrides`
API section to see other functionalities.

.. code-block:: python

    from web_poet import default_registry

    # Retrieves all OverrideRules that were registered in the registry
    rules = default_registry.get_overrides()

    # Or, we could also filter out the OverrideRules by the module they were defined in
    rules = default_registry.get_overrides(filters="my_project.page_objects")

    print(len(rules))  # 3
    print(rules[0])    # OverrideRule(for_patterns=Patterns(include=['example.com'], exclude=[], priority=500), use=<class 'my_project.page_objects.ExampleProductPage'>, instead_of=<class 'my_project.page_objects.GenericProductPage'>, meta={})

.. note::

    Notice in the code sample above where we could filter out the Override rules
    per module via the ``filters`` param. This could also offer another alternative
    way to organize your Page Object rules by module hierarchies in your project.
    This could require on solely using the ``default_registry``. There's no need
    to declare multiple :class:`~.PageObjectRegistry` instances and use multiple
    annotations.

.. warning::

    :meth:`~.PageObjectRegistry.get_overrides` relies on the fact that all essential
    packages/modules which contains the :func:`web_poet.handle_urls`
    annotations are properly loaded.

    Thus, for cases like importing Page Objects from another external package, you'd
    need to properly load all :meth:`web_poet.handle_urls` annotations
    from the external module. This ensures that the external Page Objects have
    their annotations properly loaded.

    This can be done via the function named :func:`~.web_poet.overrides.consume_modules`.
    Here's an example:

    .. code-block:: python

        from web_poet import default_registry, consume_modules

        consume_modules("external_package_A.po", "another_ext_package.lib")
        rules = default_registry.get_overrides()

        # Fortunately, `get_overrides()` provides a shortcut for the lines above:
        rules = default_registry.get_overrides(consume=["external_package_A.po", "another_ext_package.lib"])

A handy CLI tool is also available at your disposal to quickly see the available
:class:`~.OverrideRule` in a given module in your project. For example, invoking
something like ``web_poet my_project.page_objects`` would produce the following:

.. code-block::

    Registry   Use this                                              instead of                                  for the URL patterns                                                 except for the patterns      with priority  meta
    ---------  ----------------------------------------------------  ------------------------------------------  -------------------------------------------------------------------  -------------------------  ---------------  ------
    default    my_project.page_objects.ExampleProductPage            my_project.page_objects.GenericProductPage  ['example.com']                                                      []                                     500  {}
    default    my_project.page_objects.AnotherExampleProductPage     my_project.page_objects.GenericProductPage  ['anotherexample.com']                                               ['/digital-goods/']                    500  {}
    default    my_project.page_objects.DualExampleProductPage        my_project.page_objects.GenericProductPage  ['dualexample.com/shop/?product=*', 'dualexample.net/store/?pid=*']  []                                     500  {}

You can also filter them via the **name** of :class:`~.PageObjectRegistry`. For example,
invoking ``web_poet my_project.page_objects --registry_name=custom`` would produce
something like:

.. code-block::

    Registry    Use this                                              instead of                                  for the URL patterns    except for the patterns      with priority  meta
    ----------  ----------------------------------------------------  ------------------------------------------  ----------------------  -------------------------  ---------------  ------
    custom      my_project.page_objects.CustomProductPage             my_project.page_objects.GenericProductPage  ['example.com']         []                                     500  {}
    custom      my_project.page_objects.AnotherCustomProductPage      my_project.page_objects.GenericProductPage  ['anotherexample.com']  ['/digital-goods/']                    500  {}

Organizing Page Object Overrides
--------------------------------

After tackling the two (2) different approaches from the previous chapters on how
to declare overrides, we can now explore how to organize them in our projects.
Although it's mostly up to the developer which override declaration method to
use. Yet, we'll present a few different approaches depending on the situation.

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
``default_registry`` as something like:

.. code-block:: python

    # my_page_obj_project/cool_gadget_site/us/products.py

    from web_poet import handle_urls  # remember that this uses the default_registry
    from web_poet.pages import ItemWebPage

    @handle_urls("coolgadgetsite.com", overrides=GenericProductPage)
    class CoolGadgetUsSiteProductPage(ItemWebPage):
        def to_item(self):
            ... # parsers here

Then we could easily retrieve all :class:`~.OverrideRule` filtered per subpackage
or module like this:

.. code-block:: python

    from web_poet import default_registry, consume_modules

    # We can do it per website.
    rules_gadget = default_registry.get_overrides(filters="my_page_obj_project.cool_gadget_site")
    rules_furniture = default_registry.get_overrides(filters="my_page_obj_project.furniture_site")

    # It can also drill down to the country domains on a given site.
    rules_gadget_us = default_registry.get_overrides(filters="my_page_obj_project.cool_gadget_site.us")
    rules_gadget_fr = default_registry.get_overrides(filters="my_page_obj_project.cool_gadget_site.fr")

    # Or even drill down further to the specific module.
    rules_gadget_us_products = default_registry.get_overrides(filters="my_page_obj_project.cool_gadget_site.us.products")
    rules_gadget_us_listings = default_registry.get_overrides(filters="my_page_obj_project.cool_gadget_site.us.product_listings")

    # Or simply all of the Override rules ever declared.
    rules = default_registry.get_overrides()

    # Lastly, you'd need to properly load external packages/modules for the
    # @handle_urls annotation to be correctly read. If there are any.
    consume_modules("external_package_A.po", "another_ext_package.lib")
    rules = default_registry.get_overrides()

    # Remember, a shortcut for consuming imports would be:
    rules = default_registry.get_overrides(consume=["external_package_A.po", "another_ext_package.lib"])


.. warning::

    Remember to consider calling :func:`~.web_poet.overrides.consume_modules`
    or the ``consume`` param of :meth:`~.PageObjectRegistry.get_overrides` for the
    imports to properly load. Most especially if you intend to use Page Objects
    from externally imported packages.

    This enables the :meth:`~.PageObjectRegistry.handle_urls` that annotates
    the external Page Objects to be properly loaded.

Multiple Registry Approach
~~~~~~~~~~~~~~~~~~~~~~~~~~

The **package-based** approach heavily relies on how the developer organizes the
project modules into intuitive hierarchies depending on the nature of the project.
There might be cases that for some reason, a developer would want to use a **flat 
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

As such, calling :meth:`~.PageObjectRegistry.get_overrides` with a ``from`` 
filter parameter would not effectively work on projects with a **flat hierarchy**.
Thus, we can organize them using our own instances of the :class:`~.PageObjectRegistry`
instead:

.. code-block:: python

    # my_page_obj_project/__init__.py

    from web_poet import PageObjectRegistry

    cool_gadget_registry = PageObjectRegistry(name="cool_gadget")
    cool_gadget_us_registry = PageObjectRegistry(name="cool_gadget_us")
    cool_gadget_fr_registry = PageObjectRegistry(name="cool_gadget_fr")
    furniture_shop_registry = PageObjectRegistry(name="furniture_shop")

.. tip::

    Later on, you can access all of the :class:`~.PageObjectRegistry` that were
    ever instantiated. This can be done via ``web_poet.registry_pool`` which
    simply a holds a mapping structured as ``Dict[str, PageObjectRegistry]``.

    So after declaring the :class:`~.PageObjectRegistry` instances above, we can
    view them via:

    .. code-block:: python

        from web_poet import registry_pool

        print(registry_pool)
        # {
        #     'default': <web_poet.overrides.PageObjectRegistry object at 0x7f47d654d8b0>,
        #     'cool_gadget' = <my_page_obj_project.PageObjectRegistry object at 0x7f47d654382a>,
        #     'cool_gadget_us' = <my_page_obj_project.PageObjectRegistry object at 0xb247d65433c3>,
        #     'cool_gadget_fr' = <my_page_obj_project.PageObjectRegistry object at 0xd93746549dea>,
        #     'furniture_shop' = <my_page_obj_project.PageObjectRegistry object at 0x82n78654441b>
        # }

    Notice that the ``default`` registry will always be present. 

.. warning::

    Please be aware that there might be some :class:`~.PageObjectRegistry`
    that are not available, most especially if you're using them from external
    packages.

    Thus, it's imperative to use :func:`~.web_poet.overrides.consume_modules`
    beforehand. Not only that it helps us find the :meth:`~.PageObjectRegistry.handle_urls`
    annotated in external packages, but also finds the instances of
    :class:`~.PageObjectRegistry` as well.

    Here's an example:

    .. code-block:: python

        from web_poet import registry_pool, consume_modules

        consume_modules("external_pkg")

        print(registry_pool)
        # {
        #     'default': <web_poet.overrides.PageObjectRegistry object at 0x7f47d654d8b0>,
        #     'cool_gadget' = <my_page_obj_project.PageObjectRegistry object at 0x7f47d654382a>,
        #     'cool_gadget_us' = <my_page_obj_project.PageObjectRegistry object at 0xb247d65433c3>,
        #     'cool_gadget_fr' = <my_page_obj_project.PageObjectRegistry object at 0xd93746549dea>,
        #     'furniture_shop' = <my_page_obj_project.PageObjectRegistry object at 0x82n78654441b>,
        #     'ecommerce': <external_pkg.PageObjectRegistry object at 0xbc45d8328420>
        # }

    Notice that the ``external_pkg.PageObjectRegistry`` named **ecommerce** has
    now been successfully discovered.

After declaring the :class:`~.PageObjectRegistry` instances, they can be used
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

Suppose we'd want to get all the rules for all of the listings `(ignoring anything
else)`, then one way to retrieve such rules would be:

.. code-block:: python

    from web_poet import default_registry

    product_listing_rules = default_registry.get_overrrides(
        filters=[
            "my_page_obj_project.cool_gadget_site.us.product_listings",
            "my_page_obj_project.cool_gadget_site.fr.product_listings",
            "my_page_obj_project.furniture_shop.product_listings",
        ]
    )

On the other hand, we can also create another :class:`~.PageObjectRegistry` instance
that we'll be using aside from the ``default_registry`` to help us better organize
our :class:`~.OverrideRule`.

.. code-block:: python

    # my_page_obj_project/__init__.py

    from web_poet import PageObjectRegistry

    product_listings_registry = PageObjectRegistry(name="product_listings")

Using the new **product_listings_registr** instance above, we'll use it to
provide another annotation for the Page Objects in each of the
``product_listings.py`` module. For example:

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

Retrieving all of the Product Listing :class:`~.OverrideRule` would simply be:

.. code-block:: python

    from my_page_obj_project import product_listings_registry

    # Getting all of the override rules for product listings.
    rules = product_listings_registry.get_overrides()

    # We can also filter it down further on a per site basis if needed.
    rules = product_listings_registry.get_overrides(filters="my_page_obj_project.cool_gadget_site")

Using Overrides from External Packages
--------------------------------------

Developers have the option to import existing Page Objects alongside the
:class:`~.OverrideRule` attached to them. This section aims to showcase different
ways you can play with the Registries to manipulate the :class:`~.OverrideRule`
according to your needs.

Let's suppose we have the following use case before us:

    - An **external** Python package named ``ecommerce_page_objects`` is available
      which contains Page Objects for common websites. It's using the
      ``default_registry`` from **web-poet**.
    - Another similar package named ``gadget_sites_page_objects`` is available
      for even more specific websites. It's using its own registry named
      ``gadget_registry``.
    - Your project's objectives is to handle as much eCommerce websites as you
      can. Thus, you'd want to use the already available packages above and
      perhaps improve on them or create new Page Objects for new websites.

Assuming that you'd want to **use all existing** :class:`~.OverrideRule` **from
the external packages** in your project, you can do it like:

.. code-block:: python

    import ecommerce_page_objects
    import gadget_sites_page_objects
    from web_poet import PageObjectRegistry, consume_modules, default_registry


    # We're using `consume_modules()` here instead of the `consume` param of
    # `PageObjectRegistry.get_overrides()` since we need to access the `data`
    # attribute of the registry even before calling `PageObjectRegistry.get_overrides()`
    consume_modules("ecommerce_page_objects", "gadget_sites_page_objects")

    combined_registry = PageObjectRegistry(name="combined")
    combined_registry.data = {
        # Since ecommerce_page_objects is using web_poet.default_registry, then
        # it functions like a global registry which we can access as:
        **default_registry.data,

        # External packages not using the web_poet.default_registry would need
        # to have their own registry accessed.
        **gadget_sites_page_objects.gadget_registry.data,
    }

    combined_rules = combined_registry.get_overrides()

    # The combined_rules would be as follows:
    # 1. OverrideRule(for_patterns=Patterns(include=['site_1.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_1.EcomSite1'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, meta={})
    # 2. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, meta={})
    # 3. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_2.GadgetSite2'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, meta={})
    # 4. OverrideRule(for_patterns=Patterns(include=['site_3.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_3.GadgetSite3'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, meta={})

    # If there are any duplicates when combining the OverrideRules,
    # you could do the following to ensure uniqueness:
    combined_rules = set(combined_rules)

.. note::

    Note that ``registry.get_overrides() == list(registry.data.values())``.

    We're using ``registry.data`` for these cases so that we can easily look up
    specific Page Objects using the ``dict``'s key. Otherwise, it may become a
    problem on large cases with lots of :class:`~.OverrideRule`.

.. tip::

    If you don't need the entire data contents of Registries, then you can opt
    to use :meth:`~.PageObjectRegistry.data_from` to easily filter them out
    per package/module.

    Here's an example:

    .. code-block:: python

        default_registry.data_from("ecommerce_page_objects.site_1", "ecommerce_page_objects.site_2")

As you can see in the example above, we can easily combine the data from multiple
different registries as it simply follows a ``Dict[Callable, OverrideRule]``
structure. There won't be any duplication or clashes of ``dict`` keys between
registries of different external packages since the keys are the Page Object
classes intended to be used. 

From our example above, the ``dict`` keys from a given ``data`` registry
attribute would be:

    1. ``<class 'ecommerce_page_objects.site_1.EcomSite1'>``
    2. ``<class 'ecommerce_page_objects.site_2.EcomSite2'>``
    3. ``<class 'gadget_sites_page_objects.site_2.GadgetSite2'>``
    4. ``<class 'gadget_sites_page_objects.site_3.GadgetSite3'>``

As you might've observed, combining the two Registries above may result in a
conflict for the :class:`~.OverrideRule` for **#2** and **#3**:

.. code-block:: python

    # 2. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, meta={})
    # 3. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_2.GadgetSite2'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, meta={})

The `url-matcher`_ library is the one responsible breaking such conflicts. It's
specifically discussed in this section: `rules-conflict-resolution
<https://url-matcher.readthedocs.io/en/stable/intro.html#rules-conflict-resolution>`_.

However, it's technically **NOT** a conflict, **yet**, since:

    - ``ecommerce_page_objects.site_2.EcomSite2`` would only be used in **site_2.com**
      if ``ecommerce_page_objects.EcomGenericPage`` is to be replaced.
    - The same case with ``gadget_sites_page_objects.site_2.GadgetSite2`` wherein
      it's only going to be utilized for **site_2.com** if the following is to be
      replaced: ``gadget_sites_page_objects.GadgetGenericPage``.

It would be only become a conflict if the **#2** and **#3** :class:`~.OverrideRule`
for **site_2.com** both `intend to replace the` **same** `Page Object`. In fact,
none of the :class:`~.OverrideRule` above would ever be used if your project never
intends to use the following Page Objects *(since there's nothing to override)*.
You can import these Page Objects into your project and use them so they can be
overridden:

    - ``ecommerce_page_objects.EcomGenericPage``
    - ``gadget_sites_page_objects.GadgetGenericPage``

However, let's assume that you want to create your own generic Page Object and
only intend to use it instead of the ones above. We can easily replace them like:

.. code-block:: python

    class ImprovedEcommerceGenericPage:
        def to_item(self):
            ...  # different type of generic parsers

    for _, rule in combined_registry.data.items():
        rule.instead_of = ImprovedEcommerceGenericPage

    updated_rules = combined_registry.get_overrides()

    # The updated_rules would be as follows:
    # 1. OverrideRule(for_patterns=Patterns(include=['site_1.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_1.EcomSite1'>, instead_of=<class 'my_project.ImprovedEcommerceGenericPage'>, meta={})
    # 2. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'my_project.ImprovedEcommerceGenericPage'>, meta={})
    # 3. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_2.GadgetSite2'>, instead_of=<class 'my_project.ImprovedEcommerceGenericPage'>, meta={})
    # 4. OverrideRule(for_patterns=Patterns(include=['site_3.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_3.GadgetSite3'>, instead_of=<class 'my_project.ImprovedEcommerceGenericPage'>, meta={})

Now, **#2** and **#3** have a conflict since they now both intend to replace
``ImprovedEcommerceGenericPage``. As mentioned earlier, the `url-matcher`_
would be the one to resolve such conflicts.

However, it would help prevent future confusion if we could remove the source of
ambiguity in our :class:`~.OverrideRule`.

Suppose, we prefer ``gadget_sites_page_objects.site_2.GadgetSite2`` more than
``ecommerce_page_objects.site_2.EcomSite2``. As such, we could remove the latter:

.. code-block:: python

    del combined_registry.data[ecommerce_page_objects.site_2.EcomSite2]

    updated_rules = combined_registry.get_overrides()

    # The newly updated_rules would be as follows:
    # 1. OverrideRule(for_patterns=Patterns(include=['site_1.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_1.EcomSite1'>, instead_of=<class 'my_project.ImprovedEcommerceGenericPage'>, meta={})
    # 2. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'my_project.ImprovedEcommerceGenericPage'>, meta={})
    # 3. OverrideRule(for_patterns=Patterns(include=['site_3.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_3.GadgetSite3'>, instead_of=<class 'my_project.ImprovedEcommerceGenericPage'>, meta={})

As discussed before, the Registry's data is structured simply as
``Dict[Callable, OverrideRule]`` for which we can easily manipulate it via ``dict``
operations.

Now, suppose we want to improve ``ecommerce_page_objects.site_1.EcomSite1``
from **#1** above by perhaps adding/fixing fields. We can do that by:

.. code-block:: python

    class ImprovedEcomSite1(ecommerce_page_objects.site_1.EcomSite1):
        def to_item(self):
            ...  # replace and improve some of the parsers here

    combined_registry.data[ecommerce_page_objects.site_1.EcomSite1].use = ImprovedEcomSite1

    updated_rules = combined_registry.get_overrides()

    # The newly updated_rules would be as follows:
    # 1. OverrideRule(for_patterns=Patterns(include=['site_1.com'], exclude=[], priority=500), use=<class 'my_project.ImprovedEcomSite1'>, instead_of=<class 'my_project.ImprovedEcommerceGenericPage'>, meta={})
    # 2. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_2.GadgetSite2'>, instead_of=<class 'my_project.ImprovedEcommerceGenericPage'>, meta={})
    # 3. OverrideRule(for_patterns=Patterns(include=['site_3.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_3.GadgetSite3'>, instead_of=<class 'my_project.ImprovedEcommerceGenericPage'>, meta={})
