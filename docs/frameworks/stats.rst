.. _framework-stats:

================
Supporting stats
================

To support :ref:`stats <stats>`, your framework must provide the
:class:`~web_poet.page_inputs.stats.StatCollector` implementation of
:class:`~web_poet.page_inputs.stats.Stats`.

It is up to you to decide how to store the stats, and how your users can access
them at run time (outside page objects) or afterwards.
