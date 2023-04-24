.. _framework-rules:

================
Supporting rules
================

Ideally, a framework should support returning the right :ref:`page object
<page-objects>` or :ref:`output item <items>` given a target URL and a desired
:ref:`output item type <items>` when :ref:`rules <rules>` are used.

To provide basic support for rules in your framework, use the
:class:`~.RulesRegistry` object at ``web_poet.default_registry`` to choose
a page object based on rules:

.. code-block:: python

    from web_poet import default_registry

    page_cls = default_registry.page_cls_for_item("https://example.com", MyItem)

To give your users more flexibility, you can also let them configure an
alternative :class:`~.RulesRegistry` object to be used for rule resolution.

You should also let your users know what is the best approach to :ref:`load
rules <load-rules>` when using your framework. For example, let them know the
best location for their calls to the :func:`~.web_poet.rules.consume_modules`
function.
