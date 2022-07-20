import asyncio

import attrs
import pytest

from web_poet import HttpResponse, ItemPage, field, item_from_fields


@attrs.define
class Item:
    name: str
    price: str


@attrs.define
class Page(ItemPage):
    response: HttpResponse

    @field
    def name(self):  # noqa: D102
        return self.response.css("title ::text").get()

    @field
    async def price(self):  # noqa: D102
        await asyncio.sleep(0.01)
        return "$123"

    async def to_item(self):  # noqa: D102
        return await item_from_fields(self, Item)


@attrs.define
class InvalidPage(ItemPage):
    response: HttpResponse

    @field
    def name(self):  # noqa: D102
        return self.response.css("title ::text").get()

    @field
    def unknown_attribute(self):  # noqa: D102
        return "foo"

    async def to_item(self):  # noqa: D102
        return await item_from_fields(self, Item)


@pytest.mark.asyncio
async def test_fields():
    response = HttpResponse(
        "http://example.com",
        b"""
    <html>
    <head><title>Hello!</title>
    </html>
    """,
    )
    page = Page(response=response)

    assert page.name() == "Hello!"

    item = await page.to_item()
    assert isinstance(item, Item)
    assert item.name == "Hello!"
    assert item.price == "$123"


@pytest.mark.asyncio
async def test_fields_invalid_page():
    response = HttpResponse("http://example.com", b"")
    page = InvalidPage(response=response)
    with pytest.raises(TypeError, match="unexpected keyword argument 'unknown_attribute'"):
        await page.to_item()
