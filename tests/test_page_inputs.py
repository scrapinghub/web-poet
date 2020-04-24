from core_po.page_inputs import ResponseData


def test_html_response():
    response = ResponseData('url', 'content')
    assert response.url == 'url'
    assert response.html == 'content'
