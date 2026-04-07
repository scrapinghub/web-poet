from typing import Annotated

import niquests
import pytest
from attrs import define

from web_poet import Injectable, ItemPage, field
from web_poet.exceptions import HttpResponseError
from web_poet.page_inputs import Stats
from web_poet.page_inputs.browser import BrowserHtml, BrowserResponse
from web_poet.page_inputs.client import HttpClient
from web_poet.page_inputs.http import (
    HttpRequest,
    HttpRequestBody,
    HttpRequestHeaders,
    HttpResponse,
    HttpResponseBody,
    HttpResponseHeaders,
)
from web_poet.page_inputs.page_params import PageParams
from web_poet.page_inputs.response import AnyResponse
from web_poet.page_inputs.stats import DictStatCollector
from web_poet.page_inputs.url import RequestUrl, ResponseUrl
from web_poet.simple_framework import Poet, _providers, browser


@define
class SampleItem:
    foo: str


SAMPLE_ITEM = SampleItem(foo="bar")


class SampleItemPageStub:
    def to_item(self):
        return SAMPLE_ITEM


def patch_aget(
    monkeypatch,
    *,
    response_url="https://b.example",
    status=200,
    content=b"",
    headers=None,
):
    class DummyResponse:
        def __init__(self):
            self.url = response_url
            self.status_code = status
            self.content = content
            self.headers = headers or {}

    state = {"calls": 0}

    async def fake_aget(_url, timeout=300):
        state["calls"] += 1
        return DummyResponse()

    monkeypatch.setattr(niquests, "aget", fake_aget)
    return state


def patch_async_playwright(
    monkeypatch,
    *,
    response_url="https://c.example",
    html="<html><body>engine:{engine}</body></html>",
    status=200,
):
    state = {"calls": 0, "launches": {}}

    class DummyGotoResponse:
        def __init__(self, status_code):
            self.status = status_code

    class DummyPage:
        def __init__(self, engine_name: str):
            self.url = "about:blank"
            self._engine = engine_name

        async def goto(self, _url):
            state["calls"] += 1
            self.url = response_url
            if status is None:
                return None
            return DummyGotoResponse(status)

        async def content(self):
            try:
                return html.format(engine=self._engine)
            except Exception:
                return html

    class DummyBrowser:
        def __init__(self, engine_name: str):
            self._engine = engine_name

        async def new_page(self):
            return DummyPage(self._engine)

        async def close(self):
            return None

    class DummyEngine:
        def __init__(self, name: str):
            self.name = name

        async def launch(self):
            state["launches"].setdefault(self.name, 0)
            state["launches"][self.name] += 1
            return DummyBrowser(self.name)

    class DummyPlaywright:
        chromium = DummyEngine("chromium")
        firefox = DummyEngine("firefox")
        webkit = DummyEngine("webkit")

    class DummyPlaywrightContext:
        async def __aenter__(self):
            return DummyPlaywright()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    def fake_async_playwright():
        return DummyPlaywrightContext()

    monkeypatch.setattr(_providers, "async_playwright", fake_async_playwright)
    return state


@pytest.mark.asyncio
async def test_async_to_item(registry):
    @registry.handle_urls("a.example")
    class Page(ItemPage[SampleItem]):
        @field
        async def foo(self):
            return "bar"

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM


@pytest.mark.asyncio
async def test_sync_to_item(registry):
    @registry.handle_urls("a.example")
    class Page(ItemPage[SampleItem]):
        def to_item(self):
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM


@pytest.mark.asyncio
async def test_get_item_no_page(registry):
    poet = Poet(registry=registry)
    with pytest.raises(
        ValueError, match=r"No page object class found for URL: https://a.example"
    ):
        await poet.get_item("https://a.example", SampleItem)


@pytest.mark.asyncio
async def test_http_client(registry, monkeypatch):
    http_state = patch_aget(monkeypatch)
    browser_state = patch_async_playwright(monkeypatch)

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        http_client: HttpClient

        async def to_item(self):
            response = await self.http_client.get("https://a.example")
            assert response.status == 200
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert http_state["calls"] == 1
    assert browser_state["calls"] == 0


@pytest.mark.asyncio
async def test_http_client_allow_status(registry, monkeypatch):
    http_state = patch_aget(monkeypatch, status=404)
    browser_state = patch_async_playwright(monkeypatch)

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        http_client: HttpClient

        async def to_item(self):
            # Default behavior: 404 raises HttpResponseError
            with pytest.raises(HttpResponseError):
                await self.http_client.get("https://a.example")

            # Allow 404 via allow_status
            resp = await self.http_client.get("https://a.example", allow_status=404)
            assert resp.status == 404
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert http_state["calls"] == 2
    assert browser_state["calls"] == 0


@pytest.mark.asyncio
async def test_page_params(registry, monkeypatch):
    http_state = patch_aget(monkeypatch)
    browser_state = patch_async_playwright(monkeypatch)

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        page_params: PageParams

        async def to_item(self):
            return SampleItem(foo=self.page_params["foo"])

    poet = Poet(registry=registry)
    item = await poet.get_item(
        "https://a.example", SampleItem, page_params={"foo": "bar"}
    )
    assert item == SAMPLE_ITEM
    assert http_state["calls"] == 0
    assert browser_state["calls"] == 0


@pytest.mark.asyncio
async def test_response_url(registry, monkeypatch):
    http_state = patch_aget(monkeypatch)
    browser_state = patch_async_playwright(monkeypatch)

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        url: ResponseUrl

        async def to_item(self):
            assert str(self.url) == "https://b.example"
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert http_state["calls"] == 1
    assert browser_state["calls"] == 0


@pytest.mark.asyncio
async def test_browser_response(registry, monkeypatch):
    http_state = patch_aget(monkeypatch)
    browser_state = patch_async_playwright(
        monkeypatch,
        response_url="https://c.example",
        html="<html><body>hello</body></html>",
        status=201,
    )

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        response: BrowserResponse

        async def to_item(self):
            assert isinstance(self.response, BrowserResponse)
            assert str(self.response.url) == "https://c.example"
            assert self.response.status == 201
            assert self.response.text == "<html><body>hello</body></html>"
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert browser_state["calls"] == 1
    assert http_state["calls"] == 0


@pytest.mark.asyncio
async def test_stats_no_collector_passed(registry):
    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[dict]):
        stats: Stats

        async def to_item(self):
            self.stats.set("a", "1")
            self.stats.inc("b")
            # return the underlying collector dict for assertion
            return self.stats._stats._stats

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", dict)
    assert item == {"a": "1", "b": 1}


@pytest.mark.asyncio
async def test_stats_with_collector_passed(registry):
    collector = DictStatCollector()

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        stats: Stats

        async def to_item(self):
            self.stats.set("latest", "ok")
            self.stats.inc("hits")
            return SAMPLE_ITEM

    poet = Poet(registry=registry, stats=collector)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert collector.data == {"latest": "ok", "hits": 1}


@pytest.mark.asyncio
async def test_any_response_prefers_http(registry, monkeypatch):
    http_state = patch_aget(monkeypatch, response_url="https://b.example")
    browser_state = patch_async_playwright(monkeypatch)

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        response: AnyResponse

        async def to_item(self):
            assert isinstance(self.response, AnyResponse)
            assert isinstance(self.response.response, HttpResponse)
            assert str(self.response.url) == "https://b.example"
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert http_state["calls"] == 1
    assert browser_state["calls"] == 0


@pytest.mark.asyncio
async def test_any_response_uses_browser_when_browser_needed(registry, monkeypatch):
    http_state = patch_aget(monkeypatch)
    browser_state = patch_async_playwright(
        monkeypatch,
        response_url="https://c.example",
        html="<html><body>hello</body></html>",
        status=201,
    )

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        browser_response: BrowserResponse
        response: AnyResponse

        async def to_item(self):
            assert isinstance(self.response, AnyResponse)
            assert isinstance(self.response.response, BrowserResponse)
            assert str(self.response.url) == "https://c.example"
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert browser_state["calls"] == 1
    assert http_state["calls"] == 0


@pytest.mark.asyncio
async def test_request_specific_browser_annotation(registry, monkeypatch):
    http_state = patch_aget(monkeypatch)
    browser_state = patch_async_playwright(monkeypatch)

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        response: Annotated[BrowserResponse, browser("firefox")]

        async def to_item(self):
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert http_state["calls"] == 0
    assert browser_state["launches"] == {"firefox": 1}


@pytest.mark.asyncio
async def test_default_browser_param_override(registry, monkeypatch):
    http_state = patch_aget(monkeypatch)
    browser_state = patch_async_playwright(monkeypatch)

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        response: BrowserResponse

        async def to_item(self):
            return SAMPLE_ITEM

    poet = Poet(registry=registry, default_browser="webkit")
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert http_state["calls"] == 0
    assert browser_state["launches"] == {"webkit": 1}


@pytest.mark.asyncio
async def test_multiple_browser_responses_and_unannotated_choice(registry, monkeypatch):
    http_state = patch_aget(monkeypatch)
    browser_state = patch_async_playwright(monkeypatch)

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        resp_a: Annotated[BrowserResponse, browser("firefox")]
        resp_b: Annotated[BrowserResponse, browser("chromium")]
        resp_c: BrowserResponse

        async def to_item(self):
            # When annotated deps include the default browser, unannotated deps
            # should use the default.
            assert isinstance(self.resp_a, BrowserResponse)
            assert "engine:firefox" in self.resp_a.text
            assert isinstance(self.resp_b, BrowserResponse)
            assert "engine:chromium" in self.resp_b.text
            assert isinstance(self.resp_c, BrowserResponse)
            assert "engine:chromium" in self.resp_c.text
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert browser_state["launches"] == {"chromium": 1, "firefox": 1}
    assert http_state["calls"] == 0

    # repeat with default override to firefox (unannotated should pick default)
    browser_state2 = patch_async_playwright(monkeypatch)

    @registry.handle_urls("b.example")
    @define
    class Page2(ItemPage[SampleItem]):
        resp_a: Annotated[BrowserResponse, browser("firefox")]
        resp_b: Annotated[BrowserResponse, browser("chromium")]
        resp_c: BrowserResponse

        async def to_item(self):
            # with default override to firefox, unannotated resp_c should use firefox
            assert isinstance(self.resp_a, BrowserResponse)
            assert "engine:firefox" in self.resp_a.text
            assert isinstance(self.resp_b, BrowserResponse)
            assert "engine:chromium" in self.resp_b.text
            assert isinstance(self.resp_c, BrowserResponse)
            assert "engine:firefox" in self.resp_c.text
            return SAMPLE_ITEM

    poet = Poet(registry=registry, default_browser="firefox")
    item = await poet.get_item("https://b.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert browser_state2["launches"] == {"chromium": 1, "firefox": 1}
    assert http_state["calls"] == 0

    # scenario: resp_a uses firefox and resp_b uses webkit => unannotated picks
    # alphabetical (firefox)
    browser_state3 = patch_async_playwright(monkeypatch)

    @registry.handle_urls("a.example/page3")
    @define
    class Page3(ItemPage[SampleItem]):
        resp_a: Annotated[BrowserResponse, browser("firefox")]
        resp_b: Annotated[BrowserResponse, browser("webkit")]
        resp_c: BrowserResponse

        async def to_item(self):
            # resp_a (firefox), resp_b (webkit), resp_c should pick alphabetical (firefox)
            assert isinstance(self.resp_a, BrowserResponse)
            assert "engine:firefox" in self.resp_a.text
            assert isinstance(self.resp_b, BrowserResponse)
            assert "engine:webkit" in self.resp_b.text
            assert isinstance(self.resp_c, BrowserResponse)
            assert "engine:firefox" in self.resp_c.text
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example/page3", SampleItem)
    assert item == SAMPLE_ITEM
    assert browser_state3["launches"] == {"firefox": 1, "webkit": 1}


@pytest.mark.asyncio
async def test_browser_html_annotation(registry, monkeypatch):
    http_state = patch_aget(monkeypatch)
    browser_state = patch_async_playwright(monkeypatch)

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        html: Annotated[BrowserHtml, browser("firefox")]

        async def to_item(self):
            assert isinstance(self.html, BrowserHtml)
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert browser_state["launches"] == {"firefox": 1}
    assert http_state["calls"] == 0


@pytest.mark.asyncio
async def test_unsupported_browser_raises(registry, monkeypatch):
    patch_aget(monkeypatch)
    patch_async_playwright(monkeypatch)

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        response: Annotated[BrowserResponse, browser("foo")]

        async def to_item(self):
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    with pytest.raises(ValueError, match=r"Playwright does not provide engine"):
        await poet.get_item("https://a.example", SampleItem)


@pytest.mark.asyncio
async def test_browser_html_dependency(registry, monkeypatch):
    http_state = patch_aget(monkeypatch)
    browser_state = patch_async_playwright(
        monkeypatch,
        response_url="https://c.example",
        html="<html><body>hello</body></html>",
        status=200,
    )

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        html: BrowserHtml

        async def to_item(self):
            assert isinstance(self.html, BrowserHtml)
            assert str(self.html) == "<html><body>hello</body></html>"
            assert self.html.xpath("//body/text()").get("").strip() == "hello"
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert browser_state["calls"] == 1
    assert http_state["calls"] == 0


@pytest.mark.asyncio
async def test_response_url_with_browser_response(registry, monkeypatch):
    http_state = patch_aget(monkeypatch)
    browser_state = patch_async_playwright(
        monkeypatch, response_url="https://c.example"
    )

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        response_url: ResponseUrl
        browser_response: BrowserResponse

        async def to_item(self):
            assert str(self.browser_response.url) == "https://c.example"
            assert str(self.response_url) == "https://c.example"
            return SAMPLE_ITEM

    item = await Poet(registry=registry).get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert browser_state["calls"] == 1
    assert http_state["calls"] == 0


@pytest.mark.asyncio
async def test_http_request_body(registry):
    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        body: HttpRequestBody

        async def to_item(self):
            assert isinstance(self.body, HttpRequestBody)
            assert bytes(self.body) == b"foo"
            return SAMPLE_ITEM

    request = HttpRequest(url="https://a.example", body=b"foo")
    poet = Poet(registry=registry)
    item = await poet.get_item(request, SampleItem)
    assert item == SAMPLE_ITEM


@pytest.mark.asyncio
async def test_http_request_headers(registry):
    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        headers: HttpRequestHeaders

        async def to_item(self):
            assert isinstance(self.headers, HttpRequestHeaders)
            assert self.headers.get("x-foo") == "bar"
            return SAMPLE_ITEM

    request = HttpRequest(url="https://a.example", headers={"X-Foo": "bar"})
    poet = Poet(registry=registry)
    item = await poet.get_item(request, SampleItem)
    assert item == SAMPLE_ITEM


@pytest.mark.asyncio
async def test_http_request(registry):
    request = HttpRequest(url="https://a.example")

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        request: HttpRequest

        async def to_item(self):
            assert self.request is request
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item(request, SampleItem)
    assert item == SAMPLE_ITEM


@pytest.mark.asyncio
async def test_http_response_body(registry, monkeypatch):
    state = patch_aget(monkeypatch, content=b"hello")

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        body: HttpResponseBody

        async def to_item(self):
            assert isinstance(self.body, HttpResponseBody)
            assert bytes(self.body) == b"hello"
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert state["calls"] == 1


@pytest.mark.asyncio
async def test_http_response_headers(registry, monkeypatch):
    state = patch_aget(monkeypatch, headers={"X-Foo": "bar"})

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        headers: HttpResponseHeaders

        async def to_item(self):
            assert isinstance(self.headers, HttpResponseHeaders)
            assert self.headers.get("x-foo") == "bar"
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert state["calls"] == 1


@pytest.mark.asyncio
async def test_request_url(registry, monkeypatch):
    http_state = patch_aget(monkeypatch)
    browser_state = patch_async_playwright(monkeypatch)

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        request_url: RequestUrl

        async def to_item(self):
            assert str(self.request_url) == "https://a.example"
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert http_state["calls"] == 0
    assert browser_state["calls"] == 0


@pytest.mark.asyncio
async def test_both_urls(registry, monkeypatch):
    http_state = patch_aget(monkeypatch)
    browser_state = patch_async_playwright(monkeypatch)

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        request_url: RequestUrl
        response_url: ResponseUrl

        async def to_item(self):
            assert str(self.request_url) == "https://a.example"
            assert str(self.response_url) == "https://b.example"
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert http_state["calls"] == 1
    assert browser_state["calls"] == 0


@pytest.mark.asyncio
async def test_http_and_browser_responses(registry, monkeypatch):
    http_state = patch_aget(monkeypatch, response_url="https://b.example")
    browser_state = patch_async_playwright(
        monkeypatch, response_url="https://c.example"
    )

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        http_response: HttpResponse
        browser_response: BrowserResponse
        response_url: ResponseUrl

        async def to_item(self):
            assert str(self.http_response.url) == "https://b.example"
            assert str(self.browser_response.url) == "https://c.example"
            assert str(self.response_url) == "https://c.example"
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert http_state["calls"] == 1
    assert browser_state["calls"] == 1


@pytest.mark.asyncio
async def test_multiple_http_response_dependencies(registry, monkeypatch):
    http_state = patch_aget(monkeypatch)
    browser_state = patch_async_playwright(monkeypatch)

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

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert http_state["calls"] == 1
    assert browser_state["calls"] == 0


@pytest.mark.asyncio
async def test_multiple_browser_response_dependencies(registry, monkeypatch):
    http_state = patch_aget(monkeypatch)
    browser_state = patch_async_playwright(
        monkeypatch, response_url="https://c.example"
    )

    @define
    class Page2(Injectable):
        url: ResponseUrl

    @registry.handle_urls("a.example")
    @define
    class Page(ItemPage[SampleItem]):
        url: ResponseUrl
        response: BrowserResponse
        page2: Page2

        async def to_item(self):
            assert str(self.url) == "https://c.example"
            assert str(self.page2.url) == "https://c.example"
            assert str(self.response.url) == "https://c.example"
            return SAMPLE_ITEM

    poet = Poet(registry=registry)
    item = await poet.get_item("https://a.example", SampleItem)
    assert item == SAMPLE_ITEM
    assert browser_state["calls"] == 1
    assert http_state["calls"] == 0
