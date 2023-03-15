.. _inputs:

======
Inputs
======

:ref:`Page object classes <page-object-classes>`, in their ``__init__`` method,
must define input parameters with type hints pointing to input classes.

Those input classes may be:

-   :ref:`Built-in web-poet input classes <built-in-inputs>`.

-   :ref:`Custom input classes <custom-inputs>`.

-   Other :ref:`page object classes <page-object-classes>`.

-   :ref:`Item classes <items>`, when using a :ref:`framework <frameworks>`
    that can provide item classes.

Based on the target URL and parameter type hints, :ref:`frameworks
<frameworks>` automatically build the required objects at run time, and pass
them to the ``__init__`` method of the corresponding page object class.

For example, if a page object class has an ``__init__`` parameter of type
:class:`~web_poet.page_inputs.HttpResponse`, and the target URL is
https://example.com, your framework would send an HTTP request to
https://example.com, download the response, build an
:class:`~web_poet.page_inputs.HttpResponse` object with the response data, and
pass it to the ``__init__`` method of the page object class being used.

.. _built-in-inputs:

Built-in input classes
======================

The :mod:`web_poet.page_inputs` module defines multiple classes that you can
define as inputs for a page object class, including:

-   :class:`~web_poet.page_inputs.HttpResponse`, a complete HTTP response,
    including URL, headers, and body. This is the most common input for a page
    object class.

-   :class:`~web_poet.page_inputs.HttpClient`, to send  :ref:`additional
    requests <additional-requests>`.

-   :class:`~web_poet.page_inputs.RequestUrl`, the target URL before following
    redirects. Useful, for example, to skip the target URL download, and
    instead use :class:`~web_poet.page_inputs.HttpClient` to send a custom
    request based on parts of the target URL.

-   :class:`~web_poet.page_inputs.PageParams`, to receive data from the
    crawling code.


.. _custom-inputs:

Custom input classes
====================

You may define your own input classes if you are using a :ref:`framework
<frameworks>` that supports it.

However, note that custom input classes may make your :ref:`page object classes
<page-object-classes>` less portable across frameworks.
