import pytest
import asyncio

from web_poet.page_inputs import ResponseData, Meta, HttpResponseBody, HttpResponseHeaders


def test_html_response():
    html = "content"
    http_body = HttpResponseBody(b"content")

    response = ResponseData("url", html, body=http_body)
    assert response.url == "url"
    assert response.body == b"content"
    assert response.status is None
    assert response.headers is None

    headers = HttpResponseHeaders.from_name_value_pairs([{"name": "User-Agent", "value": "test agent"}])
    response = ResponseData("url", html, status=200, headers=headers)
    assert response.status == 200
    assert len(response.headers) == 1
    assert response.headers.get("user-agent") == "test agent"


def test_meta_restriction():
    # Any value that conforms with `Meta.restrictions` raises an error
    with pytest.raises(ValueError) as err:
        Meta(func=lambda x: x + 1)

    with pytest.raises(ValueError) as err:
        Meta(class_=ResponseData)

    # These are allowed though
    m = Meta(x="hi", y=2.2, z={"k": "v"})
    m["allowed"] = [1, 2, 3]

    with pytest.raises(ValueError) as err:
        m["not_allowed"] = asyncio.sleep(1)
