from __future__ import annotations

from pathlib import Path

import pytest

from web_poet.page_inputs import HttpResponse, HttpResponseBody

pytest_plugins = ["pytester"]


def read_fixture(path: str) -> str:
    return (Path(__file__).parent / path).read_text(encoding="utf-8")


@pytest.fixture
def book_list_html():
    return read_fixture("fixtures/book_list.html")


@pytest.fixture
def some_json_response():
    body = """
    {
      "description": "paragraph",
      "website": {
        "url": "http://www.scrapy.org",
        "name": "homepage"
      },
      "logo": "/images/logo.png"
    }
    """
    return HttpResponse(
        url="http://books.toscrape.com/result.json",
        body=body.encode("utf-8"),
        encoding="utf-8",
    )


@pytest.fixture
def book_list_html_response(book_list_html):
    body = HttpResponseBody(bytes(book_list_html, "utf-8"))
    return HttpResponse(
        url="http://books.toscrape.com/index.html", body=body, encoding="utf-8"
    )
