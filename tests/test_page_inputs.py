import json

import aiohttp.web_response
import pytest
import requests

from web_poet.page_inputs import HttpResponse, HttpResponseBody, HttpResponseHeaders


def test_http_response_body_hashable():
    http_body = HttpResponseBody(b"content")
    assert http_body in {http_body}
    assert http_body in {b"content"}
    assert http_body not in {b"foo"}


def test_http_response_body_bytes_api():
    http_body = HttpResponseBody(b"content")
    assert http_body == b"content"
    assert b"ent" in http_body


def test_http_response_body_declared_encoding():
    http_body = HttpResponseBody(b"content")
    assert http_body.declared_encoding() is None

    http_body = HttpResponseBody(b"""
    <html><head>
    <meta charset="utf-8" />
    </head></html>
    """)
    assert http_body.declared_encoding() == "utf-8"


def test_http_response_body_json():
    http_body = HttpResponseBody(b"content")
    with pytest.raises(json.JSONDecodeError):
        data = http_body.json()

    http_body = HttpResponseBody(b'{"foo": 123}')
    assert http_body.json() == {"foo": 123}

    http_body = HttpResponseBody('{"ключ": "значение"}'.encode("utf8"))
    assert http_body.json() == {"ключ": "значение"}


def test_http_response_defaults():
    http_body = HttpResponseBody(b"content")

    response = HttpResponse("url", body=http_body)
    assert response.url == "url"
    assert response.body == b"content"
    assert response.status is None
    assert not response.headers
    assert response.headers.get("user-agent") is None


def test_http_response_with_headers():
    http_body = HttpResponseBody(b"content")
    headers = HttpResponseHeaders.from_name_value_pairs([{"name": "User-Agent", "value": "test agent"}])
    response = HttpResponse("url", body=http_body, status=200, headers=headers)
    assert response.status == 200
    assert len(response.headers) == 1
    assert response.headers.get("user-agent") == "test agent"


def test_http_response_bytes_body():
    response = HttpResponse("http://example.com", body=b"content")
    assert isinstance(response.body, HttpResponseBody)
    assert response.body == HttpResponseBody(b"content")


def test_http_response_body_validation_str():
    with pytest.raises(TypeError):
        response = HttpResponse("http://example.com", body="content")


def test_http_response_body_validation_None():
    with pytest.raises(TypeError):
        response = HttpResponse("http://example.com", body=None)


@pytest.mark.xfail(reason="not implemented")
def test_http_response_body_validation_other():
    with pytest.raises(TypeError):
        response = HttpResponse("http://example.com", body=123)


def test_http_respose_headers():
    headers = HttpResponseHeaders({"user-agent": "mozilla"})
    assert headers['user-agent'] == "mozilla"
    assert headers['User-Agent'] == "mozilla"

    with pytest.raises(KeyError):
        headers["user agent"]


def test_http_response_headers_from_bytes():
    raw_headers = {
        b"Content-Length": [b"316"],
        b"Content-Encoding": [b"gzip", b"br"],
        b"server": b"sffe",
        "X-string": "string",
        "X-missing": None
    }
    headers = HttpResponseHeaders.from_bytes(raw_headers)

    assert headers.get("content-length") == "316"
    assert headers.get("content-encoding") == "gzip"
    assert headers.getall("Content-Encoding") == ["gzip", "br"]
    assert headers.get("server") == "sffe"
    assert headers.get("x-string") == "string"
    assert headers.get("X-missing") is None


def test_http_response_headers_init_requests():
    requests_response = requests.Response()
    requests_response.headers['User-Agent'] = "mozilla"

    response = HttpResponse("http://example.com", body=b"",
                            headers=requests_response.headers)
    assert isinstance(response.headers, HttpResponseHeaders)
    assert response.headers['user-agent'] == "mozilla"
    assert response.headers['User-Agent'] == "mozilla"


def test_http_response_headers_init_aiohttp():
    aiohttp_response = aiohttp.web_response.Response()
    aiohttp_response.headers['User-Agent'] = "mozilla"

    response = HttpResponse("http://example.com", body=b"",
                            headers=aiohttp_response.headers)
    assert isinstance(response.headers, HttpResponseHeaders)
    assert response.headers['user-agent'] == "mozilla"
    assert response.headers['User-Agent'] == "mozilla"


def test_http_response_headers_init_dict():
    response = HttpResponse("http://example.com", body=b"",
                            headers={"user-agent": "mozilla"})
    assert isinstance(response.headers, HttpResponseHeaders)
    assert response.headers['user-agent'] == "mozilla"
    assert response.headers['User-Agent'] == "mozilla"


def test_http_response_headers_init_invalid():
    with pytest.raises(TypeError):
        response = HttpResponse("http://example.com", body=b"",
                                headers=123)


def test_http_response_selectors(book_list_html_response):
    title = "All products | Books to Scrape - Sandbox"

    assert title == book_list_html_response.css("title ::text").get("").strip()
    assert title == book_list_html_response.xpath("//title/text()").get("").strip()


def test_http_response_json():
    url = "http://example.com"

    with pytest.raises(json.JSONDecodeError):
        response = HttpResponse(url, body=b'non json')
        response.json()

    response = HttpResponse(url, body=b'{"key": "value"}')
    assert response.json() == {"key": "value"}

    response = HttpResponse(url, '{"ключ": "значение"}'.encode("utf8"))
    assert response.json() == {"ключ": "значение"}


def test_http_response_text():
    """This tests a character which raises a UnicodeDecodeError when decoded in
    'ascii'.

    The backup series of encodings for decoding should be able to handle it.
    """
    text = "œ is a Weird Character"
    body = HttpResponseBody(b"\x9c is a Weird Character")
    response = HttpResponse("http://example.com", body)

    assert response.text == text


@pytest.mark.parametrize(["headers", "encoding"], [
    ({"Content-type": "text/html; charset=utf-8"}, "utf-8"),
    ({"Content-type": "text/html; charset=UTF8"}, "utf-8"),
    ({}, None),
    ({"Content-type": "text/html; charset=iso-8859-1"}, "cp1252"),
    ({"Content-type": "text/html; charset=None"}, None),
    ({"Content-type": "text/html; charset=gb2312"}, "gb18030"),
    ({"Content-type": "text/html; charset=gbk"}, "gb18030"),
    ({"Content-type": "text/html; charset=UNKNOWN"}, None),
])
def test_http_headers_declared_encoding(headers, encoding):
    headers = HttpResponseHeaders(headers)
    assert headers.declared_encoding() == encoding

    response = HttpResponse("http://example.com", b'', headers=headers)
    assert response.encoding == encoding or HttpResponse._DEFAULT_ENCODING


def test_http_response_utf16():
    """Test utf-16 because UnicodeDammit is known to have problems with"""
    r = HttpResponse("http://www.example.com",
                     body=b'\xff\xfeh\x00i\x00',
                     encoding='utf-16')
    assert r.text == "hi"
    assert r.encoding == "utf-16"


def test_explicit_encoding():
    response = HttpResponse("http://www.example.com", "£".encode('utf-8'),
                            encoding='utf-8')
    assert response.encoding == "utf-8"
    assert response.text == "£"


def test_explicit_encoding_invalid():
    response = HttpResponse("http://www.example.com", "£".encode('utf-8'),
                            encoding='latin1')
    assert response.encoding == "latin1"
    assert response.text == "£".encode('utf-8').decode("latin1")


def test_utf8_body_detection():
    response = HttpResponse("http://www.example.com", body=b"\xc2\xa3",
                            headers={"Content-type": "text/html; charset=None"})
    assert response.encoding == "utf-8"

    response = HttpResponse("http://www.example.com", body=b"\xc2",
                            headers={"Content-type": "text/html; charset=None"})
    assert response.encoding != "utf-8"


def test_gb2312():
    response = HttpResponse("http://www.example.com", body=b"\xa8D",
                            headers={"Content-type": "text/html; charset=gb2312"})
    assert response.text == "\u2015"


def test_invalid_utf8_encoded_body_with_valid_utf8_BOM():
    response = HttpResponse("http://www.example.com",
                            headers={"Content-type": "text/html; charset=utf-8"},
                            body=b"\xef\xbb\xbfWORD\xe3\xab")
    assert response.encoding == "utf-8"
    assert response.text == 'WORD\ufffd'


def test_bom_is_removed_from_body():
    # Inferring encoding from body also cache decoded body as sideeffect,
    # this test tries to ensure that calling response.encoding and
    # response.text in indistint order doesn't affect final
    # values for encoding and decoded body.
    url = 'http://example.com'
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


def test_replace_wrong_encoding():
    """Test invalid chars are replaced properly"""
    r = HttpResponse("http://www.example.com", encoding='utf-8',
                     body=b'PREFIX\xe3\xabSUFFIX')
    # XXX: Policy for replacing invalid chars may suffer minor variations
    # but it should always contain the unicode replacement char ('\ufffd')
    assert '\ufffd' in r.text, repr(r.text)
    assert 'PREFIX' in r.text, repr(r.text)
    assert 'SUFFIX' in r.text, repr(r.text)

    # Do not destroy html tags due to encoding bugs
    r = HttpResponse("http://example.com", encoding='utf-8',
                     body=b'\xf0<span>value</span>')
    assert '<span>value</span>' in r.text, repr(r.text)


def test_html_encoding():
    body = b"""<html><head><title>Some page</title><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
    </head><body>Price: \xa3100</body></html>'
    """
    r1 = HttpResponse("http://www.example.com", body=body)
    assert r1.encoding == 'cp1252'
    assert r1.text == body.decode('cp1252')

    body = b"""<?xml version="1.0" encoding="iso-8859-1"?>
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
    Price: \xa3100
    """
    r2 = HttpResponse("http://www.example.com", body=body)
    assert r2.encoding == 'cp1252'
    assert r2.text == body.decode('cp1252')


def test_html_headers_encoding_precedence():
    # for conflicting declarations headers must take precedence
    body = b"""<html><head><title>Some page</title><meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    </head><body>Price: \xa3100</body></html>'
    """
    response = HttpResponse("http://www.example.com", body=body,
                            headers={"Content-type": "text/html; charset=iso-8859-1"})
    assert response.encoding == 'cp1252'
    assert response.text == body.decode('cp1252')


def test_html5_meta_charset():
    body = b"""<html><head><meta charset="gb2312" /><title>Some page</title><body>bla bla</body>"""
    response = HttpResponse("http://www.example.com", body=body)
    assert response.encoding == 'gb18030'
    assert response.text == body.decode('gb18030')
