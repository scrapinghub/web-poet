from core_po.page_inputs import HTMLResponse


def test_html_response():
    response = HTMLResponse('url', 'content')
    assert response.url == 'url'
    assert response.content == 'content'
