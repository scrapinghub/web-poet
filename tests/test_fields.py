import asyncio
import random

import attrs
import pytest

from web_poet import (
    HttpResponse,
    Injectable,
    ItemPage,
    field,
    item_from_fields,
    item_from_fields_sync,
)
from web_poet.fields import get_fields_dict


@attrs.define
class Item:
    name: str
    price: str


@attrs.define
class Page(ItemPage[Item]):
    response: HttpResponse

    @field
    def name(self):  # noqa: D102
        return self.response.css("title ::text").get()

    @field
    async def price(self):  # noqa: D102
        await asyncio.sleep(0.01)
        return "$123"


@attrs.define
class InvalidPage(ItemPage[Item]):
    response: HttpResponse

    @field
    def name(self):  # noqa: D102
        return self.response.css("title ::text").get()

    @field
    def unknown_attribute(self):  # noqa: D102
        return "foo"


EXAMPLE_RESPONSE = HttpResponse(
    "http://example.com",
    body=b"<html><head><title>Hello!</title></html>",
)


@pytest.mark.asyncio
async def test_fields() -> None:
    page = Page(response=EXAMPLE_RESPONSE)

    assert page.name == "Hello!"
    assert await page.price == "$123"

    item = await page.to_item()
    assert isinstance(item, Item)
    assert item.name == "Hello!"
    assert item.price == "$123"


@pytest.mark.asyncio
async def test_fields_invalid_page() -> None:
    page = InvalidPage(response=EXAMPLE_RESPONSE)
    with pytest.raises(
        TypeError, match="unexpected keyword argument 'unknown_attribute'"
    ):
        await page.to_item()


def test_item_from_fields_sync() -> None:
    @attrs.define
    class Page(ItemPage):
        @field
        def name(self):  # noqa: D102
            return "name"

        def to_item(self):  # noqa: D102
            return item_from_fields_sync(self, dict)

    page = Page()
    assert page.to_item() == dict(name="name")


def test_field_non_callable() -> None:
    with pytest.raises(TypeError):

        @attrs.define
        class Page(ItemPage):
            # https://github.com/python/mypy/issues/1362#issuecomment-438246775
            @field  # type: ignore
            @property
            def name(self):  # noqa: D102
                return "name"

            def to_item(self):  # noqa: D102
                return item_from_fields_sync(self, dict)


def test_field_classmethod() -> None:
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
async def test_field_order() -> None:
    class DictItemPage(Page):
        async def to_item(self):
            return await item_from_fields(self)

    page = DictItemPage(response=EXAMPLE_RESPONSE)
    item = await page.to_item()
    assert item == {"name": "Hello!", "price": "$123"}
    assert list(item.keys()) == ["name", "price"]


def test_field_decorator_no_arguments() -> None:
    class Page(ItemPage):
        @field()
        def name(self):
            return "Name"

        def to_item(self):
            return item_from_fields_sync(self)

    page = Page()
    assert page.to_item() == {"name": "Name"}


def test_field_cache_sync() -> None:
    class Page:
        _n_called_1 = 0
        _n_called_2 = 0

        def __init__(self, name):
            self.name = name

        @field(cached=True)
        def n_called_1(self):
            self._n_called_1 += 1
            return self._n_called_1, self.name

        @field(cached=False)
        def n_called_2(self):
            self._n_called_2 += 1
            return self._n_called_2, self.name

    pages = [Page("first"), Page("second")]
    for page in pages:
        assert page.n_called_1 == (1, page.name)
        assert page.n_called_1 == (1, page.name)

        assert page.n_called_2 == (1, page.name)
        assert page.n_called_2 == (2, page.name)


@pytest.mark.asyncio
async def test_field_cache_async() -> None:
    class Page:
        _n_called_1 = 0
        _n_called_2 = 0

        def __init__(self, name):
            self.name = name

        @field(cached=True)
        async def n_called_1(self):
            self._n_called_1 += 1
            return self._n_called_1, self.name

        @field(cached=False)
        async def n_called_2(self):
            self._n_called_2 += 1
            return self._n_called_2, self.name

    pages = [Page("first"), Page("second")]
    for page in pages:
        assert await page.n_called_1 == (1, page.name)
        assert await page.n_called_1 == (1, page.name)

        assert await page.n_called_2 == (1, page.name)
        assert await page.n_called_2 == (2, page.name)


@pytest.mark.asyncio
async def test_field_cache_async_locked() -> None:
    class Page:
        _n_called = 0

        @field(cached=True)
        async def n_called(self):
            await asyncio.sleep(random.randint(0, 10) / 100.0)
            self._n_called += 1
            return self._n_called

    page = Page()
    results = await asyncio.gather(
        page.n_called,
        page.n_called,
        page.n_called,
        page.n_called,
        page.n_called,
    )
    assert results == [1, 1, 1, 1, 1]


@pytest.mark.asyncio
async def test_skip_nonitem_fields_async() -> None:
    class ExtendedPage(Page):
        @field
        def new_attribute(self):
            return "foo"

    page = ExtendedPage(response=EXAMPLE_RESPONSE)
    with pytest.raises(TypeError, match="unexpected keyword argument 'new_attribute'"):
        await page.to_item()

    class ExtendedPage2(ExtendedPage):
        async def to_item(self) -> Item:
            return await item_from_fields(self, Item, skip_nonitem_fields=True)

    page = ExtendedPage2(response=EXAMPLE_RESPONSE)
    item = await page.to_item()
    assert item == Item(name="Hello!", price="$123")


def test_skip_nonitem_fields() -> None:
    @attrs.define
    class SyncPage(Injectable):
        response: HttpResponse

        @field
        def name(self):  # noqa: D102
            return self.response.css("title ::text").get()

        @field
        def price(self):  # noqa: D102
            return "$123"

        def to_item(self):  # noqa: D102
            return item_from_fields_sync(self, Item)

    class ExtendedPage(SyncPage):
        @field
        def new_attribute(self):
            return "foo"

    page = ExtendedPage(response=EXAMPLE_RESPONSE)
    with pytest.raises(TypeError, match="unexpected keyword argument 'new_attribute'"):
        page.to_item()

    class ExtendedPage2(ExtendedPage):
        def to_item(self) -> Item:
            return item_from_fields_sync(self, Item, skip_nonitem_fields=True)

    page = ExtendedPage2(response=EXAMPLE_RESPONSE)
    item = page.to_item()
    assert item == Item(name="Hello!", price="$123")


def test_field_meta() -> None:
    class MyPage(ItemPage):
        @field(meta={"good": True})
        def field1(self):
            return "foo"

        @field
        def field2(self):
            return "foo"

        def to_item(self):
            return item_from_fields_sync(self)

    page = MyPage()
    for fields in [get_fields_dict(MyPage), get_fields_dict(page)]:
        assert list(fields.keys()) == ["field1", "field2"]
        assert fields["field1"].name == "field1"
        assert fields["field1"].meta == {"good": True}

        assert fields["field2"].name == "field2"
        assert fields["field2"].meta is None


def test_field_subclassing() -> None:
    class Page(ItemPage):
        @field
        def field1(self):
            return 1

        @field
        def field3(self):
            return 1

    assert list(get_fields_dict(Page)) == ["field1", "field3"]
    assert get_fields_dict(Page)["field3"].meta is None

    class Page2(Page):
        @field
        def field2(self):
            return 1

        @field(meta={"foo": "bar"})
        def field3(self):
            return 1

    assert get_fields_dict(Page2)["field3"].meta == {"foo": "bar"}
    assert list(get_fields_dict(Page2)) == ["field1", "field3", "field2"]

    assert get_fields_dict(Page)["field3"].meta is None
    assert list(get_fields_dict(Page)) == ["field1", "field3"]

    class Page3(Page2):
        @field
        def field3(self):
            return 2

    assert get_fields_dict(Page3)["field3"].meta is None
    assert list(get_fields_dict(Page3)) == ["field1", "field3", "field2"]

    assert get_fields_dict(Page)["field3"].meta is None
    assert list(get_fields_dict(Page)) == ["field1", "field3"]

    assert get_fields_dict(Page2)["field3"].meta == {"foo": "bar"}
    assert list(get_fields_dict(Page2)) == ["field1", "field3", "field2"]


def test_field_subclassing_from_to_item() -> None:
    class PageToItem(ItemPage):
        def to_item(self):
            return {"field1": 1, "field2": 2, "field3": 3, "field4": 4}

    class Page1(PageToItem):
        @field
        def field1(self):
            return 0

    # to_item() should be the same since it was not overridden from the
    # subclass.
    page_1 = Page1()
    assert page_1.field1 == 0
    assert page_1.to_item() == {"field1": 1, "field2": 2, "field3": 3, "field4": 4}

    class Page2(PageToItem):
        @field
        def field2(self):
            return 0

        def to_item(self):
            return item_from_fields_sync(self)

    # to_item() only reflects the field from its own class.
    page_2 = Page2()
    assert page_2.field2 == 0
    assert page_2.to_item() == {"field2": 0}


def test_field_with_other_decorators() -> None:
    def clean_str(method):
        def wrapper(*args, **kwargs):
            return method(*args, **kwargs).strip()

        return wrapper

    class MyPage(ItemPage):
        @field
        @clean_str
        def field_foo(self):
            return " foo  \n"

        @field(meta={"good": True})
        @clean_str
        def field_foo_meta(self):
            return " foo  \n"

        @field(cached=True)
        @clean_str
        def field_foo_cached(self):
            return " foo  \n"

    page = MyPage()
    assert page.field_foo == "foo"
    assert page.field_foo_meta == "foo"
    assert page.field_foo_cached == "foo"
