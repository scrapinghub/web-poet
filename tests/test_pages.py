import pytest

from core_po.pages import ItemPage, ItemWebPage


def test_abstract_page_object():
    with pytest.raises(TypeError) as exc:
        ItemPage()

    msg = ("Can't instantiate abstract class ItemPage "
           "with abstract methods serialize")
    assert str(exc.value) == msg


def test_abstract_web_page_object():
    with pytest.raises(TypeError) as exc:
        ItemWebPage()

    msg = ("Can't instantiate abstract class ItemWebPage "
           "with abstract methods serialize")
    assert str(exc.value) == msg


def test_page_object():

    class MyItemPage(ItemPage):

        def serialize(self) -> dict:
            return {
                'foo': 'bar',
            }

    page_object = MyItemPage()
    assert page_object.serialize() == {'foo': 'bar', }


def test_web_page_object(book_list_html_response):

    class MyWebPage(ItemWebPage):

        def serialize(self) -> dict:
            return {
                'url': self.url,
                'title': self.css('title::text').get().strip(),
            }

    page_object = MyWebPage(book_list_html_response)
    assert page_object.serialize() == {
        'url': 'http://book.toscrape.com/',
        'title': 'All products | Books to Scrape - Sandbox',
    }
