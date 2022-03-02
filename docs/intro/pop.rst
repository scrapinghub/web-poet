.. _`intro-pop`:

Page Object Projects (POP)
==========================

**POPs** are way to package up a group of Page Objects together so they
can be used in other projects as well. This improves code reusability since
the extraction logic in some web pages are easily shareable. More importantly,
**POPs** could be built using other **POPs**. This allows for continuous
improvements by building **POPs** on top of one another.

Organizing POP
--------------

Developers have complete freedom on how to organize their Page Objects
in their project. Here are some options that developers could use.

Flat Hierarchy
~~~~~~~~~~~~~~

A good default option for organizing Page Objects would be to simply have
their respective modules in a flat hierarchy as seen in the example below.

.. code-block::

    ecommerce-page-objects
    ├── ecommerce_page_objects
    |   ├── __init__.py
    |   ├── cool_gadget_site_us_products.py
    |   ├── cool_gadget_site_us_product_listings.py
    |   ├── cool_gadget_site_fr_products.py
    |   ├── cool_gadget_site_fr_product_listings.py
    |   ├── furniture_shop_products.py
    |   └── furniture_shop_product_listings.py
    └── setup.py  

However, when your Page Object Project grows, it may be difficult to manage
a flat structure like this.

Hierarchical Directories
~~~~~~~~~~~~~~~~~~~~~~~~

One key advantage for organizing the Page Objects into a hierarchy
of subpackages is that large websites could be broken further into
its more granular form.

A quick example would be websites having multiple country-specific
domains. This could easily be grouped as something like:

.. code-block::

    ecommerce-page-objects
    ├── ecommerce_page_objects
    |   ├── cool_gadget_site
    |   |   ├── us
    |   |   |   ├── __init__.py
    |   |   |   ├── products.py
    |   |   |   └── product_listings.py
    |   |   ├── fr
    |   |   |   ├── __init__.py
    |   |   |   ├── products.py
    |   |   |   └── product_listings.py
    |   |   └── __init__.py
    |   └── furniture_shop
    |       ├── __init__.py
    |       ├── products.py
    |       └── product_listings.py
    └── setup.py

Requirements for POP
--------------------

Minimum Requirements
~~~~~~~~~~~~~~~~~~~~

This covers the basic use case:

    - Installation of **POP** either from public or private repositories:
  
      - PyPI
      - Git

    - Version specifiers that can be used to accommodate the various parser patches
      that come along in any web data extraction project.
    - Importing the Page Objects directly from the installed package in a project.


This translates into **POPs** needing to have:

    - The ``setup.py`` script which is the standard way of distributing Python packages.

Thus, the most basic way of packaging **POPs** would be:

.. code-block:: python

    from setuptools import setup, find_packages

    setup(
        name='ecommerce-page-objects',
        version='1.0.0',
        packages=find_packages(),
        install_requires=["web-poet"]
    )

This allows the **POP** to be installable via ``pip install ecommerce-page-objects==1.0.0``
`(assuming it's deployed in PyPI)` or via a Git repo like 
``pip install git+https://github.com/some-org/ecommerce-page-objects.git@1.0.0``
`(assuming the repo is public)`.

After installing the **POP**, anyone could access the Page Objects in it
by simply importing them:

.. code-block:: python

    from ecommerce_page_objects.furniture_shop.products import FurnitureProductPage

    response_data = download_response("https://www.furnitureshop.com/product/xyz")
    page = FurnitureProductPage()
    item = page.to_item()

Recommended Requirements
~~~~~~~~~~~~~~~~~~~~~~~~

This covers these use use cases:

    - The minimum requirements and use cases stated above
    - The ability to retrieve the declared :class:`~.OverrideRule`
      inside the **POP**

This means that a list of :class:`~.OverrideRule` must be explicitly
declared in the **POP**. This enables projects using the **POP** to know:

    - which URL Patterns a given Page Object is expected to work
    - what it's trying to override `(or replace)`

This could be done by declaring a ``RULES`` variable that can be
imported as a top-level variable from the package.

For example, suppose our project is named **ecommerce_page_objects**
and is using either of the project structure options discussed in the
previous sections, then we can define the ``RULES`` as the following
inside ``ecommerce_page_objects/ecommerce_page_objects/__init__.py``.

.. code-block:: python

    from web_poet import default_registry, consume_modules

    # This allows all of the OverrideRules declared inside the package
    # using @handle_urls to be properly discovered and loaded.
    consume_modules(__package__)
    RULES = default_registry.get_overrides()

This allows any developer using a **POP** to easily get the list of
:class:`~.OverrideRule` using the convention of accessing it via the
``RULES`` variable as a top-level variable:

.. code-block:: python

    from ecommerce_page_objects import RULES

There may be some circumstances that needs other ways of declaring this.
For such cases, developers/maintainers of **POPs** must reflect that
clearly in the documentation.


Conventions and Best Practices
------------------------------

1. Page Objects should have its classname end with a **Page** suffix.
   This allows for easy identification when used by other developers.

2. The list of :class:`~.OverrideRule` must be declared as a top-level
   variable from the package named ``RULES``. This enables other developers
   to easily retrieve the list of :class:`~.OverrideRule` to be used in
   their own projects.

3. It is recommended to use the ``web_poet.default_registry`` by default
   instead of creating your own custom registries by instantiating
   :class:`~.PageObjectRegistry`. This provides a default expectation
   for developers on which registry to use right from the start.

4. When building a new **POP** based of on existing **POPs**, it is
   recommended to use an **inclusion** strategy rather than **exclusion**
   when selecting the list of :class:`~.OverrideRule` to export.
   This is due to the latter having the risk of being brittle when the
   underlying source **POPs** change. This could lead to a few
   :class:`~.OverrideRule` that are unintentionally included.
