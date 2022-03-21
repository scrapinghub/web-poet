import json

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
    http_body = HttpResponseBody(b"contet")
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


def test_http_response_headers_init_requests():
    requests_response = requests.Response()
    requests_response.headers['User-Agent'] = "mozilla"

    response = HttpResponse("http://example.com", body=b"",
                            headers=requests_response.headers)
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
    http_body = HttpResponseBody(b'{"key": "value"}')
    response = HttpResponse("http://example.com", body=http_body)

    assert response.json() == {"key": "value"}


def test_http_response_encoding():
    """This tests a character which raises a UnicodeDecodeError when decoded in
    'ascii'.

    The backup series of encodings for decoding should be able to handle it.
    """
    text = "œ is a Weird Character"
    body = HttpResponseBody(b"\x9c is a Weird Character")
    response = HttpResponse("http://example.com", body)

    assert response.text == text
