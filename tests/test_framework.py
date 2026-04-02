import pytest
from attrs import define

from web_poet import ItemPage, field
from web_poet.page_inputs.client import HttpClient
from web_poet.page_inputs.page_params import PageParams
from web_poet.simple_framework import get_item


@define
class SampleItem:
    foo: str


SAMPLE_ITEM = SampleItem(foo="bar")


class SampleItemPageStub:
    def to_item(self):
        return SAMPLE_ITEM


@pytest.mark.asyncio
async def test_async_to_item(registry):
    @registry.handle_urls("a.example")
    class Page(ItemPage[SampleItem]):
        @field
        async def foo(self):
            return "bar"

    item = await get_item("https://a.example", SampleItem, registry=registry)
    assert item == SAMPLE_ITEM


@pytest.mark.asyncio
async def test_sync_to_item(registry):
    @registry.handle_urls("a.example")
    class Page(ItemPage[SampleItem]):
        def to_item(self):
            return SAMPLE_ITEM

    item = await get_item("https://a.example", SampleItem, registry=registry)
    assert item == SAMPLE_ITEM


@pytest.mark.asyncio
async def test_get_item_no_page(registry):
    with pytest.raises(
        ValueError, match=r"No page object class found for URL: https://a.example"
    ):
        await get_item("https://a.example", SampleItem, registry=registry)


@pytest.mark.asyncio
async def test_http_client(registry):
    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        http_client: HttpClient

        async def to_item(self):
            response = await self.http_client.get("https://httpbin.org/get")
            assert response.status == 200
            return SAMPLE_ITEM

    item = await get_item("https://a.example", SampleItem, registry=registry)
    assert item == SAMPLE_ITEM


@pytest.mark.asyncio
async def test_page_params(registry):
    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        page_params: PageParams

        async def to_item(self):
            return SampleItem(foo=self.page_params["foo"])

    item = await get_item(
        "https://a.example", SampleItem, registry=registry, page_params={"foo": "bar"}
    )
    assert item == SAMPLE_ITEM
