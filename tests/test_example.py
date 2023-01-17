from attrs import define

from web_poet import ItemPage, default_registry, field, handle_urls
from web_poet.example import get_item


def _revert_add_rule():
    default_registry._rule_counter -= 1
    rule_id = list(default_registry._rules)[-1]
    default_registry._rules.pop(rule_id)
    default_registry._overrides_matchers[None].remove(rule_id)
    default_registry._item_matchers[None].remove(rule_id)


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
        _revert_add_rule()


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
        _revert_add_rule()
