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

.. automodule:: web_poet.page_inputs.client
   :members:
   :undoc-members:

.. automodule:: web_poet.page_inputs.http
   :members:
   :undoc-members:
   :inherited-members: str,bytes,MultiDict
   :show-inheritance:

.. automodule:: web_poet.page_inputs.response
   :members:
   :undoc-members:
   :inherited-members: str
   :show-inheritance:

.. automodule:: web_poet.page_inputs.page_params
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: web_poet.page_inputs.stats
   :members:
   :show-inheritance:

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

.. autoclass:: BrowserPage
   :show-inheritance:
   :members:
   :undoc-members:
   :inherited-members:
   :no-special-members:

.. autoclass:: Returns
   :show-inheritance:
   :members:

.. autoclass:: Extractor
   :show-inheritance:
   :members:
   :no-special-members:

.. autoclass:: SelectorExtractor
   :show-inheritance:
   :members:
   :no-special-members:

Mixins
======

.. automodule:: web_poet.mixins

.. autoclass:: web_poet.mixins.ResponseShortcutsMixin
   :members:
   :inherited-members:
   :no-special-members:

.. autoclass:: web_poet.mixins.SelectableMixin
   :members:
   :inherited-members:
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

See :ref:`rules` for more context about its use cases and some examples.

.. data:: web_poet.default_registry

    Default :class:`~rules.RulesRegistry`.

.. function:: web_poet.handle_urls

    :meth:`~rules.RulesRegistry.handle_urls` of the :data:`default_registry`.

.. automodule:: web_poet.rules
   :members:

Fields
======

.. automodule:: web_poet.fields
    :members:

Annotation support
==================

.. autofunction:: web_poet.annotation_encode
.. autofunction:: web_poet.annotation_decode
.. autoclass:: web_poet.AnnotatedInstance

Utils
=====

.. automodule:: web_poet.utils
    :members:


Example framework
=================

The :mod:`web_poet.example` module is a simplified, incomplete example of a
web-poet framework, written as support material for the :ref:`tutorial
<tutorial>`.

No part of the :mod:`web_poet.example` module is intended for production use,
and it may change in a backward-incompatible way at any point in the future.

.. automodule:: web_poet.example
    :members:
