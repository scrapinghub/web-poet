from __future__ import annotations

from typing import Generic, Optional, TypeVar

import attrs
import pytest

from web_poet import HttpResponse, PageParams, field
from web_poet.pages import (
    Injectable,
    ItemPage,
    ItemT,
    Returns,
    SelectorExtractor,
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
        def to_item(self) -> dict:  # type: ignore[override]
            return {
                "url": self.url,
                "title": self.css("title::text").get("").strip(),
            }

    page_object = MyWebPage(book_list_html_response)
    assert page_object.to_item() == {
        "url": "http://books.toscrape.com/index.html",
        "title": "All products | Books to Scrape - Sandbox",
    }


def test_is_injectable() -> None:
    class MyClass:
        pass

    class MyItemPage(ItemPage):
        def to_item(self) -> dict:  # type: ignore[override]
            return {
                "foo": "bar",
            }

    from collections.abc import Set as CollectionsSet  # noqa: PYI025,PLC0415
    from typing import Set as TypingSet  # noqa: UP035,PLC0415

    assert is_injectable(None) is False
    assert is_injectable(type(None)) is False
    assert is_injectable(set) is False
    assert is_injectable(set[str]) is False
    assert is_injectable(TypingSet[str]) is False  # noqa: UP006
    assert is_injectable(CollectionsSet[str]) is False
    assert is_injectable(Optional[str]) is False
    assert is_injectable(MyClass) is False
    assert is_injectable(MyClass()) is False
    assert is_injectable(MyItemPage) is True
    assert is_injectable(MyItemPage()) is False
    assert is_injectable(ItemPage) is True


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
        price: float | None

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

    # Same as above but a slotted attrs class with dependency.
    # See: https://github.com/scrapinghub/web-poet/issues/141
    @attrs.define
    class SubclassWithDep(BasePage, Returns[Item], skip_nonitem_fields=True):
        params: PageParams

    # Check if flicking skip_nonitem_fields to False in the subclass works
    @attrs.define
    class SubclassSkipFalse(SubclassWithDep, Returns[Item], skip_nonitem_fields=False):
        pass

    for page in [Subclass(), SubclassWithDep(params=PageParams())]:
        assert page.item_cls is Item
        item = await page.to_item()
        assert isinstance(item, Item)
        assert item == Item(name="hello")

    page = SubclassSkipFalse(params=PageParams())
    assert page.item_cls is Item
    with pytest.raises(TypeError, match="unexpected keyword argument 'price'"):
        await page.to_item()

    # Item only contains "name", but not "price", but "price" should be passed
    class SubclassStrict(BasePage, Returns[Item]):
        pass

    page2 = SubclassStrict()
    assert page2.item_cls is Item
    with pytest.raises(TypeError, match="unexpected keyword argument 'price'"):
        await page2.to_item()


def test_returns_inheritance() -> None:
    @attrs.define
    class MyItem:
        name: str

    class BasePage(ItemPage[MyItem]):
        @field
        def name(self):
            return "hello"

    MetadataT = TypeVar("MetadataT")

    class HasMetadata(Generic[MetadataT]):
        pass

    class DummyMetadata:
        pass

    class Page(BasePage, HasMetadata[DummyMetadata]):
        pass

    page = Page()
    assert page.item_cls is MyItem


@pytest.mark.asyncio
async def test_extractor(book_list_html_response) -> None:
    @attrs.define
    class BookItem:
        name: str
        price: str

    @attrs.define
    class ListItem:
        books: list[BookItem]

    @attrs.define
    class MyPage(ItemPage[ListItem]):
        response: HttpResponse

        @field
        async def books(self):
            books = []
            for book in self.response.css("article"):
                item = await BookExtractor(book).to_item()
                books.append(item)
            return books

    class BookExtractor(SelectorExtractor[BookItem]):
        @field(out=[str.lower])
        def name(self):
            return self.css("img.thumbnail::attr(alt)").get()

        @field
        def price(self):
            return self.xpath(".//p[@class='price_color']/text()").get()

    page = MyPage(book_list_html_response)
    item = await page.to_item()
    assert len(item.books) == 20
    assert item.books[0].name == "a light in the attic"
    assert item.books[0].price == "£51.77"
