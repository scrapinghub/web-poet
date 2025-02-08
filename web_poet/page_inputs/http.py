from __future__ import annotations

import json
from hashlib import sha1
from typing import Any
from urllib.parse import urljoin

import attrs
from w3lib.encoding import (
    html_body_declared_encoding,
    html_to_unicode,
    http_content_type_encoding,
    read_bom,
    resolve_encoding,
)
from w3lib.url import canonicalize_url

from web_poet._base import _HttpHeaders
from web_poet.mixins import SelectableMixin, UrlShortcutsMixin
from web_poet.utils import memoizemethod_noargs

from .url import RequestUrl as _RequestUrl
from .url import ResponseUrl as _ResponseUrl


class HttpRequestBody(bytes):
    """A container for holding the raw HTTP request body in bytes format."""


class HttpResponseBody(bytes):
    """A container for holding the raw HTTP response body in bytes format."""

    def bom_encoding(self) -> str | None:
        """Returns the encoding from the byte order mark if present."""
        return read_bom(self)[0]

    def declared_encoding(self) -> str | None:
        """Return the encoding specified in meta tags in the html body,
        or ``None`` if no suitable encoding was found"""
        return html_body_declared_encoding(self)

    def json(self) -> Any:
        """
        Deserialize a JSON document to a Python object.
        """
        return json.loads(self)


class HttpRequestHeaders(_HttpHeaders):
    """A container for holding the HTTP request headers.

    It's able to accept instantiation via an Iterable of Tuples:

    >>> pairs = [("Content-Encoding", "gzip"), ("content-length", "648")]
    >>> HttpRequestHeaders(pairs)
    <HttpRequestHeaders('Content-Encoding': 'gzip', 'content-length': '648')>

    It's also accepts a mapping of key-value pairs as well:

    >>> pairs = {"Content-Encoding": "gzip", "content-length": "648"}
    >>> headers = HttpRequestHeaders(pairs)
    >>> headers
    <HttpRequestHeaders('Content-Encoding': 'gzip', 'content-length': '648')>

    Note that this also supports case insensitive header-key lookups:

    >>> headers.get("content-encoding")
    'gzip'
    >>> headers.get("Content-Length")
    '648'

    These are just a few of the functionalities it inherits from
    :class:`multidict.CIMultiDict`. For more info on its other features, read
    the API spec of :class:`multidict.CIMultiDict`.
    """


class HttpResponseHeaders(_HttpHeaders):
    """A container for holding the HTTP response headers.

    It's able to accept instantiation via an Iterable of Tuples:

    >>> pairs = [("Content-Encoding", "gzip"), ("content-length", "648")]
    >>> HttpResponseHeaders(pairs)
    <HttpResponseHeaders('Content-Encoding': 'gzip', 'content-length': '648')>

    It's also accepts a mapping of key-value pairs as well:

    >>> pairs = {"Content-Encoding": "gzip", "content-length": "648"}
    >>> headers = HttpResponseHeaders(pairs)
    >>> headers
    <HttpResponseHeaders('Content-Encoding': 'gzip', 'content-length': '648')>

    Note that this also supports case insensitive header-key lookups:

    >>> headers.get("content-encoding")
    'gzip'
    >>> headers.get("Content-Length")
    '648'

    These are just a few of the functionalities it inherits from
    :class:`multidict.CIMultiDict`. For more info on its other features, read
    the API spec of :class:`multidict.CIMultiDict`.
    """

    def declared_encoding(self) -> str | None:
        """Return encoding detected from the Content-Type header, or None
        if encoding is not found"""
        content_type = self.get("Content-Type", "")
        return http_content_type_encoding(content_type)


@attrs.define(auto_attribs=False, slots=False, eq=False)
class HttpRequest:
    """Represents a generic HTTP request used by other functionalities in
    **web-poet** like :class:`~.HttpClient`.

    .. tip:: To build a request to submit an HTML form, use the
        :doc:`form2request library <form2request:index>`, which provides
        integration with web-poet.
    """

    url: _RequestUrl = attrs.field(converter=_RequestUrl)
    method: str = attrs.field(default="GET", kw_only=True)
    headers: HttpRequestHeaders = attrs.field(
        factory=HttpRequestHeaders, converter=HttpRequestHeaders, kw_only=True
    )
    body: HttpRequestBody = attrs.field(
        factory=HttpRequestBody, converter=HttpRequestBody, kw_only=True
    )

    def urljoin(self, url: str | _RequestUrl | _ResponseUrl) -> _RequestUrl:
        """Return *url* as an absolute URL.

        If *url* is relative, it is made absolute relative to :attr:`url`."""
        return _RequestUrl(urljoin(str(self.url), str(url)))


@attrs.define(auto_attribs=False, slots=False, eq=False)
class HttpResponse(SelectableMixin, UrlShortcutsMixin):
    """A container for the contents of a response, downloaded directly using an
    HTTP client.

    ``url`` should be a URL of the response (after all redirects),
    not a URL of the request, if possible.

    ``body`` contains the raw HTTP response body.

    The following are optional since it would depend on the source of the
    ``HttpResponse`` if these are available or not. For example, the responses
    could simply come off from a local HTML file which doesn't contain ``headers``
    and ``status``.

    ``status`` should represent the int status code of the HTTP response.

    ``headers`` should contain the HTTP response headers.

    ``encoding`` encoding of the response. If None (default), encoding
    is auto-detected from headers and body content.
    """

    url: _ResponseUrl = attrs.field(converter=_ResponseUrl)
    body: HttpResponseBody = attrs.field(converter=HttpResponseBody)
    status: int | None = attrs.field(default=None, kw_only=True)
    headers: HttpResponseHeaders = attrs.field(
        factory=HttpResponseHeaders, converter=HttpResponseHeaders, kw_only=True
    )
    _encoding: str | None = attrs.field(default=None, kw_only=True)

    _DEFAULT_ENCODING = "ascii"
    _cached_text: str | None = None

    @property
    def text(self) -> str:
        """
        Content of the HTTP body, converted to unicode
        using the detected encoding of the response, according
        to the web browser rules (respecting Content-Type header, etc.)
        """
        # Access self.encoding before self._cached_text, because
        # there is a chance self._cached_text would be already populated
        # while detecting the encoding
        encoding = self.encoding
        if self._cached_text is None:
            fake_content_type_header = f"charset={encoding}"
            encoding, text = html_to_unicode(fake_content_type_header, self.body)
            self._cached_text = text
        return self._cached_text

    def _selector_input(self) -> str:
        return self.text

    @property
    def encoding(self) -> str | None:
        """Encoding of the response"""
        return (
            self._encoding
            or self._body_bom_encoding()
            or self._headers_declared_encoding()
            or self._body_declared_encoding()
            or self._body_inferred_encoding()
        )

    @memoizemethod_noargs
    def json(self) -> Any:
        """Deserialize a JSON document to a Python object."""
        return self.body.json()

    @memoizemethod_noargs
    def _body_bom_encoding(self) -> str | None:
        return self.body.bom_encoding()

    @memoizemethod_noargs
    def _headers_declared_encoding(self) -> str | None:
        return self.headers.declared_encoding()

    @memoizemethod_noargs
    def _body_declared_encoding(self) -> str | None:
        return self.body.declared_encoding()

    @memoizemethod_noargs
    def _body_inferred_encoding(self) -> str | None:
        content_type = self.headers.get("Content-Type", "")
        body_encoding, text = html_to_unicode(
            content_type,
            self.body,
            auto_detect_fun=self._auto_detect_fun,
            default_encoding=self._DEFAULT_ENCODING,
        )
        self._cached_text = text
        return body_encoding

    def _auto_detect_fun(self, body: bytes) -> str | None:
        for enc in (self._DEFAULT_ENCODING, "utf-8", "cp1252"):
            try:
                body.decode(enc)
            except UnicodeError:
                continue
            return resolve_encoding(enc)
        return None


def request_fingerprint(req: HttpRequest) -> str:
    """Return the fingerprint of the request."""
    fp = sha1()  # noqa: S324
    fp.update(req.method.encode() + b"\n")
    fp.update(canonicalize_url(str(req.url)).encode() + b"\n")
    for name, value in sorted(req.headers.items()):
        fp.update(f"{name.title()}:{value}\n".encode())
    fp.update(b"\n")
    fp.update(req.body)
    return fp.hexdigest()
