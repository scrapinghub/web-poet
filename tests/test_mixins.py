import parsel
import pytest
from packaging import version

from web_poet.mixins import ResponseShortcutsMixin
from web_poet.page_inputs import HttpResponse

PARSEL_VERSION = version.parse(getattr(parsel, "__version__", "0.0"))
PARSEL_18_PLUS = PARSEL_VERSION >= version.parse("1.8.0")  # noqa: SIM300


class MyPage(ResponseShortcutsMixin):
    def __init__(self, response: HttpResponse):
        self.response = response


@pytest.fixture
def my_page(book_list_html_response):
    return MyPage(book_list_html_response)


@pytest.fixture
def my_json_page(some_json_response):
    return MyPage(some_json_response)


def test_url(my_page) -> None:
    assert my_page.url == "http://books.toscrape.com/index.html"


def test_html(my_page, book_list_html) -> None:
    assert my_page.html == book_list_html


def test_xpath(my_page) -> None:
    title = my_page.xpath(".//title/text()").get().strip()
    assert title == "All products | Books to Scrape - Sandbox"


@pytest.mark.skipif(not PARSEL_18_PLUS, reason="parsel < 1.8 doesn't support jmespath")
def test_jmespath(my_json_page) -> None:
    for obj in [my_json_page, my_json_page.response]:
        name = obj.jmespath("website.name").get()
        assert name == "homepage"


@pytest.mark.skipif(PARSEL_18_PLUS, reason="parsel >= 1.8 supports jmespath")
def test_jmespath_not_available(my_json_page) -> None:
    for obj in [my_json_page, my_json_page.response]:
        with pytest.raises(AttributeError):
            obj.jmespath("website.name").get()


def test_css(my_page) -> None:
    title = my_page.css("title::text").get().strip()
    assert title == "All products | Books to Scrape - Sandbox"


def test_baseurl(my_page) -> None:
    assert my_page.base_url == "http://books.toscrape.com/index.html"


def test_urljoin(my_page) -> None:
    assert my_page.urljoin("foo") == "http://books.toscrape.com/foo"


def test_custom_baseurl() -> None:
    body = b"""
    <html>
    <head>
        <base href="http://example.com/foo/">
    </head>
    <body><body>
    </html>
    """
    response = HttpResponse(
        url="http://www.example.com/path",
        body=body,
    )
    page = MyPage(response=response)

    assert page.url == "http://www.example.com/path"
    assert page.base_url == "http://example.com/foo/"
    assert page.urljoin("bar") == "http://example.com/foo/bar"
    assert page.urljoin("http://example.com/1") == "http://example.com/1"
