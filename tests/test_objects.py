import pytest

from core_po.objects import PageObject, WebPageObject


def test_abstract_page_object():
    with pytest.raises(TypeError) as exc:
        PageObject()

    msg = ("Can't instantiate abstract class PageObject "
           "with abstract methods serialize")
    assert str(exc.value) == msg


def test_abstract_web_page_object():
    with pytest.raises(TypeError) as exc:
        WebPageObject()

    msg = ("Can't instantiate abstract class WebPageObject "
           "with abstract methods serialize")
    assert str(exc.value) == msg


def test_page_object():

    class MyPageObject(PageObject):

        def serialize(self) -> dict:
            return {
                'foo': 'bar',
            }

    page_object = MyPageObject()
    assert page_object.serialize() == {'foo': 'bar', }


def test_web_page_object(book_list_html_response):

    class MyWebPageObject(WebPageObject):

        def serialize(self) -> dict:
            return {
                'url': self.url,
                'title': self.css('title::text').get().strip(),
            }

    page_object = MyWebPageObject(book_list_html_response)
    assert page_object.serialize() == {
        'url': 'http://book.toscrape.com/',
        'title': 'All products | Books to Scrape - Sandbox',
    }
