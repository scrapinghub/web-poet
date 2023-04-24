.. _rules:

=====
Rules
=====

Rules are :class:`~.ApplyRule` objects that tell web-poet which :ref:`page
object class <page-object-classes>` to use for a given combination of input URL
and :ref:`item type <item-types>`.

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
name and being asked for an :ref:`item <items>` of type ``MyItem``.

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
URL matching. For details and examples, see the :ref:`url-matcher documentation
<url-matcher:intro>`.

When using the :func:`~handle_urls` decorator, its ``include``, ``exclude``,
and ``priority`` parameters are used to create a :class:`~url_matcher.Patterns`
object. When creating an :class:`~.ApplyRule` object manually, you must create
a :class:`~url_matcher.Patterns` object manually and pass it to the
``for_patterns`` parameter of :class:`~.ApplyRule`.


.. _rule-precedence:

Rule precedence
---------------

Often you define rules so that a given combination of input URL and
:ref:`item type <item-types>` can only match 1 rule. However, there are
scenarios where it can be useful to define 2 or more rules that can all match a
given combination.

For example, you might want to define a “generic” page object class with some
default implementation of field extraction, e.g. based on semantic markup or
machine learning, and be able to replace it based on the input URL, e.g. for
specific websites or URL patterns, with a more specific page object class.

For a given combination of input URL and item type, when 2 or more rules are a
match, web-poet breaks the tie as follows:

-   One rule can indicate that it replaces the :ref:`page object class
    <page-object-classes>` from another rule, taking precedence.

    This is specified by :attr:`ApplyRule.instead_of <~.ApplyRule.instead_of>`.
    When using the :func:`~handle_urls` decorator, the value comes from the
    ``instead_of`` parameter of the decorator.

    For example, the following page object would override ``MyPage`` from
    :ref:`above <handle_url_example>`:

    .. code-block:: python

        @handle_urls("example.com", instead_of=MyPage)
        class ReplacementPage(ItemPage[MyItem]):
            ...

-   One rule can declare a higher priority than another rule, taking
    precedence.

    Rule priority is determined by the value of
    :attr:`ApplyRule.for_patterns.priority <url_matcher.Patterns.priority>`.
    When using the :func:`~handle_urls` decorator, the value comes from the
    ``priority`` parameter of the decorator. Rule priority is 500 by default.

    For example, the following page object would override ``MyPage`` from
    :ref:`above <handle_url_example>`:

    .. code-block:: python

        @handle_urls("example.com", priority=501)
        class PriorityPage(ItemPage[MyItem]):
            ...

``instead_of`` triumphs ``priority``: If a rule replaces another rule using
``instead_of``, it does not matter if the replaced rule had a higher priority.

If none of those tie breakers are in place, the first rule added to the
registry takes precedence. However, relying on registration order is
discouraged, and you will get a warning if you register 2 or more rules with
the same URL patterns, same output item type, same priority, and no
``instead_of`` value.


Rule registries
===============

Rules should be stored in a :class:`~.RulesRegistry` object.

web-poet defines a default, global :class:`~.RulesRegistry` object at
``web_poet.default_registry``. Rules defined with the :func:`~.handle_urls`
decorator are added to this registry.

Using an alternative :class:`~.RulesRegistry` object is possible if your
:ref:`framework <frameworks>` supports it.

.. _load-rules:

Loading rules
-------------

For a :ref:`framework <frameworks>` to apply your rules, you need to make sure
that your code that adds those rules to the corresponding rules registry is
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
