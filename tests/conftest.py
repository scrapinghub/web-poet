import os

import pytest


def read_fixture(path):
    path = os.path.join(os.path.dirname(__file__), path)
    with open(path) as f:
        return f.read()


@pytest.fixture
def book_list():
    return read_fixture('fixtures/books_list.html')
