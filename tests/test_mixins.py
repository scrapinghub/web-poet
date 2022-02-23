import json

import pytest

from web_poet.mixins import ResponseShortcutsMixin, JsonResponseShortcutsMixin
from web_poet.page_inputs import ResponseData


class MyPage(ResponseShortcutsMixin):
    def __init__(self, response: ResponseData):
        self.response = response


@pytest.fixture
def my_page(book_list_html_response):
    return MyPage(book_list_html_response)


class MyJsonPage(JsonResponseShortcutsMixin):
    def __init__(self, response: ResponseData):
        self.response = response


@pytest.fixture
def my_json_page(api_json_response):
    return MyJsonPage(api_json_response)


@pytest.fixture
def my_incorrect_json_page(book_list_html_response):
    return MyJsonPage(book_list_html_response)


def test_url(my_page):
    assert my_page.url == 'http://books.toscrape.com/index.html'


def test_html(my_page, book_list_html):
    assert my_page.html == book_list_html


def test_xpath(my_page):
    title = my_page.xpath('.//title/text()').get().strip()
    assert title == 'All products | Books to Scrape - Sandbox'


def test_css(my_page):
    title = my_page.css('title::text').get().strip()
    assert title == 'All products | Books to Scrape - Sandbox'


def test_baseurl(my_page):
    assert my_page.base_url == 'http://books.toscrape.com/index.html'


def test_urljoin(my_page):
    assert my_page.urljoin("foo") == 'http://books.toscrape.com/foo'


def test_custom_baseurl():
    html = """
    <html>
    <head>
        <base href="http://example.com/foo/">
    </head>
    <body><body>
    </html>
    """
    response = ResponseData(
        url="http://www.example.com/path",
        html=html,
    )
    page = MyPage(response=response)

    assert page.url == 'http://www.example.com/path'
    assert page.base_url == 'http://example.com/foo/'
    assert page.urljoin("bar") == 'http://example.com/foo/bar'
    assert page.urljoin("http://example.com/1") == "http://example.com/1"


def test_json(my_json_page):
    expected = {"status": "OK", "query": 123, "results": [{"name": "hello"}, {"name": "world"}]}
    assert my_json_page.json == expected
    assert my_json_page.json.get("status") == "OK"
    assert my_json_page.json.get("not existing") == None

def test_json_jmespath(my_json_page, my_incorrect_json_page):
    assert my_json_page.jmespath("status") == "OK"
    assert my_json_page.jmespath("results[].name") == ["hello", "world"]

    with pytest.raises(json.decoder.JSONDecodeError):
        my_incorrect_json_page.json
