import pytest

from web_poet.mixins import ResponseShortcutsMixin
from web_poet.page_inputs import ResponseData


class MyPage(ResponseShortcutsMixin):

    def __init__(self, response: ResponseData):
        self.response = response


@pytest.fixture
def my_page(book_list_html_response):

    return MyPage(book_list_html_response)


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
