.. _rules-intro:

Apply Rules
===========

Basic Usage
-----------

@handle_urls
~~~~~~~~~~~~

web-poet provides a :func:`~.handle_urls` decorator, which allows to
declare how a page object can be used (applied):

* for which websites / URL patterns it works,
* which data type (item classes) it can return,
* which page objects it can replace (override; more on this later).

.. code-block:: python

    from web_poet import ItemPage, handle_urls
    from my_items import MyItem

    @handle_urls("example.com")
    class MyPage(ItemPage[MyItem]):
        # ...


``handle_urls("example.com")`` can serve as documentation, but it also enables
getting the information about page objects programmatically.
The information about all page objects decorated with
:func:`~.handle_urls` is stored in ``web_poet.default_registry``, which is
an instance of :class:`~.RulesRegistry`. In the example above, the
following :class:`~.ApplyRule` is added to the registry:

.. code-block::

    ApplyRule(
        for_patterns=Patterns(include=('example.com',), exclude=(), priority=500),
        use=<class 'MyPage'>,
        instead_of=None,
        to_return=<class 'my_items.MyItem'>,
        meta={}
    )

Note how ``rule.to_return`` is set to ``MyItem`` automatically.
Such rules can be used by libraries like `scrapy-poet`_. For example,
if a spider needs to extract ``MyItem`` from some page on the ``example.com``
website, `scrapy-poet`_ now knows that ``MyPage`` page object can be used.

.. _scrapy-poet: https://scrapy-poet.readthedocs.io

Specifying the URL patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:func:`~handle_urls` decorator uses url-matcher_ library to define the
URL rules. Some examples:

.. code-block:: python

    # page object can be applied on any URL from the example.com domain,
    # or from any of its subdomains
    @handle_urls("example.com")

    # page object can be applied on example.com pages under /products/ path
    @handle_urls("example.com/products/")

    # page object can be applied on any URL from example.com, but only if
    # it contains "productId=..." in the query string
    @handle_urls("example.com?productId=*")

The string passed to :func:`~.handle_urls` is converted to
a :class:`url_matcher.matcher.Patterns` instance. Please consult
with the url-matcher_ documentation to learn more about the possible rules;
it is pretty flexible. You can exclude patterns, use wildcards,
require certain query parameters to be present and ignore others, etc.
Unlike regexes, this mini-language "understands" the URL structure.

.. _url-matcher: https://url-matcher.readthedocs.io

.. _rules-intro-overrides:

Overrides
---------

:func:`~.handle_urls` can be used to declare that a particular Page Object
could (and should) be used *instead of* some other Page Object on
certain URL patterns:

.. code-block:: python

    from web_poet import ItemPage, handle_urls
    from my_items import Product
    from my_pages import DefaultProductPage

    @handle_urls("site1.example.com", instead_of=DefaultProductPage)
    class Site1ProductPage(ItemPage[Product]):
        # ...

    @handle_urls("site2.example.com", instead_of=DefaultProductPage)
    class Site2ProductPage(ItemPage[Product]):
        # ...

This concept is a bit more advanced than the basic ``handle_urls`` usage
("this Page Object can return ``MyItem`` on example.com website").

A common use case is a "generic", or a "template" spider, which uses some
default implementation of the extraction, and allows to replace it
("override") on specific websites or URL patterns.

This default page extraction (``DefaultProductPage`` in the example) can be based on
semantic markup, Machine Learning, heuristics, or just be empty. Page Objects which
can be used instead of the default (``Site1ProductPage``, ``Site2ProductPage``)
are commonly written using XPath or CSS selectors, with website-specific rules.

Libraries like scrapy-poet_ allow to create such "generic" spiders by
using the information declared via ``handle_urls(..., instead_of=...)``.

Example Use Case
~~~~~~~~~~~~~~~~

Let's explore an example use case for the Overrides concept.

Suppose we're using Page Objects for our broadcrawl project which explores
eCommerce websites to discover product pages. It wouldn't be entirely possible
for us to create parsers for all websites since we don't know which sites we're
going to crawl beforehand.

However, we could at least create a generic Page Object to support parsing of
some fields in well-known locations of product information like ``<title>``.
This enables our broadcrawler to at least parse some useful information. Let's
call such a Page Object to be ``GenericProductPage``.

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
~~~~~~~~~~~~~~~~~~

To simplify the code examples in the next few subsections, let's assume that
these item classes have been predefined:

.. code-block:: python

    import attrs


    @attrs.define
    class Product:
        product_title: str
        regular_price: float


    @attrs.define
    class SimilarProduct:
        product_title: str
        regular_price: float

Page Object
"""""""""""

Let's take a look at how the following code is structured:

.. code-block:: python

    from web_poet import handle_urls, WebPage, validates_input


    class GenericProductPage(WebPage):
        @validates_input
        def to_item(self) -> Product:
            return Product(product_title=self.css("title::text").get())


    @handle_urls("some.example", instead_of=GenericProductPage)
    class ExampleProductPage(WebPage):
        ...  # more specific parsing


    @handle_urls("another.example", instead_of=GenericProductPage, exclude="/digital-goods/")
    class AnotherExampleProductPage(WebPage):
        ...  # more specific parsing


    @handle_urls(["dual.example/shop/?product=*", "uk.dual.example/store/?pid=*"], instead_of=GenericProductPage)
    class DualExampleProductPage(WebPage):
        ...  # more specific parsing

The code above declares that:

    - The Page Objects return ``Product`` and ``SimilarProduct`` item classes.
      Returning item classes is a preferred approach as explained in the
      :ref:`fields` section.
    - For sites that match the ``some.example`` pattern, ``ExampleProductPage``
      would be used instead of ``GenericProductPage``.
    - The same is true for ``DualExampleProductPage`` where it is used
      instead of ``GenericProductPage`` for two URL patterns which works as
      something like:

      - :sub:`(match) https://www.dual.example/shop/electronics/?product=123`
      - :sub:`(match) https://www.dual.example/shop/books/paperback/?product=849`
      - :sub:`(NO match) https://www.dual.example/on-sale/books/?product=923`
      - :sub:`(match) https://www.uk.dual.example/store/kitchen/?pid=776`
      - :sub:`(match) https://www.uk.dual.example/store/?pid=892`
      - :sub:`(NO match) https://www.uk.dual.example/new-offers/fitness/?pid=892`

    - On the other hand, ``AnotherExampleProductPage`` is used instead of
      ``GenericProductPage`` when we're handling pages that match the
      ``another.example`` URL Pattern, which doesn't contain
      ``/digital-goods/`` in its URL path.

.. tip::

    The URL patterns declared in the ``@handle_urls`` decorator can still be
    further customized. You can read some of the specific parameters in the
    :ref:`API section <api-rules>` of :func:`web_poet.handle_urls`.

.. _rules-item-class-example:

Item Class
""""""""""

An alternative approach for the Page Object Overrides example above is to specify
the returned item class. For example, we could change the previous example into
the following:


.. code-block:: python

    from web_poet import handle_urls, WebPage, validates_input


    class GenericProductPage(WebPage[Product]):
        @validates_input
        def to_item(self) -> Product:
            return Product(product_title=self.css("title::text").get())


    @handle_urls("some.example")
    class ExampleProductPage(WebPage[Product]):
        ...  # more specific parsing


    @handle_urls("another.example", exclude="/digital-goods/")
    class AnotherExampleProductPage(WebPage[Product]):
        ...  # more specific parsing


    @handle_urls(["dual.example/shop/?product=*", "uk.dual.example/store/?pid=*"])
    class DualExampleProductPage(WebPage[Product]):
        ...  # more specific parsing

Let's break this example down:

    - The URL patterns are exactly the same as with the previous code example.
    - The ``@handle_urls`` decorator determines the item class to return (i.e.
      ``Product``) from the decorated Page Object.
    - The ``instead_of`` parameter can be omitted in lieu of the derived Item
      Class from the Page Object which becomes the ``to_return`` attribute in
      :class:`~.ApplyRule` instances. This means that:

        - If a ``Product`` item class is requested for URLs matching with the
          "some.example" pattern, then the ``Product`` item class would come from
          the ``to_item()`` method of ``ExampleProductPage``.
        - Similarly, if a page with a URL matches with "another.example" without
          the "/digital-goods/" path, then the ``Product`` item class comes from
          the ``AnotherExampleProductPage`` Page Object.
        - However, if a ``Product`` item class is requested matching with the URL
          pattern of "dual.example/shop/?product=*", a ``SimilarProduct``
          item class is returned by the ``DualExampleProductPage``'s ``to_item()``
          method instead.

Specifying the item class that a Page Object returns makes it possible for
web-poet frameworks to make Page Object usage transparent to end users.

For example, a web-poet framework could implement a function like:

.. code-block:: python

    item = get_item(url, item_class=Product)

Here there is no reference to the Page Object being used underneath, you only
need to indicate the desired item class, and the web-poet framework
automatically determines the Page Object to use based on the specified URL and
the specified item class.

Note, however, that web-poet frameworks are encouraged to also allow getting a
Page Object instead of an item class instance, for scenarios where end users
wish access to Page Object attributes and methods.


.. _rules-combination:

Combination
"""""""""""

Of course, you can use the combination of both which enables you to specify in
either contexts of Page Objects and item classes.

.. code-block:: python

    from web_poet import handle_urls, WebPage, validates_input


    class GenericProductPage(WebPage[Product]):
        @validates_input
        def to_item(self) -> Product:
            return Product(product_title=self.css("title::text").get())


    @handle_urls("some.example", instead_of=GenericProductPage)
    class ExampleProductPage(WebPage[Product]):
        ...  # more specific parsing


    @handle_urls("another.example", instead_of=GenericProductPage, exclude="/digital-goods/")
    class AnotherExampleProductPage(WebPage[Product]):
        ...  # more specific parsing


    @handle_urls(["dual.example/shop/?product=*", "uk.dual.example/store/?pid=*"], instead_of=GenericProductPage)
    class DualExampleProductPage(WebPage[SimilarProduct]):
        ...  # more specific parsing

See the next :ref:`rules-retrieving` section to observe what are the actual
:class:`~.ApplyRule` that were created by the ``@handle_urls`` decorators.

Working with rules
------------------

.. _rules-retrieving:

Retrieving all available rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :meth:`~.RulesRegistry.get_rules` method from the ``web_poet.default_registry``
allows retrieval of all :class:`~.ApplyRule` in the given registry.
Following from our example above in the :ref:`rules-combination` section, using it
would be:

.. code-block:: python

    from web_poet import default_registry

    # Retrieves all ApplyRules that were registered in the registry
    rules = default_registry.get_rules()

    for r in rules:
        print(r)
    # ApplyRule(for_patterns=Patterns(include=('some.example',), exclude=(), priority=500), use=<class 'ExampleProductPage'>, instead_of=<class 'GenericProductPage'>, to_return=<class 'Product'>, meta={})
    # ApplyRule(for_patterns=Patterns(include=('another.example',), exclude=('/digital-goods/',), priority=500), use=<class 'AnotherExampleProductPage'>, instead_of=<class 'GenericProductPage'>, to_return=<class 'Product'>, meta={})
    # ApplyRule(for_patterns=Patterns(include=('dual.example/shop/?product=*', 'uk.dual.example/store/?pid=*'), exclude=(), priority=500), use=<class 'DualExampleProductPage'>, instead_of=<class 'GenericProductPage'>, to_return=<class 'SimilarProduct'>, meta={})

Remember that using ``@handle_urls`` to annotate the Page Objects would result
in the :class:`~.ApplyRule` to be written into ``web_poet.default_registry``.


.. warning::

    :meth:`~.RulesRegistry.get_rules` relies on the fact that all essential
    packages/modules which contains the :func:`web_poet.handle_urls`
    decorators are properly loaded `(i.e imported)`.

    Thus, for cases like importing and using Page Objects from other external packages,
    the ``@handle_urls`` decorators from these external sources must be read and
    processed properly. This ensures that the external Page Objects have all of their
    :class:`~.ApplyRule` present.

    This can be done via the function named :func:`~.web_poet.rules.consume_modules`.
    Here's an example:

    .. code-block:: python

        from web_poet import default_registry, consume_modules

        consume_modules("external_package_A.po", "another_ext_package.lib")
        rules = default_registry.get_rules()

    The next section explores this caveat further.

Using URLs against the registered rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One of the important aspects of :class:`~.ApplyRule` is dictating which URLs it's
able to work using its ``for_patterns`` attribute. There are a few methods
available in :class:`~.RulesRegistry` which accepts a URL value (:class:`str`,
:class:`~.RequestUrl`, or :class:`~.ResponseUrl`) to find specific information
from the registered rules.

.. _rules-overrides_for-example:

Find the page object overrides
""""""""""""""""""""""""""""""

Suppose you want to see what are the :ref:`rules-intro-overrides` that are
available from a given webpage, you can use :meth:`~.RulesRegistry.overrides_for`
by passing the webpage URL. For example:

.. code-block:: python

    from web_poet import default_registry

    overrides = default_registry.overrides_for("http://books.toscrape.com/")
    print(overrides)

    # {
    #     <class 'OldProductPage'>: <class 'NewProductPage'>,
    #     <class 'OverriddenPage'>: <class 'UseThisPage'>,
    # }

It returns a :class:`Mapping` where the *key* represents the page object class
that is overridden or replaced by the page object class in the *value*.

.. _rules-page_cls_for_item-example:

Identify the page object that could create the item
"""""""""""""""""""""""""""""""""""""""""""""""""""

Suppose you want to retrieve the page object class that is able to create the
item class that you want from a given webpage, you can use
:meth:`~.RulesRegistry.page_cls_for_item`. For example:

.. code-block:: python

    from web_poet import default_registry

    page_cls = default_registry.page_cls_for_item(
        "http://books.toscrape.com/catalogue/sapiens-a-brief-history-of-humankind_996/index.html",
        Book
    )
    print(page_cls)  # BookPage


Using rules from External Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Developers have the option to import existing Page Objects alongside the
:class:`~.ApplyRule` attached to them. This section aims to showcase different
scenarios that come up when using multiple Page Object Projects.

.. _rules-using-all:

Using all available ApplyRules from multiple Page Object Projects
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Let's suppose we have the following use case before us:

    - An **external** Python package named ``ecommerce_page_objects`` is available
      which contains Page Objects for common websites.
    - Another similar **external** package named ``gadget_sites_page_objects`` is
      available for even more specific websites.
    - Your project's objective is to handle as much eCommerce websites as you
      can.

        - Thus, you'd want to use the already available packages above and
          perhaps improve on them or create new Page Objects for new websites.

Remember that all of the :class:`~.ApplyRule` are declared by annotating
Page Objects using the :func:`web_poet.handle_urls` via ``@handle_urls``. Thus,
they can easily be accessed using the :meth:`~.RulesRegistry.get_rules`
of ``web_poet.default_registry``.

This can be done something like:

.. code-block:: python

    from web_poet import default_registry, consume_modules

    # ❌ Remember that this wouldn't retrieve any rules at all since the
    # ``@handle_urls`` decorators are NOT properly loaded.
    rules = default_registry.get_rules()
    print(rules)  # []

    # ✅ Instead, you need to run the following so that all of the Page
    # Objects in the external packages are recursively imported.
    consume_modules("ecommerce_page_objects", "gadget_sites_page_objects")
    rules = default_registry.get_rules()

    # The collected rules would then be as follows:
    print(rules)
    # 1. ApplyRule(for_patterns=Patterns(include=['site_1.example'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_1.EcomSite1'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, to_return=None, meta={})
    # 2. ApplyRule(for_patterns=Patterns(include=['site_2.example'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, to_return=None, meta={})
    # 3. ApplyRule(for_patterns=Patterns(include=['site_2.example'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_2.GadgetSite2'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, to_return=None, meta={})
    # 4. ApplyRule(for_patterns=Patterns(include=['site_3.example'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_3.GadgetSite3'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, to_return=None, meta={})

.. note::

    Once :func:`~.web_poet.rules.consume_modules` is called, then all
    external Page Objects are recursively imported and available for the entire
    runtime duration. Calling :func:`~.web_poet.rules.consume_modules` again
    makes no difference unless a new set of modules are provided.

.. _rules-using-subset:

Using only a subset of the available ApplyRules
"""""""""""""""""""""""""""""""""""""""""""""""

Suppose that the use case from the previous section has changed wherein a
subset of :class:`~.ApplyRule` would be used. This could be achieved by
using the :meth:`~.RulesRegistry.search` method which allows for
convenient selection of a subset of rules from a given registry.

Here's an example of how you could manually select the rules using the
:meth:`~.RulesRegistry.search` method instead:

.. code-block:: python

    from web_poet import default_registry, consume_modules
    import ecommerce_page_objects, gadget_sites_page_objects

    consume_modules("ecommerce_page_objects", "gadget_sites_page_objects")

    ecom_rules = default_registry.search(instead_of=ecommerce_page_objects.EcomGenericPage)
    print(ecom_rules)
    # ApplyRule(for_patterns=Patterns(include=['site_1.example'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_1.EcomSite1'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, to_return=None, meta={})
    # ApplyRule(for_patterns=Patterns(include=['site_2.example'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, to_return=None, meta={})

    gadget_rules = default_registry.search(use=gadget_sites_page_objects.site_3.GadgetSite3)
    print(gadget_rules)
    # ApplyRule(for_patterns=Patterns(include=['site_3.example'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_3.GadgetSite3'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, to_return=None, meta={})

    rules = ecom_rules + gadget_rules
    print(rules)
    # ApplyRule(for_patterns=Patterns(include=['site_1.example'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_1.EcomSite1'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, to_return=None, meta={})
    # ApplyRule(for_patterns=Patterns(include=['site_2.example'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, to_return=None, meta={})
    # ApplyRule(for_patterns=Patterns(include=['site_3.example'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_3.GadgetSite3'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, to_return=None, meta={})

As you can see, using the :meth:`~.RulesRegistry.search` method allows you to
conveniently select for :class:`~.ApplyRule` which conform to a specific criteria. This
allows you to conveniently drill down to which :class:`~.ApplyRule` you're interested in
using.

.. _rules-custom-registry:

Creating a new registry
"""""""""""""""""""""""

After gathering all the pre-selected rules, we can then store it in a new instance
of :class:`~.RulesRegistry` in order to separate it from the ``default_registry``
which contains all of the rules. We can use the ``RulesRegistry(rules=...)``
for this:

.. code-block:: python

    from web_poet import RulesRegistry

    my_new_registry = RulesRegistry(rules=rules)


.. _rules-improve-po:

Improving on external Page Objects
""""""""""""""""""""""""""""""""""

There would be cases wherein you're using Page Objects with :class:`~.ApplyRule`
from external packages only to find out that a few of them lacks some of the
fields or features that you need.

Let's suppose that we wanted to use `all` of the :class:`~.ApplyRule` similar
to this section: :ref:`rules-using-all`. However, the ``EcomSite1`` Page Object
needs to properly handle some edge cases where some fields are not being extracted
properly. One way to fix this is to subclass the said Page Object and improve its
``to_item()`` method, or even creating a new class entirely. For simplicity, let's
have the first approach as an example:

.. code-block:: python

    from web_poet import default_registry, consume_modules, handle_urls, validates_input
    import ecommerce_page_objects, gadget_sites_page_objects

    consume_modules("ecommerce_page_objects", "gadget_sites_page_objects")
    rules = default_registry.get_rules()

    # The collected rules would then be as follows:
    print(rules)
    # 1. ApplyRule(for_patterns=Patterns(include=['site_1.example'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_1.EcomSite1'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, to_return=None, meta={})
    # 2. ApplyRule(for_patterns=Patterns(include=['site_2.example'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, to_return=None, meta={})
    # 3. ApplyRule(for_patterns=Patterns(include=['site_2.example'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_2.GadgetSite2'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, to_return=None, meta={})
    # 4. ApplyRule(for_patterns=Patterns(include=['site_3.example'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_3.GadgetSite3'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, to_return=None, meta={})

    @handle_urls("site_1.example", instead_of=ecommerce_page_objects.EcomGenericPage, priority=1000)
    class ImprovedEcomSite1(ecommerce_page_objects.site_1.EcomSite1):
        @validates_input
        def to_item(self):
            ...  # call super().to_item() and improve on the item's shortcomings

    rules = default_registry.get_rules()
    print(rules)
    # 1. ApplyRule(for_patterns=Patterns(include=['site_1.example'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_1.EcomSite1'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, to_return=None, meta={})
    # 2. ApplyRule(for_patterns=Patterns(include=['site_2.example'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, to_return=None, meta={})
    # 3. ApplyRule(for_patterns=Patterns(include=['site_2.example'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_2.GadgetSite2'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, to_return=None, meta={})
    # 4. ApplyRule(for_patterns=Patterns(include=['site_3.example'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_3.GadgetSite3'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, to_return=None, meta={})
    # 5. ApplyRule(for_patterns=Patterns(include=['site_1.example'], exclude=[], priority=1000), use=<class 'my_project.ImprovedEcomSite1'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, to_return=None, meta={})

Notice that we're adding a new :class:`~.ApplyRule` for the same URL pattern
for ``site_1.example``.

When the time comes that a Page Object needs to be selected when parsing ``site_1.example``
and it needs to replace ``ecommerce_page_objects.EcomGenericPage``, rules **#1**
and **#5** will be the choices. However, since we've assigned a much **higher priority**
for the new rule in **#5** than the default ``500`` value,  rule **#5** will be
chosen because of its higher priority value.

More details on this in the :ref:`Priority Resolution <rules-priority-resolution>`
subsection.


Handling conflicts when using Multiple External Packages
""""""""""""""""""""""""""""""""""""""""""""""""""""""""

You might've observed from the previous section that retrieving the list of all
:class:`~.ApplyRule` from two different external packages may result in a
conflict.

We can take a look at the rules for **#2** and **#3** when we were importing all
available rules:

.. code-block:: python

    # 2. ApplyRule(for_patterns=Patterns(include=['site_2.example'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'ecommerce_page_objects.EcomGenericPage'>, to_return=None, meta={})
    # 3. ApplyRule(for_patterns=Patterns(include=['site_2.example'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_2.GadgetSite2'>, instead_of=<class 'gadget_sites_page_objects.GadgetGenericPage'>, to_return=None, meta={})

However, it's technically **NOT** a `conflict`, **yet**, since:

    - ``ecommerce_page_objects.site_2.EcomSite2`` would only be used in **site_2.example**
      if ``ecommerce_page_objects.EcomGenericPage`` is to be replaced.
    - The same case with ``gadget_sites_page_objects.site_2.GadgetSite2`` wherein
      it's only going to be utilized for **site_2.example** if the following is to be
      replaced: ``gadget_sites_page_objects.GadgetGenericPage``.

It would be only become a conflict if both rules for **site_2.example** `intend to
replace the` **same** `Page Object`.

However, let's suppose that there are some :class:`~.ApplyRule` which actually
result in a conflict. To give an example, let's suppose that rules **#2** and **#3**
`intends to replace the` **same** `Page Object`. It would look something like:

.. code-block:: python

    # 2. ApplyRule(for_patterns=Patterns(include=['site_2.example'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'common_items.ProductGenericPage'>, to_return=None, meta={})
    # 3. ApplyRule(for_patterns=Patterns(include=['site_2.example'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_2.GadgetSite2'>, instead_of=<class 'common_items.ProductGenericPage'>, to_return=None, meta={})

Notice that the ``instead_of`` param are the same and only the ``use`` param
remained different.

There are two main ways we recommend in solving this.

.. _rules-priority-resolution:

**1. Priority Resolution**

If you notice, the ``for_patterns`` attribute of :class:`~.ApplyRule` is an
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
:class:`~.ApplyRule`. This is made by design so that they are hashable and could
be deduplicated immediately without consequences of them changing in value.

The only way that the ``priority`` value can be changed is by creating a new
:class:`~.ApplyRule` with a different ``priority`` value (`higher if it needs
more priority`). You don't necessarily need to `delete` the **old**
:class:`~.ApplyRule` since they will be resolved via ``priority`` anyways.

Creating a new :class:`~.ApplyRule` with a higher priority could be as easy as:

    1. Subclassing the Page Object in question.
    2. Declare a new :func:`web_poet.handle_urls` decorator with the same URL
       pattern and Page Object to override but with a much higher priority.

Here's an example:

.. code-block:: python

    from web_poet import default_registry, consume_modules, handle_urls, validates_input
    import ecommerce_page_objects, gadget_sites_page_objects, common_items

    @handle_urls("site_2.example", instead_of=common_items.ProductGenericPage, priority=1000)
    class EcomSite2Copy(ecommerce_page_objects.site_1.EcomSite1):
        @validates_input
        def to_item(self):
            return super().to_item()

Now, the conflicting **#2** and **#3** rules would never be selected because of
the new :class:`~.ApplyRule` having a much higher priority (see rule **#4**):

.. code-block:: python

    # 2. ApplyRule(for_patterns=Patterns(include=['site_2.example'], exclude=[], priority=500), use=<class 'ecommerce_page_objects.site_2.EcomSite2'>, instead_of=<class 'common_items.ProductGenericPage'>, to_return=None, meta={})
    # 3. ApplyRule(for_patterns=Patterns(include=['site_2.example'], exclude=[], priority=500), use=<class 'gadget_sites_page_objects.site_2.GadgetSite2'>, instead_of=<class 'common_items.ProductGenericPage'>, to_return=None, meta={})

    # 4. ApplyRule(for_patterns=Patterns(include=['site_2.example'], exclude=[], priority=1000), use=<class 'my_project.EcomSite2Copy'>, instead_of=<class 'common_items.ProductGenericPage'>, to_return=None, meta={})

A similar idea was also discussed in the :ref:`rules-improve-po` section.


**2. Specifically Selecting the Rules**

When the last resort of ``priority``-resolution doesn't work, then you could always
specifically select the list of :class:`~.ApplyRule` you want to use.

We **recommend** in creating an **inclusion**-list rather than an **exclusion**-list
since the latter is quite brittle. For instance, an external package you're using
has updated its rules and the exlusion strategy misses out on a few rules that
were recently added. This could lead to a `silent-error` of receiving a different
set of rules than expected.

This **inclusion**-list approach can be done by importing the Page Objects directly
and creating instances of :class:`~.ApplyRule` from it. You could also import
all of the available :class:`~.ApplyRule` using :meth:`~.RulesRegistry.get_rules`
to sift through the list of available rules and manually selecting the rules you need.

Most of the time, the needed rules are the ones which uses the Page Objects we're
interested in. You can use :meth:`~.RulesRegistry.search` to get
them (see :ref:`rules-using-subset`):

.. code-block:: python

    from web_poet import default_registry, consume_modules
    import package_A, package_B, package_C

    consume_modules("package_A", "package_B", "package_C")

    rules = default_registry.search(use=package_A.PageObject1) + \
            default_registry.search(use=package_B.PageObject2) + \
            default_registry.search(use=package_C.PageObject3)

    # ApplyRule(for_patterns=Patterns(include=['site_A.example'], exclude=[], priority=500), use=<class 'package_A.PageObject1'>, instead_of=<class 'GenericPage'>, to_return=None, meta={})
    # ApplyRule(for_patterns=Patterns(include=['site_B.example'], exclude=[], priority=500), use=<class 'package_B.PageObject2'>, instead_of=<class 'GenericPage'>, to_return=None, meta={})
    # ApplyRule(for_patterns=Patterns(include=['site_C.example'], exclude=[], priority=500), use=<class 'package_C.PageObject3'>, instead_of=<class 'GenericPage'>, to_return=None, meta={})


Another example:

.. code-block:: python

    from url_matcher import Patterns
    from web_poet import default_registry, consume_modules
    import package_A, package_B, package_C

    consume_modules("package_A", "package_B", "package_C")

    rule_from_A = default_registry.search(use=package_A.PageObject1)
    print(rule_from_A)
    # [ApplyRule(for_patterns=Patterns(include=['site_A.example'], exclude=[], priority=500), use=<class 'package_A.PageObject1'>, instead_of=<class 'GenericPage'>, to_return=None, meta={})]

    rule_from_B = default_registry.search(instead_of=GenericProductPage)
    print(rule_from_B)
    # []

    rule_from_C = default_registry.search(for_patterns=Patterns(include=["site_C.example"]))
    print(rule_from_C)
    # [
    #     ApplyRule(for_patterns=Patterns(include=['site_C.example'], exclude=[], priority=500), use=<class 'package_C.PageObject3'>, instead_of=<class 'GenericPage'>, to_return=None, meta={}),
    #     ApplyRule(for_patterns=Patterns(include=['site_C.example'], exclude=[], priority=1000), use=<class 'package_C.PageObject3_improved'>, instead_of=<class 'GenericPage'>, to_return=None, meta={})
    # ]

    rules = rule_from_A + rule_from_B + rule_from_C
