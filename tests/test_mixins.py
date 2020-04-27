import pytest

from web_poet.mixins import ResponseShortcutsMixin
from web_poet.page_inputs import ResponseData


class MyClass(ResponseShortcutsMixin):

    def __init__(self, response: ResponseData):
        self.response = response


@pytest.fixture
def my_instance(book_list_html_response):

    return MyClass(book_list_html_response)


def test_url(my_instance):
    assert my_instance.url == 'http://book.toscrape.com/'


def test_html(my_instance, book_list_html):
    assert my_instance.html == book_list_html


def test_xpath(my_instance):
    title = my_instance.xpath('.//title/text()').get().strip()
    assert title == 'All products | Books to Scrape - Sandbox'


def test_css(my_instance):
    title = my_instance.css('title::text').get().strip()
    assert title == 'All products | Books to Scrape - Sandbox'
