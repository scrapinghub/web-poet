import asyncio

import attrs
import pytest

from web_poet import (
    HttpResponse,
    ItemPage,
    field,
    item_from_fields,
    item_from_fields_sync,
)


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


def test_item_from_fields_sync():
    @attrs.define
    class Page(ItemPage):
        @field
        def name(self):  # noqa: D102
            return "name"

        def to_item(self):  # noqa: D102
            return item_from_fields_sync(self, dict)

    page = Page()
    assert page.to_item() == dict(name="name")


def test_field_non_callable():
    with pytest.raises(TypeError):

        @attrs.define
        class Page(ItemPage):
            @field
            @property
            def name(self):  # noqa: D102
                return "name"

            def to_item(self):  # noqa: D102
                return item_from_fields_sync(self, dict)


def test_field_classmethod():
    with pytest.raises(TypeError):

        @attrs.define
        class Page(ItemPage):
            @field
            @classmethod
            def name(cls):  # noqa: D102
                return "name"

            def to_item(self):  # noqa: D102
                return item_from_fields_sync(self, dict)


@pytest.mark.asyncio
async def test_field_order():
    class DictItemPage(Page):
        async def to_item(self):
            return await item_from_fields(self)

    response = HttpResponse(
        "http://example.com",
        b"""
    <html>
    <head><title>Hello!</title>
    </html>
    """,
    )
    page = DictItemPage(response=response)
    item = await page.to_item()
    assert item == {"name": "Hello!", "price": "$123"}
    assert list(item.keys()) == ["name", "price"]
