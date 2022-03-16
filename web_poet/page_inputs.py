import json
from typing import Optional, Dict, List

import attrs
from multidict import CIMultiDict
import parsel
from w3lib.encoding import (
    html_to_unicode,
    html_body_declared_encoding,
    resolve_encoding,
    http_content_type_encoding
)

from .utils import memoizemethod_noargs


class HttpResponseBody(bytes):
    """A container for holding the raw HTTP response body in bytes format."""

    @memoizemethod_noargs
    def declared_encoding(self) -> Optional[str]:
        """ Return the encoding specified in meta tags in the html body,
        or ``None`` if no suitable encoding was found """
        return html_body_declared_encoding(self)

    @memoizemethod_noargs
    def json(self):
        """
        Deserialize a JSON document to a Python object.
        """
        return json.loads(self)


class HttpResponseHeaders(CIMultiDict):
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

    @classmethod
    def from_name_value_pairs(cls, arg: List[Dict]):
        """An alternative constructor for instantiation using a ``List[Dict]``
        where the 'key' is the header name while the 'value' is the header value.

        >>> pairs = [
        ...     {"name": "Content-Encoding", "value": "gzip"},
        ...     {"name": "content-length", "value": "648"}
        ... ]
        >>> headers = HttpResponseHeaders.from_name_value_pairs(pairs)
        >>> headers
        <HttpResponseHeaders('Content-Encoding': 'gzip', 'content-length': '648')>
        """
        return cls([(pair["name"], pair["value"]) for pair in arg])

    def declared_encoding(self) -> Optional[str]:
        """ Return encoding detected from the Content-Type header, or None
        if encoding is not found """
        content_type = self.get('Content-Type', '')
        return http_content_type_encoding(content_type)


@attrs.define(auto_attribs=False)
class HttpResponse:
    """A container for the contents of a response, downloaded directly using an
    HTTP client.

    ``url`` should be a URL of the response (after all redirects),
    not a URL of the request, if possible.

    ``body`` contains the raw HTTP response body.

    The following are optional since it would depend on the source of the
    ``ResponseData`` if these are available or not. For example, the responses
    could simply come off from a local HTML file which doesn't contain ``headers``
    and ``status``.

    ``status`` should represent the int status code of the HTTP response.

    ``headers`` should contain the HTTP response headers.

    ``encoding`` encoding of the response. If None (default), encoding
    is auto-detected from headers and body content.
    """

    url: str = attrs.field()
    # FIXME: raise an error or handle the case when str is passed as body
    body: HttpResponseBody = attrs.field(converter=HttpResponseBody)
    status: Optional[int] = attrs.field(default=None)
    headers: Optional[HttpResponseHeaders] = attrs.field(default=None)
    _encoding: Optional[str] = attrs.field(default=None)

    _DEFAULT_ENCODING = 'ascii'
    _cached_text: Optional[str] = None

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
            fake_content_type_header = f'charset={encoding}'
            encoding, text = html_to_unicode(fake_content_type_header, self.body)
            self._cached_text = text
        return self._cached_text

    @property
    def encoding(self):
        """ Encoding of the response """
        return (
            self._encoding
            or self._headers_declared_encoding()
            or self._body_declared_encoding()
            or self._body_inferred_encoding()
        )

    @property
    @memoizemethod_noargs
    def selector(self) -> parsel.Selector:
        # XXX: should we pass base_url=self.url, as Scrapy does?
        return parsel.Selector(text=self.text)

    def xpath(self, query, **kwargs):
        return self.selector.xpath(query, **kwargs)

    def css(self, query):
        return self.selector.css(query)

    def json(self):
        return self.body.json()

    @memoizemethod_noargs
    def _headers_declared_encoding(self):
        if self.headers:
            return self.headers.declared_encoding()

    @memoizemethod_noargs
    def _body_declared_encoding(self):
        return self.body.declared_encoding()

    @memoizemethod_noargs
    def _body_inferred_encoding(self):
        content_type = (self.headers or {}).get('Content-Type', '')
        body_encoding, text = html_to_unicode(
            content_type,
            self.body,
            auto_detect_fun=self._auto_detect_fun,
            default_encoding=self._DEFAULT_ENCODING
        )
        self._cached_text = text
        return body_encoding

    def _auto_detect_fun(self, text):
        for enc in (self._DEFAULT_ENCODING, 'utf-8', 'cp1252'):
            try:
                text.decode(enc)
            except UnicodeError:
                continue
            return resolve_encoding(enc)
