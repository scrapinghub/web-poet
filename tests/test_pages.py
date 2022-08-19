import attrs
import pytest

from web_poet import field
from web_poet.pages import (
    Injectable,
    ItemPage,
    ItemT,
    ItemWebPage,
    Returns,
    is_injectable,
)


@attrs.define
class Item:
    name: str


def test_page_object():
    class MyItemPage(Injectable):
        def to_item(self) -> dict:
            return {
                "foo": "bar",
            }

    page_object = MyItemPage()
    assert page_object.to_item() == {
        "foo": "bar",
    }


def test_web_page_object(book_list_html_response):
    class MyWebPage(ItemWebPage):
        def to_item(self) -> dict:  # type: ignore
            return {
                "url": self.url,
                "title": self.css("title::text").get().strip(),
            }

    page_object = MyWebPage(book_list_html_response)
    assert page_object.to_item() == {
        "url": "http://books.toscrape.com/index.html",
        "title": "All products | Books to Scrape - Sandbox",
    }


def test_is_injectable():
    class MyClass:
        pass

    class MyItemPage(ItemPage):
        def to_item(self) -> dict:  # type: ignore
            return {
                "foo": "bar",
            }

    assert is_injectable(None) is False
    assert is_injectable(MyClass) is False
    assert is_injectable(MyClass()) is False
    assert is_injectable(MyItemPage) is True
    assert is_injectable(MyItemPage()) is False
    assert is_injectable(ItemPage) is True
    assert is_injectable(ItemWebPage) is True


@pytest.mark.asyncio
async def test_item_page_typed():
    class MyPage(ItemPage[Item]):
        @field
        def name(self):
            return "name"

    page = MyPage()
    assert page.item_cls is Item
    item = await page.to_item()
    assert isinstance(item, Item)
    assert item == Item(name="name")


@pytest.mark.asyncio
async def test_item_page_typed_subclass():
    class BasePage(ItemPage[ItemT]):
        @field
        def name(self):
            return "name"

    class Subclass(BasePage[Item]):
        pass

    page = BasePage()
    assert page.item_cls is dict
    assert (await page.to_item()) == {"name": "name"}

    page2 = Subclass()
    assert page2.item_cls is Item
    assert (await page2.to_item()) == Item(name="name")


@pytest.mark.asyncio
async def test_item_page_change_item_type_extra_fields() -> None:
    class BasePage(ItemPage[Item]):
        @field
        def name(self):
            return "hello"

    @attrs.define
    class MyItem(Item):
        price: float

    class Subclass(BasePage, Returns[MyItem]):
        @field
        def price(self):
            return 123

    page = Subclass()
    assert page.item_cls is MyItem
    item = await page.to_item()
    assert isinstance(item, MyItem)
    assert item == MyItem(name="hello", price=123)


@pytest.mark.asyncio
async def test_item_page_change_item_type_remove_fields() -> None:
    @attrs.define
    class MyItem:
        name: str
        price: float

    class BasePage(ItemPage[MyItem]):
        @field
        def name(self):
            return "hello"

        @field
        def price(self):
            return 123

    # Item only contains "name", but not "price"
    class Subclass(BasePage, Returns[Item], skip_nonitem_fields=True):
        pass

    page = Subclass()
    assert page.item_cls is Item
    item = await page.to_item()
    assert isinstance(item, Item)
    assert item == Item(name="hello")
