import pytest

from core_po.pages import ItemPage, ItemWebPage


def test_abstract_page_object():
    with pytest.raises(TypeError) as exc:
        ItemPage()

    msg = ("Can't instantiate abstract class ItemPage "
           "with abstract methods to_item")
    assert str(exc.value) == msg


def test_abstract_web_page_object():
    with pytest.raises(TypeError) as exc:
        ItemWebPage()

    msg = ("Can't instantiate abstract class ItemWebPage "
           "with abstract methods to_item")
    assert str(exc.value) == msg


def test_page_object():

    class MyItemPage(ItemPage):

        def to_item(self) -> dict:
            return {
                'foo': 'bar',
            }

    page_object = MyItemPage()
    assert page_object.to_item() == {'foo': 'bar', }


def test_web_page_object(book_list_html_response):

    class MyWebPage(ItemWebPage):

        def to_item(self) -> dict:
            return {
                'url': self.url,
                'title': self.css('title::text').get().strip(),
            }

    page_object = MyWebPage(book_list_html_response)
    assert page_object.to_item() == {
        'url': 'http://book.toscrape.com/',
        'title': 'All products | Books to Scrape - Sandbox',
    }
