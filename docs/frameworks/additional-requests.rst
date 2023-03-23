.. _frameworks:
.. _framework-additional-requests:

==============================
Supporting Additional Requests
==============================

To support :ref:`additional requests <additional-requests>`, your framework must
provide the request download implementation of :class:`~.HttpClient`.

.. _advanced-downloader-impl:

Providing the Downloader
------------------------

On its own, :class:`~.HttpClient` doesn't do anything. It doesn't
know how to execute the request on its own. Thus, for frameworks or projects
wanting to use additional requests in Page Objects, they need to set the
implementation on how to execute an :class:`~.HttpRequest`.

For more info on this, kindly read the API Specifications for :class:`~.HttpClient`.

In any case, frameworks that wish to support **web-poet** could provide the
HTTP downloader implementation in two ways:

.. _setup-contextvars:

1. Context Variable
*******************

:mod:`contextvars` is natively supported in :mod:`asyncio` in order to set and
access context-aware values. This means that the framework using **web-poet**
can assign the request downloader implementation using the :mod:`contextvars`
instance named ``web_poet.request_downloader_var``.

This can be set using:

.. code-block:: python

    import attrs
    import web_poet
    from web_poet import validate_input

    async def request_implementation(req: web_poet.HttpRequest) -> web_poet.HttpResponse:
        ...


    def create_http_client():
        return web_poet.HttpClient()


    @attrs.define
    class SomePage(web_poet.WebPage):
        http: web_poet.HttpClient

        @validate_input
        async def to_item(self):
            ...

    # Once this is set, the ``request_implementation`` becomes available to
    # all instances of HttpClient, unless HttpClient is created with
    # the ``request_downloader`` argument (see the #2 Dependency Injection
    # example below).
    web_poet.request_downloader_var.set(request_implementation)

    # Assume that it's constructed with the necessary arguments taken somewhere.
    response = web_poet.HttpResponse(...)

    page = SomePage(response=response, http=create_http_client())
    item = await page.to_item()

When the ``web_poet.request_downloader_var`` contextvar is set,
:class:`~.HttpClient` instances use it by default.

.. warning::

    If no value for ``web_poet.request_downloader_var`` is set, then
    :class:`~.RequestDownloaderVarError` is raised. However, no exception is
    raised if **option 2** below is used.


2. Dependency Injection
***********************

The framework using **web-poet** may be using libraries that don't
have a full support to :mod:`contextvars` `(e.g. Twisted)`. With that, an
alternative approach would be to supply the request downloader implementation
when creating an :class:`~.HttpClient` instance:

.. code-block:: python

    import attrs
    import web_poet
    from web_poet import validate_input

    async def request_implementation(req: web_poet.HttpRequest) -> web_poet.HttpResponse:
        ...

    def create_http_client():
        return web_poet.HttpClient(request_downloader=request_implementation)


    @attrs.define
    class SomePage(web_poet.WebPage):
        http: web_poet.HttpClient

        @validate_input
        async def to_item(self):
            ...

    # Assume that it's constructed with the necessary arguments taken somewhere.
    response = web_poet.HttpResponse(...)

    page = SomePage(response=response, http=create_http_client())
    item = await page.to_item()

From the code sample above, we can see that every time an :class:`~.HttpClient`
instance is created for Page Objects needing it, the framework
must create :class:`~.HttpClient` with a framework-specific **request
downloader implementation**, using the ``request_downloader`` argument.

Downloader Behavior
-------------------

The request downloader MUST accept an instance of :class:`~.HttpRequest`
as the input and return an instance of :class:`~.HttpResponse`. This is important
in order to handle and represent generic HTTP operations. The only time that
it won't be returning :class:`~.HttpResponse` would be when it's raising exceptions
(see :ref:`framework-exception-handling`).

The request downloader MUST resolve Location-based **redirections** when the HTTP
method is not ``HEAD``. In other words, for non-``HEAD`` requests the
returned :class:`~.HttpResponse` must be the final response, after all redirects.
For ``HEAD`` requests redirects MUST NOT be resolved.

Lastly, the request downloader function MUST support the ``async/await``
syntax.

.. _framework-exception-handling:

Exception Handling
------------------

In the previous :ref:`exception-handling` section, we can see how Page Object
developers could use the exception classes built inside **web-poet** to handle
various ways additional requests MAY fail. In this section, we'll see the
rationale and ways the framework MUST be able to do that.

Rationale
*********

Frameworks that handle **web-poet** MUST be able to ensure that Page Objects
having additional requests using :class:`~.HttpClient` are able to work with
any type of HTTP downloader implementation.

For example, in Python, the common HTTP libraries have different types of base
exceptions when something has occurred:

    * `aiohttp.ClientError <https://docs.aiohttp.org/en/v3.8.1/client_reference.html?highlight=exceptions#aiohttp.ClientError>`_
    * `requests.RequestException <https://2.python-requests.org/en/master/api/#requests.RequestException>`_
    * `urllib.error.HTTPError <https://docs.python.org/3/library/urllib.error.html#urllib.error.HTTPError>`_

Imagine if Page Objects are **expected** to work in `different` backend implementations
like the ones above, then it would cause the code to look like:

.. code-block:: python

    import urllib

    import aiohttp
    import attrs
    import requests
    import web_poet
    from web_poet import validate_input


    @attrs.define
    class SomePage(web_poet.WebPage):
        http: web_poet.HttpClient

        @validate_input
        async def to_item(self):
            try:
                response = await self.http.get("...")
            except (aiohttp.ClientError, requests.RequestException, urllib.error.HTTPError):
                # handle the error here

Such code could turn messy in no time especially when the number of HTTP backends
that Page Objects have to support are steadily increasing. Not to mention the
plethora of exception types that HTTP libraries have. This means that Page
Objects aren't truly portable in different types of frameworks or environments.
Rather, they're only limited to work in the specific framework they're supported.

In order for Page Objects to work in different Downloader Implementations,
the framework that implements the HTTP Downloader backend MUST raise
exceptions from the :mod:`web_poet.exceptions.http` module in lieu of the backend
specific ones `(e.g. aiohttp, requests, urllib, etc.)`.

This makes the code simpler:

.. code-block:: python

    import attrs
    import web_poet
    from web_poet import validate_input


    @attrs.define
    class SomePage(web_poet.WebPage):
        http: web_poet.HttpClient

        @validate_input
        async def to_item(self):
            try:
                response = await self.http.get("...")
            except web_poet.exceptions.HttpError:
                # handle the error here

Expected behavior for Exceptions
********************************

All exceptions that the HTTP Downloader Implementation (see :ref:`advanced-downloader-impl`
doc section) explicitly raises when implementing it for **web-poet** MUST be
:class:`web_poet.exceptions.http.HttpError` *(or a subclass from it)*.

For frameworks that implement and use **web-poet**, exceptions that occurred when
handling the additional requests like `connection errors`, `TLS errors`, etc MUST
be replaced by :class:`web_poet.exceptions.http.HttpRequestError` by raising it
explicitly.

For responses that are not really errors like in the ``100-3xx`` status code range,
exception MUST NOT be raised at all. For responses with status codes in
the ``400-5xx`` range, **web-poet** raises the :class:`web_poet.exceptions.http.HttpResponseError`
exception.

From this distinction, the framework MUST NOT raise :class:`web_poet.exceptions.http.HttpResponseError`
on its own at all, since the :class:`~.HttpClient` already handles that.
