from attrs import define

from web_poet import ItemPage, default_registry, field, handle_urls
from web_poet.example import get_item


def test_async_to_item():
    @define
    class Item:
        foo: str

    try:

        @handle_urls("")
        class Page(ItemPage[Item]):
            @field
            async def foo(self):
                return "bar"

        item = get_item("file:///dev/null", Item)
        assert isinstance(item, Item)
        assert item.foo == "bar"
    finally:
        default_registry._rules.pop()


def test_sync_to_item():
    @define
    class Item:
        foo: str

    try:

        @handle_urls("")
        class Page(ItemPage[Item]):
            def to_item(self):
                return Item(foo="bar")

        item = get_item("file:///dev/null", Item)
        assert isinstance(item, Item)
        assert item.foo == "bar"
    finally:
        default_registry._rules.pop()
