from web_poet.page_inputs import ResponseData


def test_html_response():
    response = ResponseData("url", "content")
    assert response.url == "url"
    assert response.html == "content"
    assert response.status is None
    assert response.headers is None

    response = ResponseData("url", "content", 200, {"User-Agent": "test agent"})
    assert response.status == 200
    assert response.headers["User-Agent"] == "test agent"
