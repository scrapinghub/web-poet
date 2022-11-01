from typing import Optional

import attrs
import pytest

from web_poet import HttpResponse, field
from web_poet.pages import (
    Injectable,
    ItemPage,
    ItemT,
    ItemWebPage,
    Returns,
    WebPage,
    is_injectable,
)


@attrs.define
class Item:
    name: str


def test_page_object() -> None:
    class MyItemPage(Injectable):
        def to_item(self) -> dict:
            return {
                "foo": "bar",
            }

    page_object = MyItemPage()
    assert page_object.to_item() == {
        "foo": "bar",
    }


def test_web_page_object(book_list_html_response) -> None:
    class MyWebPage(WebPage):
        def to_item(self) -> dict:  # type: ignore
            return {
                "url": self.url,
                "title": self.css("title::text").get("").strip(),
            }

    page_object = MyWebPage(book_list_html_response)
    assert page_object.to_item() == {
        "url": "http://books.toscrape.com/index.html",
        "title": "All products | Books to Scrape - Sandbox",
    }


def test_item_web_page_deprecated() -> None:
    with pytest.warns(
        DeprecationWarning, match="deprecated class web_poet.pages.ItemWebPage"
    ):

        class MyItemWebPage(ItemWebPage):
            pass


def test_is_injectable() -> None:
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
async def test_item_page_typed() -> None:
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
async def test_web_page_fields() -> None:
    class MyPage(WebPage[Item]):
        @field
        def name(self):
            return "name"

    page = MyPage(HttpResponse(url="http://example.com", body=b""))
    assert page.item_cls is Item
    item = await page.to_item()
    assert isinstance(item, Item)
    assert item == Item(name="name")


@pytest.mark.asyncio
async def test_item_page_typed_subclass() -> None:
    class BasePage(ItemPage[ItemT]):
        @field
        def name(self):
            return "name"

    class Subclass(BasePage[Item]):
        pass

    page: BasePage = BasePage()
    assert page.item_cls is dict
    assert (await page.to_item()) == {"name": "name"}

    page2: Subclass = Subclass()
    assert page2.item_cls is Item
    assert (await page2.to_item()) == Item(name="name")


@pytest.mark.asyncio
async def test_item_page_fields_typo() -> None:
    class MyPage(ItemPage[Item]):
        @field
        def nane(self):
            return "name"

    page = MyPage()
    assert page.item_cls is Item
    with pytest.raises(TypeError, match="unexpected keyword argument 'nane'"):
        await page.to_item()


@pytest.mark.asyncio
async def test_item_page_required_field_missing() -> None:
    @attrs.define
    class MyItem:
        name: str
        price: Optional[float]

    class MyPage(ItemPage[MyItem]):
        @field
        def price(self):
            return 100

    page = MyPage()
    assert page.item_cls is MyItem
    with pytest.raises(
        TypeError, match="missing 1 required positional argument: 'name'"
    ):
        await page.to_item()


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

    # Item only contains "name", but not "price", but "price" should be passed
    class SubclassStrict(BasePage, Returns[Item]):
        pass

    page2 = SubclassStrict()
    assert page2.item_cls is Item
    with pytest.raises(TypeError, match="unexpected keyword argument 'price'"):
        await page2.to_item()
