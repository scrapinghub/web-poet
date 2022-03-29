.. _`intro-pop`:

Page Object Projects (POP)
==========================

**POPs** are a way to standardize how a group of Page Objects are packaged
together so they can be uniformly used in other projects. More importantly,
**POPs** could be built using other **POPs**. This allows for continuous
improvements by building **POPs** on top of one another.

Organizing POP
--------------

Developers have complete freedom on how to organize their Page Objects
in their projects. Here are some of the options that developers could use.

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
    |   ├── furniture_shop
    |   |   ├── __init__.py
    |   |   ├── products.py
    |   |   └── product_listings.py
    |   └── __init__.py
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


This means that **POPs** need to have:

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

    response = download_response("https://www.furnitureshop.com/product/xyz")
    page = FurnitureProductPage(response)
    item = page.to_item()

Recommended Requirements
~~~~~~~~~~~~~~~~~~~~~~~~

This covers these use cases:

    - The `minimum requirements` and its use cases 
    - The ability to retrieve the declared :class:`~.OverrideRule`
      available inside the **POP**

This means that a collection of :class:`~.OverrideRule` must be properly
discovered within the **POP**. This enables projects using the **POP** to know:

    - which URL Patterns a given Page Object is expected to work
    - what it's trying to override `(or replace)`

To give an example, suppose our **POP** is named **ecommerce_page_objects**
and is using any of the project structure options discussed in the
previous sections. We can then define the entry point of discovering
all :class:`~.OverrideRule` by writing the following code inside of
``ecommerce-page-objects/ecommerce_page_objects/__init__.py``:

.. code-block:: python

    from web_poet import consume_modules

    # This allows all of the OverrideRules declared inside the package
    # using @handle_urls to be properly discovered and loaded.
    consume_modules(__package__)

.. note::

    Remember, code in Python like annotations are only read and executed
    when the module it belongs to is imported. Thus, in order for all the
    ``@handle_urls`` annotation to properly reflect its data, they need to
    be imported recursively via :func:`~.consume_modules`.

This allows developers to properly access all of the :class:`~.OverrideRule`
declared using the ``@handle_urls`` annotation inside the **POP**. In turn,
this also allows **POPs** which use ``web_poet.default_registry`` to have all
their rules discovered if they are adhering to using Convention **#3**
(see :ref:`best-practices`).

In other words, importing the ``ecommerce_page_objects`` **POP** to a
project immediately loads all of the rules in **web-poet's**
``default_registry``:

.. code-block:: python

    from web_poet import default_registry

    import ecommerce_page_objects

    # All the rules are now available.
    rules = default_registry.get_overrides()

If this recommended requirement is followed properly, there's no need to
call ``consume_modules("ecommerce_page_objects")`` before performing the
:meth:`~.PageObjectRegistry.get_overrides`, since all the :class:`~.OverrideRule`
were already discovered upon **POP** importation.

.. _`best-practices`:


Conventions and Best Practices
------------------------------

1. Page Objects should have its classname end with a **Page** suffix.
   This allows for easy identification when used by other developers.

2. The list of :class:`~.OverrideRule` must be declared as a top-level
   variable from the package named ``REGISTRY``. This enables other developers
   to easily retrieve the list of :class:`~.OverrideRule` to be used in
   their own projects.

3. It is recommended to use the ``web_poet.default_registry`` by default
   instead of creating your own custom registries by instantiating
   :class:`~.PageObjectRegistry`. This provides a default expectation
   for developers on which registry to use right from the start.

    * However, there will be some cases where creating a new instance of
      :class:`~.PageObjectRegistry` is inevitably needed. Here's an
      :ref:`example <overrides-custom-registry>` in the tutorial section.

4. When building a new **POP** based of on existing **POPs**, it is
   recommended to use an **inclusion** strategy rather than **exclusion**
   when selecting the list of :class:`~.OverrideRule` to export.
   This is due to the latter having the risk of being brittle when the
   underlying source **POPs** change. This could lead to a few
   :class:`~.OverrideRule` that are unintentionally included.
