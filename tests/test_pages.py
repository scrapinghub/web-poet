from typing import Optional

import attrs
import pytest

from web_poet import HttpResponse, PageParams, field
from web_poet.pages import (
    Injectable,
    ItemPage,
    ItemT,
    ItemWebPage,
    MultiLayoutPage,
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


@pytest.mark.asyncio
async def test_multi_layout_page_object():
    @attrs.define
    class Header:
        text: str

    class H1Page(WebPage[Header]):
        @field
        def text(self) -> Optional[str]:
            return self.css("h1::text").get()

    class H2Page(WebPage[Header]):
        @field
        def text(self) -> Optional[str]:
            return self.css("h2::text").get()

    @attrs.define
    class HeaderMultiLayoutPage(MultiLayoutPage[Header]):
        response: HttpResponse
        h1: H1Page
        h2: H2Page

        async def get_layout(self) -> ItemPage[Header]:
            if self.response.css("h1::text"):
                return self.h1
            return self.h2

    html_h1 = b"""
    <!DOCTYPE html>
    <html lang="en">
        <head>
            <title>h1</title>
        </head>
        <body>
            <h1>a</h1>
        </body>
    </html>
    """
    html_h2 = b"""
    <!DOCTYPE html>
    <html lang="en">
        <head>
            <title>h2</title>
        </head>
        <body>
            <h2>b</h2>
        </body>
    </html>
    """

    response1 = HttpResponse("https://example.com", body=html_h1)
    h1_1 = H1Page(response=response1)
    h2_1 = H2Page(response=response1)
    response2 = HttpResponse("https://example.com", body=html_h2)
    h1_2 = H1Page(response=response2)
    h2_2 = H2Page(response=response2)

    item1 = await HeaderMultiLayoutPage(response=response1, h1=h1_1, h2=h2_1).to_item()
    item2 = await HeaderMultiLayoutPage(response=response2, h1=h1_2, h2=h2_2).to_item()

    assert item1.text == "a"
    assert item2.text == "b"


@pytest.mark.asyncio
async def test_multi_layout_page_object_shared_partial_layout():
    """Scenario where a multi-layout page object acts as a switch for 2 or
    more layout page objects that all inherit from some other page object class
    that implements extraction for shared fields."""

    @attrs.define
    class PartialItem:
        url: str

    @attrs.define
    class FullItem(PartialItem):
        text: str

    class PartialPage(WebPage[PartialItem]):
        @field
        async def url(self) -> str:
            return str(self.response.url)

    class FullPage1(PartialPage, Returns[FullItem]):
        @field
        async def text(self) -> Optional[str]:
            return self.css("h1::text").get()

    class FullPage2(PartialPage, Returns[FullItem]):
        @field
        async def text(self) -> Optional[str]:
            return self.css("h2::text").get()

    @attrs.define
    class MyMultiLayoutPage(MultiLayoutPage[FullItem]):
        response: HttpResponse
        page1: FullPage1
        page2: FullPage2

        async def get_layout(self) -> ItemPage[FullItem]:
            if self.response.css("h1::text"):
                return self.page1  # type: ignore[return-value]
            return self.page2  # type: ignore[return-value]

    html1 = b"""
    <!DOCTYPE html>
    <html lang="en">
        <head>
            <title>h1</title>
        </head>
        <body>
            <h1>a</h1>
        </body>
    </html>
    """
    html2 = b"""
    <!DOCTYPE html>
    <html lang="en">
        <head>
            <title>h2</title>
        </head>
        <body>
            <h2>b</h2>
        </body>
    </html>
    """

    url = "https://example.com"
    response1 = HttpResponse(url, body=html1)
    page1_1 = FullPage1(response=response1)
    page2_1 = FullPage2(response=response1)
    response2 = HttpResponse(url, body=html2)
    page1_2 = FullPage1(response=response2)
    page2_2 = FullPage2(response=response2)

    multilayoutpage1 = MyMultiLayoutPage(
        response=response1, page1=page1_1, page2=page2_1
    )
    multilayoutpage2 = MyMultiLayoutPage(
        response=response2, page1=page1_2, page2=page2_2
    )

    # To access page object fields, you must first get the underlying page
    # object, and then access its fields:
    layout1 = await multilayoutpage1.get_layout()
    assert await layout1.url == url
    assert await layout1.text == "a"
    layout2 = await multilayoutpage2.get_layout()
    assert await layout2.url == url
    assert await layout2.text == "b"

    # Returned items work as expected.
    item1 = await multilayoutpage1.to_item()
    assert item1.url == url
    assert item1.text == "a"
    item2 = await multilayoutpage2.to_item()
    assert item2.url == url
    assert item2.text == "b"


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
