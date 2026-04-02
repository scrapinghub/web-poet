import niquests
import pytest
from attrs import define

from web_poet import Injectable, ItemPage, field
from web_poet.page_inputs.client import HttpClient
from web_poet.page_inputs.http import HttpResponse
from web_poet.page_inputs.page_params import PageParams
from web_poet.page_inputs.url import RequestUrl, ResponseUrl
from web_poet.simple_framework import get_item


@define
class SampleItem:
    foo: str


SAMPLE_ITEM = SampleItem(foo="bar")


class SampleItemPageStub:
    def to_item(self):
        return SAMPLE_ITEM


def patch_aget(monkeypatch):
    class DummyResponse:
        def __init__(self):
            self.url = "https://b.example"
            self.status_code = 200
            self.content = b""
            self.headers = {}

    state = {"calls": 0}

    async def fake_aget(url, timeout=300):
        state["calls"] += 1
        return DummyResponse()

    monkeypatch.setattr(niquests, "aget", fake_aget)
    return state


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
async def test_page_params(registry, monkeypatch):
    state = patch_aget(monkeypatch)

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
    assert state["calls"] == 0


@pytest.mark.asyncio
async def test_response_url(registry, monkeypatch):
    state = patch_aget(monkeypatch)

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        url: ResponseUrl

        async def to_item(self):
            assert str(self.url) == "https://b.example"
            return SAMPLE_ITEM

    item = await get_item("https://a.example", SampleItem, registry=registry)
    assert item == SAMPLE_ITEM
    assert state["calls"] == 1


@pytest.mark.asyncio
async def test_request_url(registry, monkeypatch):
    state = patch_aget(monkeypatch)

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        request_url: RequestUrl

        async def to_item(self):
            assert str(self.request_url) == "https://a.example"
            return SAMPLE_ITEM

    item = await get_item("https://a.example", SampleItem, registry=registry)
    assert item == SAMPLE_ITEM
    assert state["calls"] == 0


@pytest.mark.asyncio
async def test_both_urls(registry, monkeypatch):
    state = patch_aget(monkeypatch)

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        request_url: RequestUrl
        response_url: ResponseUrl

        async def to_item(self):
            assert str(self.request_url) == "https://a.example"
            assert str(self.response_url) == "https://b.example"
            return SAMPLE_ITEM

    item = await get_item("https://a.example", SampleItem, registry=registry)
    assert item == SAMPLE_ITEM
    assert state["calls"] == 1


@pytest.mark.asyncio
async def test_multiple_response_dependencies(registry, monkeypatch):
    state = patch_aget(monkeypatch)

    @define
    class Page2(Injectable):
        url: ResponseUrl

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        url: ResponseUrl
        response: HttpResponse
        page2: Page2

        async def to_item(self):
            assert str(self.url) == "https://b.example"
            assert str(self.page2.url) == "https://b.example"
            assert str(self.response.url) == "https://b.example"
            return SAMPLE_ITEM

    item = await get_item("https://a.example", SampleItem, registry=registry)
    assert item == SAMPLE_ITEM
    assert state["calls"] == 1
