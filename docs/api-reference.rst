.. _api-reference:

=============
API reference
=============

.. _input:

Page Inputs
===========

.. module:: web_poet.page_inputs

.. automodule:: web_poet.page_inputs.browser
   :members:
   :undoc-members:
   :inherited-members: str
   :show-inheritance:

.. automodule:: web_poet.page_inputs.http
   :members:
   :undoc-members:
   :inherited-members: str,bytes,MultiDict
   :show-inheritance:

.. automodule:: web_poet.page_inputs.page_params
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: web_poet.page_inputs.client
   :members:
   :undoc-members:

Pages
=====

.. automodule:: web_poet.pages

.. autoclass:: Injectable
   :show-inheritance:
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

.. autoclass:: Returns
   :show-inheritance:
   :members:

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

.. _api-rules:

Apply Rules
===========

See the tutorial section on :ref:`rules-intro` for more context about its
use cases and some examples.

.. autofunction:: web_poet.handle_urls

.. automodule:: web_poet.rules
   :members:
   :exclude-members: handle_urls

Fields
======

.. automodule:: web_poet.fields
    :members:

utils
=====

.. automodule:: web_poet.utils
    :members:
