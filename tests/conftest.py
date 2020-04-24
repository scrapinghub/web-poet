import os

import pytest

from core_po.page_inputs import HTMLResponse


def read_fixture(path):
    path = os.path.join(os.path.dirname(__file__), path)
    with open(path) as f:
        return f.read()


@pytest.fixture
def book_list_html():
    return read_fixture('fixtures/book_list.html')


@pytest.fixture
def book_list_html_response(book_list_html):
    return HTMLResponse('http://book.toscrape.com/', book_list_html)
