from web_poet.page_inputs import ResponseData, HttpResponseBody, HttpResponseHeaders


def test_html_response():
    body = HttpResponseBody(raw="content", html="content")
    headers = HttpResponseHeaders([{"User-Agent": "test agent"}])

    response = ResponseData("url", body)
    assert response.url == "url"
    assert response.body.html == "content"
    assert response.status is None
    assert response.headers is None

    response = ResponseData("url", body, 200, headers)
    assert response.status == 200
    assert len(response.headers.data) == 1
    assert response.headers.data[0] == {"User-Agent": "test agent"}
