import os

import pytest

from web_poet.page_inputs import ResponseData


def read_fixture(path):
    path = os.path.join(os.path.dirname(__file__), path)
    with open(path) as f:
        return f.read()


@pytest.fixture
def book_list_html():
    return read_fixture('fixtures/book_list.html')


@pytest.fixture
def book_list_html_response(book_list_html):
    return ResponseData('http://books.toscrape.com/index.html', book_list_html)
