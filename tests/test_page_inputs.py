import codecs
import json

import aiohttp.web_response
import parsel
import pytest
import requests

from web_poet import BrowserResponse, RequestUrl, ResponseUrl
from web_poet.page_inputs import (
    AnyResponse,
    BrowserHtml,
    HttpRequest,
    HttpRequestBody,
    HttpRequestHeaders,
    HttpResponse,
    HttpResponseBody,
    HttpResponseHeaders,
    Stats,
)
from web_poet.page_inputs.http import request_fingerprint


@pytest.mark.parametrize("body_cls", [HttpRequestBody, HttpResponseBody])
def test_http_body_hashable(body_cls) -> None:
    http_body = body_cls(b"content")
    assert http_body in {http_body}
    assert http_body in {b"content"}
    assert http_body not in {b"foo"}


@pytest.mark.parametrize("body_cls", [HttpRequestBody, HttpResponseBody])
def test_http_body_bytes_api(body_cls) -> None:
    http_body = body_cls(b"content")
    assert http_body == b"content"
    assert b"ent" in http_body


@pytest.mark.parametrize("body_cls", [HttpRequestBody, HttpResponseBody])
def test_http_body_str_api(body_cls) -> None:
    with pytest.raises(TypeError):
        body_cls("string content")


def test_http_response_body_declared_encoding() -> None:
    http_body = HttpResponseBody(b"content")
    assert http_body.declared_encoding() is None

    http_body = HttpResponseBody(
        b"""
    <html><head>
    <meta charset="utf-8" />
    </head></html>
    """
    )
    assert http_body.declared_encoding() == "utf-8"


def test_http_response_body_json() -> None:
    http_body = HttpResponseBody(b"content")
    with pytest.raises(json.JSONDecodeError):
        http_body.json()

    http_body = HttpResponseBody(b'{"foo": 123}')
    assert http_body.json() == {"foo": 123}

    http_body = HttpResponseBody('{"ключ": "значение"}'.encode("utf8"))
    assert http_body.json() == {"ключ": "значение"}


@pytest.mark.parametrize(
    ["cls", "body_cls"],
    [
        (HttpRequest, HttpRequestBody),
        (HttpResponse, HttpResponseBody),
    ],
)
def test_http_defaults(cls, body_cls) -> None:
    http_body = body_cls(b"content")

    obj = cls("url", body=http_body)
    assert str(obj.url) == "url"
    assert obj.body == b"content"
    assert not obj.headers
    assert obj.headers.get("user-agent") is None

    if cls == HttpResponse:
        assert obj.status is None
    else:
        with pytest.raises(AttributeError):
            obj.status


@pytest.mark.parametrize(
    ["cls", "headers_cls"],
    [
        (HttpRequest, HttpRequestHeaders),
        (HttpResponse, HttpResponseHeaders),
    ],
)
def test_http_with_headers_alt_constructor(cls, headers_cls) -> None:
    headers = headers_cls.from_name_value_pairs(
        [{"name": "User-Agent", "value": "test agent"}]
    )
    obj = cls("url", body=b"", headers=headers)
    assert len(obj.headers) == 1
    assert obj.headers.get("user-agent") == "test agent"


@pytest.mark.parametrize(
    ["cls", "body_cls"],
    [
        (HttpRequest, HttpRequestBody),
        (HttpResponse, HttpResponseBody),
    ],
)
def test_http_response_bytes_body(cls, body_cls) -> None:
    obj = cls("http://example.com", body=b"content")
    assert isinstance(obj.body, body_cls)
    assert obj.body == body_cls(b"content")


@pytest.mark.parametrize("cls", [HttpRequest, HttpResponse])
def test_http_body_validation_str(cls) -> None:
    with pytest.raises(TypeError):
        cls("http://example.com", body="content")


@pytest.mark.parametrize("cls", [HttpRequest, HttpResponse])
def test_http_body_validation_None(cls) -> None:
    with pytest.raises(TypeError):
        cls("http://example.com", body=None)


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.parametrize("cls", [HttpRequest, HttpResponse])
def test_http_body_validation_other(cls) -> None:
    with pytest.raises(TypeError):
        cls("http://example.com", body=123)


@pytest.mark.parametrize("cls", [HttpRequest, HttpResponse])
def test_http_request_headers_init_invalid(cls) -> None:
    with pytest.raises(TypeError):
        cls("http://example.com", body=b"", headers=123)


@pytest.mark.parametrize("headers_cls", [HttpRequestHeaders, HttpResponseHeaders])
def test_http_response_headers(headers_cls) -> None:
    headers = headers_cls({"user-agent": "mozilla"})
    assert headers["user-agent"] == "mozilla"
    assert headers["User-Agent"] == "mozilla"

    with pytest.raises(KeyError):
        headers["user agent"]


@pytest.mark.parametrize(
    ["cls", "headers_cls"],
    [
        (HttpRequest, HttpRequestHeaders),
        (HttpResponse, HttpResponseHeaders),
    ],
)
def test_http_headers_init_dict(cls, headers_cls) -> None:
    obj = cls("http://example.com", body=b"", headers={"user-agent": "chrome"})
    assert isinstance(obj.headers, headers_cls)
    assert obj.headers["user-agent"] == "chrome"
    assert obj.headers["User-Agent"] == "chrome"


def test_http_request_init_minimal() -> None:
    req = HttpRequest("url")
    assert str(req.url) == "url"
    assert isinstance(req.url, RequestUrl)
    assert req.method == "GET"
    assert isinstance(req.method, str)
    assert not req.headers
    assert isinstance(req.headers, HttpRequestHeaders)
    assert not req.body
    assert isinstance(req.body, HttpRequestBody)


def test_http_request_init_full() -> None:
    req_1 = HttpRequest(
        "url", method="POST", headers={"User-Agent": "test agent"}, body=b"body"
    )
    assert req_1.method == "POST"
    assert isinstance(req_1.method, str)
    assert req_1.headers == {"User-Agent": "test agent"}
    assert req_1.headers.get("user-agent") == "test agent"
    assert isinstance(req_1.headers, HttpRequestHeaders)
    assert req_1.body == b"body"
    assert isinstance(req_1.body, HttpRequestBody)

    http_headers = HttpRequestHeaders({"User-Agent": "test agent"})
    http_body = HttpRequestBody(b"body")
    req_2 = HttpRequest("url", method="POST", headers=http_headers, body=http_body)

    assert str(req_1.url) == str(req_2.url)
    assert req_1.method == req_2.method
    assert req_1.headers == req_2.headers
    assert req_1.body == req_2.body


def test_http_request_init_with_response_url() -> None:
    resp = HttpResponse("url", b"")
    assert isinstance(resp.url, ResponseUrl)
    req = HttpRequest(resp.url)
    assert isinstance(req.url, RequestUrl)
    assert str(req.url) == str(resp.url)


@pytest.mark.parametrize(
    "cls",
    (
        HttpRequestHeaders,
        HttpResponseHeaders,
    ),
)
def test_http_headers_from_bytes_dict(cls) -> None:
    raw_headers = {
        b"Content-Length": [b"316"],
        b"Content-Encoding": [b"gzip", b"br"],
        b"server": b"sffe",
        "X-string": "string",
        "X-missing": None,
        "X-tuple": (b"x", "y"),
    }
    headers = cls.from_bytes_dict(raw_headers)

    assert headers.get("content-length") == "316"
    assert headers.get("content-encoding") == "gzip"
    assert headers.getall("Content-Encoding") == ["gzip", "br"]
    assert headers.get("server") == "sffe"
    assert headers.get("x-string") == "string"
    assert headers.get("x-missing") is None
    assert headers.get("x-tuple") == "x"
    assert headers.getall("x-tuple") == ["x", "y"]


@pytest.mark.parametrize(
    "cls",
    (
        HttpRequestHeaders,
        HttpResponseHeaders,
    ),
)
def test_http_response_headers_from_bytes_dict_err(cls) -> None:
    with pytest.raises(ValueError):
        cls.from_bytes_dict({b"Content-Length": [316]})

    with pytest.raises(ValueError):
        cls.from_bytes_dict({b"Content-Length": 316})


def test_http_response_headers_init_requests() -> None:
    requests_response = requests.Response()
    requests_response.headers["User-Agent"] = "mozilla"

    response = HttpResponse(
        "http://example.com", body=b"", headers=requests_response.headers
    )
    assert isinstance(response.headers, HttpResponseHeaders)
    assert response.headers["user-agent"] == "mozilla"
    assert response.headers["User-Agent"] == "mozilla"


def test_http_response_headers_init_aiohttp() -> None:
    aiohttp_response = aiohttp.web_response.Response()
    aiohttp_response.headers["User-Agent"] = "mozilla"

    response = HttpResponse(
        "http://example.com", body=b"", headers=aiohttp_response.headers
    )
    assert isinstance(response.headers, HttpResponseHeaders)
    assert response.headers["user-agent"] == "mozilla"
    assert response.headers["User-Agent"] == "mozilla"


def test_http_response_selectors(book_list_html_response) -> None:
    title = "All products | Books to Scrape - Sandbox"

    assert title == book_list_html_response.css("title ::text").get("").strip()
    assert title == book_list_html_response.xpath("//title/text()").get("").strip()


def test_http_response_json() -> None:
    url = "http://example.com"

    with pytest.raises(json.JSONDecodeError):
        response = HttpResponse(url, body=b"non json")
        response.json()

    response = HttpResponse(url, body=b'{"key": "value"}')
    assert response.json() == {"key": "value"}

    response = HttpResponse(url, body='{"ключ": "значение"}'.encode("utf8"))
    assert response.json() == {"ключ": "значение"}


def test_http_response_text() -> None:
    """This tests a character which raises a UnicodeDecodeError when decoded in
    'ascii'.

    The backup series of encodings for decoding should be able to handle it.
    """
    text = "œ is a Weird Character"
    body = HttpResponseBody(b"\x9c is a Weird Character")
    response = HttpResponse("http://example.com", body=body)

    assert response.text == text


@pytest.mark.parametrize(
    ["headers", "encoding"],
    [
        ({"Content-type": "text/html; charset=utf-8"}, "utf-8"),
        ({"Content-type": "text/html; charset=UTF8"}, "utf-8"),
        ({}, None),
        ({"Content-type": "text/html; charset=iso-8859-1"}, "cp1252"),
        ({"Content-type": "text/html; charset=None"}, None),
        ({"Content-type": "text/html; charset=gb2312"}, "gb18030"),
        ({"Content-type": "text/html; charset=gbk"}, "gb18030"),
        ({"Content-type": "text/html; charset=UNKNOWN"}, None),
    ],
)
def test_http_headers_declared_encoding(headers, encoding) -> None:
    headers = HttpResponseHeaders(headers)
    assert headers.declared_encoding() == encoding

    response = HttpResponse("http://example.com", body=b"", headers=headers)
    assert response.encoding == encoding or HttpResponse._DEFAULT_ENCODING


def test_http_response_utf16() -> None:
    """Test utf-16 because UnicodeDammit is known to have problems with"""
    r = HttpResponse(
        "http://www.example.com", body=b"\xff\xfeh\x00i\x00", encoding="utf-16"
    )
    assert r.text == "hi"
    assert r.encoding == "utf-16"


def test_explicit_encoding() -> None:
    response = HttpResponse(
        "http://www.example.com", "£".encode("utf-8"), encoding="utf-8"
    )
    assert response.encoding == "utf-8"
    assert response.text == "£"


def test_explicit_encoding_invalid() -> None:
    response = HttpResponse(
        "http://www.example.com", body="£".encode("utf-8"), encoding="latin1"
    )
    assert response.encoding == "latin1"
    assert response.text == "£".encode("utf-8").decode("latin1")


def test_utf8_body_detection() -> None:
    response = HttpResponse(
        "http://www.example.com",
        b"\xc2\xa3",
        headers={"Content-type": "text/html; charset=None"},
    )
    assert response.encoding == "utf-8"

    response = HttpResponse(
        "http://www.example.com",
        body=b"\xc2",
        headers={"Content-type": "text/html; charset=None"},
    )
    assert response.encoding != "utf-8"


def test_gb2312() -> None:
    response = HttpResponse(
        "http://www.example.com",
        body=b"\xa8D",
        headers={"Content-type": "text/html; charset=gb2312"},
    )
    assert response.text == "\u2015"


def test_bom_encoding() -> None:
    response = HttpResponse(
        "http://www.example.com",
        body=codecs.BOM_UTF8 + "🎉".encode("utf-8"),
        headers={"Content-type": "text/html; charset=cp1251"},
    )
    assert response.encoding == "utf-8"
    assert response.text == "🎉"


def test_bom_encoding_mismatch() -> None:
    text = "Привет"
    body = codecs.BOM + text.encode("utf-8")
    response = HttpResponse(
        url="http://example.com",
        headers={"Content-Type": "text/html; charset=cp1251"},
        body=body,
        status=200,
    )

    # The resulting text is different since BOM was the one that was followed.
    assert response.encoding == "utf-16-le"
    assert response.text != text
    assert response.text == "鿐胑룐닐뗐苑"


def test_invalid_utf8_encoded_body_with_valid_utf8_BOM() -> None:
    response = HttpResponse(
        "http://www.example.com",
        headers={"Content-type": "text/html; charset=utf-8"},
        body=b"\xef\xbb\xbfWORD\xe3\xab",
    )
    assert response.encoding == "utf-8"
    assert response.text == "WORD\ufffd"


def test_bom_is_removed_from_body() -> None:
    # Inferring encoding from body also cache decoded body as sideeffect,
    # this test tries to ensure that calling response.encoding and
    # response.text in indistint order doesn't affect final
    # values for encoding and decoded body.
    url = "http://example.com"
    body = b"\xef\xbb\xbfWORD"
    headers = {"Content-type": "text/html; charset=utf-8"}

    # Test response without content-type and BOM encoding
    response = HttpResponse(url, body=body)
    assert response.encoding == "utf-8"
    assert response.text == "WORD"
    response = HttpResponse(url, body=body)
    assert response.text == "WORD"
    assert response.encoding == "utf-8"

    # Body caching sideeffect isn't triggered when encoding is declared in
    # content-type header but BOM still need to be removed from decoded
    # body
    response = HttpResponse(url, headers=headers, body=body)
    assert response.encoding == "utf-8"
    assert response.text == "WORD"
    response = HttpResponse(url, headers=headers, body=body)
    assert response.text == "WORD"
    assert response.encoding == "utf-8"


def test_replace_wrong_encoding() -> None:
    """Test invalid chars are replaced properly"""
    r = HttpResponse(
        "http://www.example.com", encoding="utf-8", body=b"PREFIX\xe3\xabSUFFIX"
    )
    # XXX: Policy for replacing invalid chars may suffer minor variations
    # but it should always contain the unicode replacement char ('\ufffd')
    assert "\ufffd" in r.text, repr(r.text)
    assert "PREFIX" in r.text, repr(r.text)
    assert "SUFFIX" in r.text, repr(r.text)

    # Do not destroy html tags due to encoding bugs
    r = HttpResponse(
        "http://example.com", encoding="utf-8", body=b"\xf0<span>value</span>"
    )
    assert "<span>value</span>" in r.text, repr(r.text)


def test_html_encoding() -> None:
    body = b"""<html><head><title>Some page</title><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
    </head><body>Price: \xa3100</body></html>'
    """
    r1 = HttpResponse("http://www.example.com", body=body)
    assert r1.encoding == "cp1252"
    assert r1.text == body.decode("cp1252")

    body = b"""<?xml version="1.0" encoding="iso-8859-1"?>
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
    Price: \xa3100
    """
    r2 = HttpResponse("http://www.example.com", body=body)
    assert r2.encoding == "cp1252"
    assert r2.text == body.decode("cp1252")


def test_html_headers_encoding_precedence() -> None:
    # for conflicting declarations headers must take precedence
    body = b"""<html><head><title>Some page</title><meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    </head><body>Price: \xa3100</body></html>'
    """
    response = HttpResponse(
        "http://www.example.com",
        body=body,
        headers={"Content-type": "text/html; charset=iso-8859-1"},
    )
    assert response.encoding == "cp1252"
    assert response.text == body.decode("cp1252")


def test_html5_meta_charset() -> None:
    body = b"""<html><head><meta charset="gb2312" /><title>Some page</title><body>bla bla</body>"""
    response = HttpResponse("http://www.example.com", body=body)
    assert response.encoding == "gb18030"
    assert response.text == body.decode("gb18030")


def test_browser_html() -> None:
    src = "<html><body><p>Hello, </p><p>world!</p></body></html>"
    html = BrowserHtml(src)
    assert html == src
    assert html != "foo"

    assert html.xpath("//p/text()").getall() == ["Hello, ", "world!"]
    assert html.css("p::text").getall() == ["Hello, ", "world!"]
    assert isinstance(html.selector, parsel.Selector)


def test_browser_response() -> None:
    url = "http://example.com"
    html = "<html><body><p>Hello, </p><p>world!</p></body></html>"
    response = BrowserResponse(url=url, html=html, status=200)
    assert response.xpath("//p/text()").getall() == ["Hello, ", "world!"]
    assert response.css("p::text").getall() == ["Hello, ", "world!"]
    assert isinstance(response.selector, parsel.Selector)
    assert isinstance(response.html, BrowserHtml)
    assert str(response.urljoin("products")) == "http://example.com/products"
    assert response.selector.root.base_url == url


@pytest.mark.parametrize(
    ["cls"],
    [
        (HttpRequest,),
        (HttpResponse,),
    ],
)
def test_urljoin_absolute(cls) -> None:
    obj = cls("https://example.com", body=b"")
    new_url = obj.urljoin("https://toscrape.com/foo")
    assert isinstance(new_url, RequestUrl)
    assert str(new_url) == "https://toscrape.com/foo"


@pytest.mark.parametrize(
    ["cls"],
    [
        (HttpRequest,),
        (HttpResponse,),
    ],
)
def test_urljoin_relative(cls) -> None:
    obj = cls("https://example.com", body=b"")
    new_url = obj.urljoin("foo")
    assert isinstance(new_url, RequestUrl)
    assert str(new_url) == "https://example.com/foo"


def test_urljoin_relative_html_base() -> None:
    body = b"""
    <!DOCTYPE html>
    <html>
    <head>
    <base href="https://toscrape.com/">
    </head>
    <body></body>
    </html>
    """
    obj = HttpResponse("https://example.com", body=body)
    new_url = obj.urljoin("foo")
    assert isinstance(new_url, RequestUrl)
    assert str(new_url) == "https://toscrape.com/foo"


@pytest.mark.parametrize(
    ["cls"],
    [
        (RequestUrl,),
        (ResponseUrl,),
    ],
)
def test_urljoin_input_classes(cls) -> None:
    obj = HttpResponse("https://example.com", body=b"")
    new_url = obj.urljoin(cls("foo"))
    assert isinstance(new_url, RequestUrl)
    assert str(new_url) == "https://example.com/foo"


def test_requesturl_move() -> None:
    from web_poet.page_inputs.http import RequestUrl

    with pytest.warns(
        DeprecationWarning,
        match=(
            "web_poet.page_inputs.http.RequestUrl is deprecated, instantiate "
            "web_poet.page_inputs.url.RequestUrl instead."
        ),
    ):
        RequestUrl("https://example.com")


def test_responseurl_move() -> None:
    from web_poet.page_inputs.http import ResponseUrl

    with pytest.warns(
        DeprecationWarning,
        match=(
            "web_poet.page_inputs.http.ResponseUrl is deprecated, instantiate "
            "web_poet.page_inputs.url.ResponseUrl instead."
        ),
    ):
        ResponseUrl("https://example.com")


def test_request_fingerprint() -> None:
    req1 = HttpRequest(url="http://toscrape.com/1")
    req2 = HttpRequest(url="http://toscrape.com/1")
    assert request_fingerprint(req1) == request_fingerprint(req2)
    req3 = HttpRequest(url="http://toscrape.com/2")
    assert request_fingerprint(req1) != request_fingerprint(req3)

    req4 = HttpRequest(url="http://toscrape.com/1", method="POST")
    assert request_fingerprint(req1) != request_fingerprint(req4)

    req5 = HttpRequest(url="http://toscrape.com/1", body=b"")
    assert request_fingerprint(req1) == request_fingerprint(req5)
    req6 = HttpRequest(url="http://toscrape.com/1", body=b"foo")
    assert request_fingerprint(req1) != request_fingerprint(req6)

    req7 = HttpRequest(url="http://toscrape.com/1", headers={})
    assert request_fingerprint(req1) == request_fingerprint(req7)
    req8 = HttpRequest(url="http://toscrape.com/1", headers={"a": "b"})
    assert request_fingerprint(req1) != request_fingerprint(req8)
    req9 = HttpRequest(url="http://toscrape.com/1", headers={"A": "b"})
    assert request_fingerprint(req8) == request_fingerprint(req9)
    req10 = HttpRequest(url="http://toscrape.com/1", headers=[("a", "b"), ("a", "c")])
    assert request_fingerprint(req1) != request_fingerprint(req10)
    assert request_fingerprint(req8) != request_fingerprint(req10)


def test_stats() -> None:
    stats = Stats()
    stats.set("a", "1")
    stats.set("b", 2)
    stats.inc("b")
    stats.inc("b", 5)
    stats.inc("c")

    assert stats._stats._stats == {"a": "1", "b": 8, "c": 1}


def test_http_or_browser_response() -> None:
    url = "http://example.com"
    html = "<html><body><p>Hello, </p><p>world!</p></body></html>"

    browser_response = BrowserResponse(url=url, html=html)
    response_1 = AnyResponse(response=browser_response)
    assert isinstance(response_1.response, BrowserResponse)
    assert response_1.response == browser_response

    http_response = HttpResponse(url=url, body=html.encode())
    response_2 = AnyResponse(response=http_response)
    assert isinstance(response_2.response, HttpResponse)
    assert response_2.response == http_response

    for response in [response_1, response_2]:
        assert isinstance(response.url, ResponseUrl)
        assert str(response.url) == url
        assert response.text == html
        assert response.xpath("//p/text()").getall() == ["Hello, ", "world!"]
        assert response.css("p::text").getall() == ["Hello, ", "world!"]
        assert isinstance(response.selector, parsel.Selector)
        assert str(response.urljoin("products")) == "http://example.com/products"
        assert response.status is None
        assert response.selector.root.base_url == url

    response = AnyResponse(response=BrowserResponse(url=url, html=html, status=200))
    assert response.status == 200

    response = AnyResponse(
        response=HttpResponse(url=url, body=html.encode(), status=200)
    )
    assert response.status == 200
