import pytest
from attrs import define

from web_poet import ItemPage, field
from web_poet.simple_framework import get_item


@define
class SampleItem:
    foo: str


class SampleItemPageStub:
    def to_item(self):
        return SampleItem(foo="bar")


def test_async_to_item(registry):
    @registry.handle_urls("a.example")
    class Page(ItemPage[SampleItem]):
        @field
        async def foo(self):
            return "bar"

    item = get_item("https://a.example", SampleItem, registry=registry)
    assert isinstance(item, SampleItem)
    assert item.foo == "bar"


def test_sync_to_item(registry):
    @registry.handle_urls("a.example")
    class Page(ItemPage[SampleItem]):
        def to_item(self):
            return SampleItem(foo="bar")

    item = get_item("https://a.example", SampleItem, registry=registry)
    assert isinstance(item, SampleItem)
    assert item.foo == "bar"


def test_get_item_no_page(registry):
    with pytest.raises(
        ValueError, match=r"No page object class found for URL: https://a.example"
    ):
        get_item("https://a.example", SampleItem, registry=registry)
