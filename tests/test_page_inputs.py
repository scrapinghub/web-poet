from web_poet.page_inputs import HttpResponse, HttpResponseBody, HttpResponseHeaders


def test_html_response():
    http_body = HttpResponseBody(b"content")

    response = HttpResponse("url", body=http_body)
    assert response.url == "url"
    assert response.body == b"content"
    assert response.status is None
    assert not response.headers
    assert response.headers.get("user-agent") is None

    headers = HttpResponseHeaders.from_name_value_pairs([{"name": "User-Agent", "value": "test agent"}])
    response = HttpResponse("url", body=http_body, status=200, headers=headers)
    assert response.status == 200
    assert len(response.headers) == 1
    assert response.headers.get("user-agent") == "test agent"
