.. _rules:

=====
Rules
=====

Rules are :class:`~.ApplyRule` objects that tell web-poet which :ref:`page
object class <page-object-classes>` to use based on user input, i.e. the target
URL and an output class (a :ref:`page object class <page-object-classes>` or an
:ref:`item class <items>`).

Rules are necessary if you want to use an item class as output class, because
they indicate which page object class to use to generate a given item class.
Rules can also be useful as documentation or to get information about page
object classes programmatically.

:ref:`Rule precedence <rule-precedence>` can also be useful. For example, to
implement generic page object classes that you can override for specific
websites.

Defining rules
==============

The :func:`~.handle_urls` decorator is the simplest way to define a rule for
a page object. For example:

.. _handle_url_example:

.. code-block:: python

    from web_poet import ItemPage, handle_urls

    from my_items import MyItem

    @handle_urls("example.com")
    class MyPage(ItemPage[MyItem]):
        ...

The code above tells web-poet to use the ``MyPage`` :ref:`page object class
<page-object-classes>` when given a URL pointing to the ``example.com`` domain
name and being asked for ``MyPage`` or ``MyItem`` as output class.

Alternatively, you can manually create and register :class:`~.ApplyRule`
objects:

.. code-block:: python

    from url_matcher import Patterns
    from web_poet import ApplyRule, ItemPage, default_registry

    from my_items import MyItem

    class MyPage(ItemPage[MyItem]):
        ...

    rule = ApplyRule(
        for_patterns=Patterns(include=['example.com']),
        use=MyPage,
        to_return=MyItem,
    )
    default_registry.add_rule(rule)

URL patterns
------------

Every rule defines a :class:`url_matcher.Patterns` object that determines if
any given URL is a match for the rule.

:class:`~url_matcher.Patterns` objects offer a simple but powerful syntax for
URL matching. For example:

======================= ===============================================================
Pattern                 Behavior
======================= ===============================================================
(empty string)          Matches any URL
example.com             Matches any URL on the example.com domain and subdomains
example.com/products/   Matches example.com URLs under the /products/ path
example.com?productId=* Matches example.com URLs with productId=… in their query string
======================= ===============================================================

For details and more examples, see the :ref:`url-matcher documentation
<url-matcher:intro>`.

When using the :func:`~handle_urls` decorator, its ``include``, ``exclude``,
and ``priority`` parameters are used to create a :class:`~url_matcher.Patterns`
object. When creating an :class:`~.ApplyRule` object manually, you must create
a :class:`~url_matcher.Patterns` object yourself and pass it to the
``for_patterns`` parameter of :class:`~.ApplyRule`.


.. _rule-precedence:

Rule precedence
---------------

Often you define rules so that a given user input, i.e. a combination of a
target URL and an output class, can only match 1 rule. However, there are
scenarios where it can be useful to define 2 or more rules that can all match a
given user input.

For example, you might want to define a “generic” page object class with some
default implementation of field extraction, e.g. based on semantic markup or
machine learning, and be able to override it based on the input URL, e.g. for
specific websites or URL patterns, with a more specific page object class.

For a given user input, when 2 or more rules are a match, web-poet breaks the
tie as follows:

-   One rule can indicate that its :ref:`page object class
    <page-object-classes>` **overrides** another page object class.

    This is specified by :attr:`ApplyRule.instead_of <~.ApplyRule.instead_of>`.
    When using the :func:`~handle_urls` decorator, the value comes from the
    ``instead_of`` parameter of the decorator.

    For example, the following page object class would override ``MyPage`` from
    :ref:`above <handle_url_example>`:

    .. code-block:: python

        @handle_urls("example.com", instead_of=MyPage)
        class OverridingPage(ItemPage[MyItem]):
            ...

    That is:

    -   If the requested output class is ``MyPage``, an instance of
        ``OverridingPage`` is returned instead.

    -   If the requested output class is ``MyItem``, an instance of
        ``OverridingPage`` is created, and used to build an instance of
        ``MyItem``, which is returned.

-   One rule can declare a higher **priority** than another rule, taking
    precedence.

    Rule priority is determined by the value of
    :attr:`ApplyRule.for_patterns.priority <url_matcher.Patterns.priority>`.
    When using the :func:`~handle_urls` decorator, the value comes from the
    ``priority`` parameter of the decorator. Rule priority is 500 by default.

    For example, given the following page object class:

    .. code-block:: python

        @handle_urls("example.com", priority=501)
        class PriorityPage(ItemPage[MyItem]):
            ...

    The following would happen:

    -   If the requested output class is ``MyItem``, an instance of
        ``PriorityPage`` is created, and used to build an instance of
        ``MyItem``, which is returned.

    -   If the requested output class is ``MyPage``, an instance of
        ``MyPage`` is returned, since ``PriorityPage`` is not defined as an
        override for ``MyPage``.

``instead_of`` triumphs ``priority``: If a rule overrides another rule using
``instead_of``, it does not matter if the overridden rule had a higher
priority.

When multiple rules override the same page object class, through, ``priority``
can break the tie.

If none of those tie breakers are in place, the first rule added to the
registry takes precedence. However, relying on registration order is
discouraged, and you will get a warning if you register 2 or more rules with
the same URL patterns, same output item class, same priority, and no
``instead_of`` value. See also :ref:`rule-conflicts`.


Rule registries
===============

Rules should be stored in a :class:`~.RulesRegistry` object.

web-poet defines a default, global :class:`~.RulesRegistry` object at
``web_poet.default_registry``. Rules defined with the :func:`~.handle_urls`
decorator are added to this registry.

.. _load-rules:

Loading rules
-------------

For a :ref:`framework <frameworks>` to apply your rules, you need to make sure
that your code that adds those rules to ``web_poet.default_registry`` is
executed.

When using the :func:`~web_poet.handle_urls` decorator, that usually means that
you need to make sure that Python imports the files where the decorator is
used.

You can use the :func:`~.web_poet.rules.consume_modules` function in some entry
point of your code for that:

.. code-block:: python

    from web_poet import consume_modules

    consume_modules("my_package.pages", "external_package.pages")

The ideal location for this function depends on your framework. Check the
documentation of your framework for more information.


.. _rule-conflicts:

Rule conflicts
==============

A rule conflict occurs when multiple rules have the same ``instead_of`` and
``priority`` values and can match the same URL.

When it affects rules defined in your code base, solve the conflict adjusting
those ``instead_of`` and ``priority`` values as needed.

When it affects rules from a external package, you have the following options
to solve the conflict:

-   **Subclass** one of the conflicting page object classes in your code base,
    using a similar rule except for a tie-breaking change to its ``instead_of``
    or ``priority`` value.

    For example, if ``package1.A`` and ``package2.B`` are page object classes
    with conflicting rules, with a default priority (500), and you want
    ``package1.A`` to take precedence, declare a new page object class as
    follows:

    .. code-block:: python

        from package1 import A
        from web_poet import handle_urls

        @handle_urls(..., priority=501)
        class NewA(A):
            pass

-   If your :ref:`framework <frameworks>` allows defining a **custom list of
    rules**, you could use :class:`web_poet.default_registry <~.RulesRegistry>`
    methods like :meth:`~.RulesRegistry.get_rules` or
    :meth:`~.RulesRegistry.search` to build such a list, including only rules
    that have no conflicts.
