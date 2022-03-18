import json

import pytest

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

