.. _`intro-overrides`:

Overrides
=========

Overrides contains mapping rules to associate which URLs a particular
Page Object would be used. The URL matching rules is handled by another library
called `url-matcher <https://url-matcher.readthedocs.io>`_.

Using such rules establishes the core concept of Overrides wherein a developer
could declare that a specific Page Object must be used *(instead of another)*
for a given set of URL patterns.

This enables **web-poet** to be used effectively by other frameworks like 
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

Let's take a look at how the following code is structured:

.. code-block:: python

    from web_poet import handle_urls, WebPage


    class GenericProductPage(WebPage):
        def to_item(self):
            return {"product-title": self.css("title::text").get()}


    @handle_urls("example.com", overrides=GenericProductPage)
    class ExampleProductPage(WebPage):
        def to_item(self):
            ...  # more specific parsing


    @handle_urls("anotherexample.com", overrides=GenericProductPage, exclude="/digital-goods/")
    class AnotherExampleProductPage(WebPage):
        def to_item(self):
            ...  # more specific parsing


    @handle_urls(["dualexample.com/shop/?product=*", "dualexample.net/store/?pid=*"], overrides=GenericProductPage)
    class DualExampleProductPage(WebPage):
        def to_item(self):
            ...  # more specific parsing

The code above declares that:

    - For sites that match the ``example.com`` pattern, ``ExampleProductPage``
      would be used instead of ``GenericProductPage``.
    - The same is true for ``DualExampleProductPage`` where it is used
      instead of ``GenericProductPage`` for two URL patterns which works as
      something like:

      - :sub:`(match) https://www.dualexample.com/shop/electronics/?product=123`
      - :sub:`(match) https://www.dualexample.com/shop/books/paperback/?product=849`
      - :sub:`(NO match) https://www.dualexample.com/on-sale/books/?product=923`
      - :sub:`(match) https://www.dualexample.net/store/kitchen/?pid=776`
      - :sub:`(match) https://www.dualexample.net/store/?pid=892`
      - :sub:`(NO match) https://www.dualexample.net/new-offers/fitness/?pid=892`

    - On the other hand, ``AnotherExampleProductPage`` is only used instead of
      ``GenericProductPage`` when we're handling pages from ``anotherexample.com``
      that doesn't contain ``/digital-goods/`` in its URL path.

.. tip::

    The URL patterns declared in the ``@handle_urls`` annotation can still be
    further customized. You can read some of the specific parameters in the
    :ref:`API section <api-overrides>` of :func:`web_poet.handle_urls`.


Retrieving all available Overrides
----------------------------------

The :meth:`~.PageObjectRegistry.get_overrides` method from the ``web_poet.default_registry``
allows retrieval of  all :class:`~.OverrideRule` in the given registry.
Following from our example above, using it would be:

.. code-block:: python

    from web_poet import default_registry

    # Retrieves all OverrideRules that were registered in the registry
    rules = default_registry.get_overrides()

    print(len(rules))  # 3
    print(rules[0])    # OverrideRule(for_patterns=Patterns(include=['example.com'], exclude=[], priority=500), use=<class 'my_project.page_objects.ExampleProductPage'>, instead_of=<class 'my_project.page_objects.GenericProductPage'>, meta={})

Remember that using ``@handle_urls`` to annotate the Page Objects would result
in the :class:`~.OverrideRule` to be written into ``web_poet.default_registry``.


.. warning::

    :meth:`~.PageObjectRegistry.get_overrides` relies on the fact that all essential
    packages/modules which contains the :func:`web_poet.handle_urls`
    annotations are properly loaded `(i.e imported)`.

    Thus, for cases like importing and using Page Objects from other external packages,
    the ``@handle_urls`` annotations from these external sources must be read and
    processed properly. This ensures that the external Page Objects have all of their
    :class:`~.OverrideRule` present.

    This can be done via the function named :func:`~.web_poet.overrides.consume_modules`.
    Here's an example:

    .. code-block:: python

        from web_poet import default_registry, consume_modules

        consume_modules("external_package_A.po", "another_ext_package.lib")
        rules = default_registry.get_overrides()

    The next section explores this caveat further.


Using Overrides from External Packages
--------------------------------------

Developers have the option to import existing Page Objects alongside the
:class:`~.OverrideRule` attached to them. This section aims to showcase different
scenarios that come up when using multiple Page Object Projects.

.. _`intro-rule-all`:

Using all available OverrideRules from multiple Page Object Projects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's suppose we have the following use case before us:

    - An **external** Python package named ``ecommerce_page_objects`` is available
      which contains Page Objects for common websites.
    - Another similar **external** package named ``gadget_sites_page_objects`` is
      available for even more specific websites.
    - Your project's objective is to handle as much eCommerce websites as you
      can.

        - Thus, you'd want to use the already available packages above and
          perhaps improve on them or create new Page Objects for new websites.

Remember that all of the :class:`~.OverrideRule` are declared by annotating
Page Objects using the :func:`web_poet.handle_urls` via ``@handle_urls``. Thus,
they can easily be accessed using the :meth:`~.PageObjectRegistry.get_overrides`
of ``web_poet.default_registry``.

This can be done something like:

.. code-block:: python

    from web_poet import default_registry, consume_modules

    # ❌ Remember that this wouldn't retrieve any rules at all since the
    # annotations are NOT properly imported.
    rules = default_registry.get_overrides()
    print(rules)  # []

    # ✅ Instead, you need to run the following so that all of the Page
    # Objects in the external packages are recursively imported.
    consume_modules("ecommerce_page_objects", "gadget_sites_page_objects")
    rules = default_registry.get_overrides()

    # The collected rules would then be as follows:
    print(rules)
    # 1. OverrideRule(for_patterns=Patterns(include=['site_1.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_1.EcomSite1'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, meta={})
    # 2. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, meta={})
    # 3. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_2.GadgetSite2'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, meta={})
    # 4. OverrideRule(for_patterns=Patterns(include=['site_3.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_3.GadgetSite3'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, meta={})

.. note::

    Once :func:`~.web_poet.overrides.consume_modules` is called, then all
    external Page Objects are recursively imported and available for the entire
    runtime duration. Calling :func:`~.web_poet.overrides.consume_modules` again
    makes no difference unless a new set of modules are provided.

.. _`intro-rule-subset`:

Using only a subset of the available OverrideRules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Suppose that the use case from the previous section has changed wherein a
subset of :class:`~.OverrideRule` would be used. This could be achieved by
using the :meth:`~.PageObjectRegistry.search_overrides` method which allows for
convenient selection of a subset of rules from a given registry.

Here's an example of how you could manually select the rules using the
:meth:`~.PageObjectRegistry.search_overrides` method instead:

.. code-block:: python

    from web_poet import default_registry, consume_modules
    import ecommerce_page_objects, gadget_sites_page_objects

    consume_modules("ecommerce_page_objects", "gadget_sites_page_objects")

    ecom_rules = default_registry.search_overrides(instead_of=ecommerce_page_objects.EcomGenericPage)
    print(ecom_rules)
    # OverrideRule(for_patterns=Patterns(include=['site_1.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_1.EcomSite1'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, meta={})
    # OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, meta={})

    gadget_rules = default_registry.search_overrides(use=gadget_sites_page_objects.site_3.GadgetSite3)
    print(gadget_rules)
    # OverrideRule(for_patterns=Patterns(include=['site_3.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_3.GadgetSite3'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, meta={})

    rules = ecom_rules + gadget_rules
    print(rules)
    # OverrideRule(for_patterns=Patterns(include=['site_1.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_1.EcomSite1'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, meta={})
    # OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, meta={})
    # OverrideRule(for_patterns=Patterns(include=['site_3.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_3.GadgetSite3'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, meta={})

As you can see, using the :meth:`~.PageObjectRegistry.search_overrides` method allows you to
conveniently select for :class:`~.OverrideRule` which conform to a specific criteria. This
allows you to conveniently drill down to which :class:`~.OverrideRule` you're interested in
using.

.. _`overrides-custom-registry`:

After gathering all the pre-selected rules, we can then store it in a new instance
of :class:`~.PageObjectRegistry` in order to separate it from the ``default_registry``
which contains all of the rules. We can use the :meth:`~.PageObjectRegistry.from_override_rules`
for this:

.. code-block:: python

    from web_poet import PageObjectRegistry

    my_new_registry = PageObjectRegistry.from_override_rules(rules)


.. _`intro-improve-po`:

Improving on external Page Objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There would be cases wherein you're using Page Objects with :class:`~.OverrideRule`
from external packages only to find out that a few of them lacks some of the
fields or features that you need.

Let's suppose that we wanted to use `all` of the :class:`~.OverrideRule` similar
to this section: :ref:`intro-rule-all`. However, the ``EcomSite1`` Page Object
needs to properly handle some edge cases where some fields are not being extracted
properly. One way to fix this is to subclass the said Page Object and improve its
``to_item()`` method, or even creating a new class entirely. For simplicity, let's
have the first approach as an example:

.. code-block:: python

    from web_poet import default_registry, consume_modules, handle_urls
    import ecommerce_page_objects, gadget_sites_page_objects

    consume_modules("ecommerce_page_objects", "gadget_sites_page_objects")
    rules = default_registry.get_overrides()

    # The collected rules would then be as follows:
    print(rules)
    # 1. OverrideRule(for_patterns=Patterns(include=['site_1.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_1.EcomSite1'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, meta={})
    # 2. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, meta={})
    # 3. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_2.GadgetSite2'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, meta={})
    # 4. OverrideRule(for_patterns=Patterns(include=['site_3.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_3.GadgetSite3'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, meta={})

    @handle_urls("site_1.com", overrides=ecommerce_page_objects.EcomGenericPage, priority=1000)
    class ImprovedEcomSite1(ecommerce_page_objects.site_1.EcomSite1):
        def to_item(self):
            ...  # call super().to_item() and improve on the item's shortcomings

    rules = default_registry.get_overrides()
    print(rules)
    # 1. OverrideRule(for_patterns=Patterns(include=['site_1.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_1.EcomSite1'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, meta={})
    # 2. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, meta={})
    # 3. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_2.GadgetSite2'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, meta={})
    # 4. OverrideRule(for_patterns=Patterns(include=['site_3.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_3.GadgetSite3'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, meta={})
    # 5. OverrideRule(for_patterns=Patterns(include=['site_1.com'], exclude=[], priority=1000), use=<class 'my_project.ImprovedEcomSite1'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, meta={})

Notice that we're adding a new :class:`~.OverrideRule` for the same URL pattern
for ``site_1.com``.

When the time comes that a Page Object needs to be selected when parsing ``site_1.com``
and it needs to replace ``ecommerce_page_objects.EcomGenericPage``, rules **#1**
and **#5** will be the choices. However, since we've assigned a much **higher priority**
for the new rule in **#5** than the default ``500`` value,  rule **#5** will be
chosen because of its higher priority value.

More details on this in the :ref:`Priority Resolution <priority-resolution>`
subsection.


Handling conflicts from using Multiple External Packages
--------------------------------------------------------

You might've observed from the previous section that retrieving the list of all
:class:`~.OverrideRule` from two different external packages may result in a
conflict. 

We can take a look at the rules for **#2** and **#3** when we were importing all
available rules:

.. code-block:: python

    # 2. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, meta={})
    # 3. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_2.GadgetSite2'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, meta={})

However, it's technically **NOT** a `conflict`, **yet**, since:

    - ``ecommerce_page_objects.site_2.EcomSite2`` would only be used in **site_2.com**
      if ``ecommerce_page_objects.EcomGenericPage`` is to be replaced.
    - The same case with ``gadget_sites_page_objects.site_2.GadgetSite2`` wherein
      it's only going to be utilized for **site_2.com** if the following is to be
      replaced: ``gadget_sites_page_objects.GadgetGenericPage``.

It would be only become a conflict if both rules for **site_2.com** `intend to
replace the` **same** `Page Object`.

However, let's suppose that there are some :class:`~.OverrideRule` which actually
result in a conflict. To give an example, let's suppose that rules **#2** and **#3**
`intends to replace the` **same** `Page Object`. It would look something like:

.. code-block:: python

    # 2. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'common_items.ProductGenericPage'>, meta={})
    # 3. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_2.GadgetSite2'>, instead_of=<class 'common_items.ProductGenericPage'>, meta={})

Notice that the ``instead_of`` param are the same and only the ``use`` param
remained different.

There are two main ways we recommend in solving this.

.. _`priority-resolution`:

**1. Priority Resolution**

If you notice, the ``for_patterns`` attribute of :class:`~.OverrideRule` is an
instance of `url_matcher.Patterns
<https://url-matcher.readthedocs.io/en/stable/api_reference.html#module-url-matcher>`_.
This instance also has a ``priority`` param where a higher value will be chosen
in times of conflict.

.. note::

    The `url-matcher`_ library is the one responsible breaking such ``priority`` conflicts
    `(amongst others)`. It's specifically discussed in this section: `rules-conflict-resolution
    <https://url-matcher.readthedocs.io/en/stable/intro.html#rules-conflict-resolution>`_.

Unfortunately, updating the ``priority`` value directly isn't possible as the
:class:`url_matcher.Patterns` is a **frozen** `dataclass`. The same is true for
:class:`~.OverrideRule`. This is made by design so that they are hashable and could
be deduplicated immediately without consequences of them changing in value.

The only way that the ``priority`` value can be changed is by creating a new
:class:`~.OverrideRule` with a different ``priority`` value (`higher if it needs
more priority`). You don't necessarily need to `delete` the **old**
:class:`~.OverrideRule` since they will be resolved via ``priority`` anyways.

Creating a new :class:`~.OverrideRule` with a higher priority could be as easy as:

    1. Subclassing the Page Object in question.
    2. Create a new :func:`web_poet.handle_urls` annotation with the same URL
       pattern and Page Object to override but with a much higher priority.

Here's an example:

.. code-block:: python

    from web_poet import default_registry, consume_modules, handle_urls
    import ecommerce_page_objects, gadget_sites_page_objects, common_items

    @handle_urls("site_2.com", overrides=common_items.ProductGenericPage, priority=1000)
    class EcomSite2Copy(ecommerce_page_objects.site_1.EcomSite1):
        def to_item(self):
            return super().to_item()

Now, the conflicting **#2** and **#3** rules would never be selected because of
the new :class:`~.OverrideRule` having a much higher priority (see rule **#4**):

.. code-block:: python

    # 2. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'common_items.ProductGenericPage'>, meta={})
    # 3. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_2.GadgetSite2'>, instead_of=<class 'common_items.ProductGenericPage'>, meta={})

    # 4. OverrideRule(for_patterns=Patterns(include=['site_2.com'], exclude=[], priority=1000), use=<class 'my_project.EcomSite2Copy'>, instead_of=<class 'common_items.ProductGenericPage'>, meta={})

A similar idea was also discussed in the :ref:`intro-improve-po` section.


**2. Specifically Selecting the Rules**

When the last resort of ``priority``-resolution doesn't work, then you could always
specifically select the list of :class:`~.OverrideRule` you want to use.

We **recommend** in creating an **inclusion**-list rather than an **exclusion**-list
since the latter is quite brittle. For instance, an external package you're using
has updated its rules and the exlusion strategy misses out on a few rules that
were recently added. This could lead to a `silent-error` of receiving a different
set of rules than expected.

This **inclusion**-list approach can be done by importing the Page Objects directly
and creating instances of :class:`~.OverrideRule` from it. You could also import
all of the available :class:`~.OverrideRule` using :meth:`~.PageObjectRegistry.get_overrides`
to sift through the list of available rules and manually selecting the rules you need.

Most of the time, the needed rules are the ones which uses the Page Objects we're
interested in. Since :class:`~.PageObjectRegistry` is a ``dict`` subclass, you can
easily find the Page Object's rule using its `key`. Here's an example:

.. code-block:: python

    from web_poet import default_registry, consume_modules
    import package_A, package_B, package_C

    consume_modules("package_A", "package_B", "package_C")

    rules = [
        default_registry[package_A.PageObject1],  # OverrideRule(for_patterns=Patterns(include=['site_A.com'], exclude=[], priority=500), use=<class 'package_A.PageObject1'>, instead_of=<class 'GenericPage'>, meta={})
        default_registry[package_B.PageObject2],  # OverrideRule(for_patterns=Patterns(include=['site_B.com'], exclude=[], priority=500), use=<class 'package_B.PageObject2'>, instead_of=<class 'GenericPage'>, meta={})
        default_registry[package_C.PageObject3],  # OverrideRule(for_patterns=Patterns(include=['site_C.com'], exclude=[], priority=500), use=<class 'package_C.PageObject3'>, instead_of=<class 'GenericPage'>, meta={})
    ]

Another approach would be using the :meth:`~.PageObjectRegistry.search_overrides`
functionality as described from this tutorial section: :ref:`intro-rule-subset`.
The :meth:`~.PageObjectRegistry.search_overrides` is quite useful in cases wherein
the **POP** contains a lot of rules as it presents a utility for programmatically
searching for them.

Here's an example:

.. code-block:: python

    from url_matcher import Patterns
    from web_poet import default_registry, consume_modules
    import package_A, package_B, package_C

    consume_modules("package_A", "package_B", "package_C")

    rule_from_A = default_registry.search_overrides(use=package_A.PageObject1)
    print(rule_from_A)
    # [OverrideRule(for_patterns=Patterns(include=['site_A.com'], exclude=[], priority=500), use=<class 'package_A.PageObject1'>, instead_of=<class 'GenericPage'>, meta={})]

    rule_from_B = default_registry.search_overrides(instead_of=GenericProductPage)
    print(rule_from_B)
    # []

    rule_from_C = default_registry.search_overrides(for_patterns=Patterns(include=["site_C.com"]))
    print(rule_from_C)
    # [
    #     OverrideRule(for_patterns=Patterns(include=['site_C.com'], exclude=[], priority=500), use=<class 'package_C.PageObject3'>, instead_of=<class 'GenericPage'>, meta={}),
    #     OverrideRule(for_patterns=Patterns(include=['site_C.com'], exclude=[], priority=1000), use=<class 'package_C.PageObject3_improved'>, instead_of=<class 'GenericPage'>, meta={})
    # ]

    rules = rule_from_A + rule_from_B + rule_from_C
