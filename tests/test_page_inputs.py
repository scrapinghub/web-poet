from web_poet.page_inputs import ResponseData, HttpResponseBody, HttpResponseHeaders


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
