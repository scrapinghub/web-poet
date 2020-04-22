from core_po.responses import HTMLResponse


def test_html_response():
    response = HTMLResponse('url', 'content')
    assert response.url == 'url'
    assert response.content == 'content'
