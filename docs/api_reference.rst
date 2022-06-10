.. _`api-reference`:

=============
API Reference
=============

Page Inputs
===========

.. automodule:: web_poet.page_inputs.browser
   :members:
   :undoc-members:

.. automodule:: web_poet.page_inputs.client
   :members:
   :undoc-members:

.. automodule:: web_poet.page_inputs.http
   :members:
   :undoc-members:

.. automodule:: web_poet.page_inputs.page_params
   :members:
   :undoc-members:

Pages
=====

.. automodule:: web_poet.pages

.. autoclass:: Injectable
   :members:
   :no-special-members:

.. autofunction:: is_injectable

.. autoclass:: ItemPage
   :show-inheritance:
   :members:
   :no-special-members:

.. autoclass:: WebPage
   :show-inheritance:
   :members:
   :undoc-members:
   :inherited-members:
   :no-special-members:

.. autoclass:: ItemWebPage
   :show-inheritance:
   :members:
   :no-special-members:

Mixins
======

.. automodule:: web_poet.mixins

.. autoclass:: web_poet.mixins.ResponseShortcutsMixin
   :members:
   :no-special-members:

Requests
========

.. automodule:: web_poet.requests
    :members:
    :undoc-members:

Exceptions
==========

.. automodule:: web_poet.exceptions.core
    :members:

.. automodule:: web_poet.exceptions.http
    :show-inheritance:
    :members:

.. _`api-overrides`:

Overrides
=========

See the tutorial section on :ref:`intro-overrides` for more context about its
use cases and some examples.

.. autofunction:: web_poet.handle_urls

.. automodule:: web_poet.overrides
   :members:
   :exclude-members: handle_urls
