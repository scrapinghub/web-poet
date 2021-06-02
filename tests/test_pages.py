import pytest

from web_poet.pages import ItemPage, ItemWebPage, is_injectable


def test_abstract_page_object():
    with pytest.raises(TypeError) as exc:
        ItemPage()
    assert "Can't instantiate abstract class" in str(exc.value)


def test_abstract_web_page_object():
    with pytest.raises(TypeError) as exc:
        ItemWebPage()
    assert "Can't instantiate abstract class" in str(exc.value)

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
        'url': 'http://books.toscrape.com/index.html',
        'title': 'All products | Books to Scrape - Sandbox',
    }


def test_is_injectable():

    class MyClass:
        pass

    class MyItemPage(ItemPage):

        def to_item(self) -> dict:
            return {
                'foo': 'bar',
            }

    assert is_injectable(None) is False
    assert is_injectable(MyClass) is False
    assert is_injectable(MyClass()) is False
    assert is_injectable(MyItemPage) is True
    assert is_injectable(MyItemPage()) is False
    assert is_injectable(ItemPage) is True
    assert is_injectable(ItemWebPage) is True
