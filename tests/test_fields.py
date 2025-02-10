from __future__ import annotations

import asyncio
import random
from typing import Callable

import attrs
import pytest

from tests.po_lib_to_return import (
    CustomProductPage,
    CustomProductPageDataTypeOnly,
    CustomProductPageNoReturns,
    ImprovedProductPage,
    LessProductPage,
    MoreProductPage,
    Product,
    ProductFewerFields,
    ProductMoreFields,
    ProductPage,
    ProductSimilar,
    SimilarProductPage,
)
from web_poet import (
    HttpResponse,
    ItemPage,
    WebPage,
    field,
    item_from_fields,
    item_from_fields_sync,
)
from web_poet.fields import FieldsMixin, get_fields_dict


@attrs.define
class Item:
    name: str
    price: str


@attrs.define
class Page(ItemPage[Item]):
    response: HttpResponse

    @field
    def name(self):
        return self.response.css("title ::text").get()

    @field
    async def price(self):
        await asyncio.sleep(0.01)
        return "$123"


@attrs.define
class InvalidPage(ItemPage[Item]):
    response: HttpResponse

    @field
    def name(self):
        return self.response.css("title ::text").get()

    @field
    def unknown_attribute(self):
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
        def name(self):
            return "name"

        def to_item(self):
            return item_from_fields_sync(self, dict)

    page = Page()
    assert page.to_item() == {"name": "name"}


def test_field_non_callable() -> None:
    with pytest.raises(TypeError):

        @attrs.define
        class Page(ItemPage):
            # https://github.com/python/mypy/issues/1362#issuecomment-438246775
            @field  # type: ignore[prop-decorator]
            @property
            def name(self):
                return "name"

            def to_item(self):
                return item_from_fields_sync(self, dict)


def test_field_classmethod() -> None:
    with pytest.raises(TypeError):

        @attrs.define
        class Page(ItemPage):
            @field
            @classmethod
            def name(cls):
                return "name"

            def to_item(self):
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
    class Page(ItemPage):
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
    class Page(ItemPage):
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
    class Page(ItemPage):
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
    class SyncPage(ItemPage):
        response: HttpResponse

        @field
        def name(self):
            return self.response.css("title ::text").get()

        @field
        def price(self):
            return "$123"

        def to_item(self) -> Item:  # type: ignore[override]
            return item_from_fields_sync(self, Item)

    class ExtendedPage(SyncPage):
        @field
        def new_attribute(self):
            return "foo"

    page = ExtendedPage(response=EXAMPLE_RESPONSE)
    with pytest.raises(TypeError, match="unexpected keyword argument 'new_attribute'"):
        page.to_item()

    class ExtendedPage2(ExtendedPage):
        def to_item(self) -> Item:  # type: ignore[override]
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


def test_field_subclassing_super() -> None:
    class Page(ItemPage):
        @field
        def field1(self):
            return 1

    class Page2(Page):
        @field
        def field1(self):
            return super().field1 + 1

    page = Page()
    assert page.field1 == 1
    page2 = Page2()
    assert page2.field1 == 2


def test_field_subclassing_from_to_item() -> None:
    # to_item() should be the same since it was not overridden from the
    # subclass.
    class PageToItem(ItemPage):
        def to_item(self):
            return {"field1": 1, "field2": 2, "field3": 3, "field4": 4}

    class Page1(PageToItem):
        @field
        def field1(self):
            return 0

    page_1 = Page1()
    assert page_1.field1 == 0
    assert page_1.to_item() == {"field1": 1, "field2": 2, "field3": 3, "field4": 4}

    # to_item() only reflects the field that was decorated.
    class Page2(PageToItem):
        @field
        def field2(self):
            return 0

        def to_item(self):
            return item_from_fields_sync(self)

    page_2 = Page2()
    assert page_2.field2 == 0
    assert page_2.to_item() == {"field2": 0}

    # to_item() raises an error if there are some required fields from the item_cls
    # that doesn't have a corresponding field value.
    @attrs.define
    class SomeItem:
        field1: int
        field2: int
        field3: int
        field4: int

    class Page3(PageToItem):
        @field
        def field3(self):
            return 0

        def to_item(self):
            return item_from_fields_sync(self, item_cls=SomeItem)

    page_3 = Page3()
    assert page_3.field3 == 0
    with pytest.raises(TypeError):
        page_3.to_item()


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


@pytest.mark.asyncio
async def test_field_with_handle_urls() -> None:
    page = ProductPage()
    assert page.name == "name"
    assert page.price == 12.99
    assert await page.to_item() == Product(name="name", price=12.99)

    page = ImprovedProductPage()
    assert page.name == "improved name"
    assert page.price == 12.99
    assert await page.to_item() == Product(name="improved name", price=12.99)

    page = SimilarProductPage()
    assert page.name == "name"
    assert page.price == 12.99
    assert await page.to_item() == ProductSimilar(name="name", price=12.99)

    page = MoreProductPage()
    assert page.name == "name"
    assert page.price == 12.99
    assert page.brand == "brand"
    assert await page.to_item() == ProductMoreFields(
        name="name", price=12.99, brand="brand"
    )

    page = LessProductPage()
    assert page.name == "name"
    assert await page.to_item() == ProductFewerFields(name="name")

    for page in [  # type: ignore[assignment]
        CustomProductPage(),
        CustomProductPageNoReturns(),
        CustomProductPageDataTypeOnly(),
    ]:
        assert page.name == "name"
        assert page.price == 12.99
        assert await page.to_item() == Product(name="name", price=12.99)


def test_field_processors_sync() -> None:
    def proc1(s):
        return s + "x"

    @attrs.define
    class Page(ItemPage):
        @field(out=[str.strip, proc1])
        def name(self):
            return "  name\t "

    page = Page()
    assert page.name == "namex"


@pytest.mark.asyncio
async def test_field_processors_async() -> None:
    def proc1(s):
        return s + "x"

    @attrs.define
    class Page(ItemPage):
        @field(out=[str.strip, proc1])
        async def name(self):
            return "  name\t "

    page = Page()
    assert await page.name == "namex"


def test_field_processors_inheritance() -> None:
    def proc1(s):
        return s + "x"

    class BasePage(ItemPage):
        @field(out=[str.strip, proc1])
        def name(self):
            return "  name\t "

    class Page(BasePage):
        @field(out=[str.strip])
        def name(self):
            return "  name\t "

    base_page = BasePage()
    assert base_page.name == "namex"
    page = Page()
    assert page.name == "name"


def test_field_processors_page() -> None:
    def proc1(s, page):
        return page.prefix + s + "x"

    class Page(ItemPage):
        @field(out=[str.strip, proc1])
        def name(self):
            return "  name\t "

        @field
        def prefix(self):
            return "prefix: "

    page = Page()
    assert page.name == "prefix: namex"


def test_field_processors_multiple_pages() -> None:
    def proc(value, page):
        return page.body + value

    class Page(WebPage):
        @field
        def body(self):
            return self.response.text

        @field(out=[proc])
        def processed(self):
            return "suffix"

    page1 = Page(response=HttpResponse("https://example.com", b"page1"))
    page2 = Page(response=HttpResponse("https://example.com", b"page2"))
    assert page1.body == "page1"
    assert page1.processed == "page1suffix"
    assert page2.body == "page2"
    assert page2.processed == "page2suffix"


def test_field_processors_circular() -> None:
    def proc1(s, page):
        return s + page.b

    def proc2(s, page):
        return s + page.a

    class Page(ItemPage):
        @field(out=[proc1])
        def a(self):
            return "a"

        @field(out=[proc2])
        def b(self):
            return "b"

    page = Page()
    with pytest.raises(RecursionError):
        page.a
    with pytest.raises(RecursionError):
        page.b


def test_field_processors_default() -> None:
    @attrs.define
    class BasePage(ItemPage):
        class Processors:
            name = [str.strip]

        @field
        def name(self):
            return "  name\t "

    class Page(BasePage):
        pass

    base_page = BasePage()
    assert base_page.name == "name"

    page = Page()
    assert page.name == "name"


def test_field_processors_override() -> None:
    def proc1(s):
        return s + "x"

    class BasePage(ItemPage):
        class Processors:
            f1: list[Callable] = [str.strip]
            f2 = [str.strip]
            f3 = [str.strip]
            f4: list[Callable] = [str.strip]
            f5: list[Callable] = [str.strip]

        @field
        def f1(self):
            return "  f1\t "

        @field(out=[])
        def f2(self):
            return "  f2\t "

        @field
        def f3(self):
            return "  f3\t "

        @field
        def f4(self):
            return "  f4\t "

        @field
        def f5(self):
            return "  f5\t "

    class Page(BasePage):
        class Processors(BasePage.Processors):
            f1 = [proc1]
            f4 = [*BasePage.Processors.f4, proc1]

        @field(out=[*BasePage.Processors.f5, proc1])
        def f5(self):
            return "  f5\t "

    base_page = BasePage()
    assert base_page.f1 == "f1"
    assert base_page.f2 == "  f2\t "
    assert base_page.f3 == "f3"
    assert base_page.f4 == "f4"
    assert base_page.f5 == "f5"

    page = Page()
    assert page.f1 == "  f1\t x"
    assert page.f2 == "  f2\t "
    assert page.f3 == "f3"
    assert page.f4 == "f4x"
    assert page.f5 == "f5x"


def test_field_processors_super() -> None:
    class BasePage(ItemPage):
        class Processors:
            name = [str.strip]
            desc = [str.strip]

        @field
        def name(self):
            return "name "

        @field
        def desc(self):
            return "desc "

    class Page(BasePage):
        class Processors(BasePage.Processors):
            name: list[Callable] = []

        @field
        def name(self):
            base_name = super().name
            return base_name + "2 "

    class Page2(Page):
        class Processors(Page.Processors):
            name: list[Callable] = []
            desc: list[Callable] = []

        @field
        def desc(self):
            base_desc = super().desc
            return base_desc + "2 "

    base_page = BasePage()
    assert base_page.name == "name"
    page = Page()
    assert page.name == "name 2 "
    page2 = Page2()
    assert page2.desc == "desc 2 "


def test_field_processors_builtin() -> None:
    @attrs.define
    class Page(ItemPage):
        @field(out=[int])
        def value(self):
            return "1"

    page = Page()
    assert page.value == 1


def test_field_mixin() -> None:
    class A(ItemPage):
        @field
        def a(self):
            return None

    class Mixin(FieldsMixin):
        @field
        def mixin(self):
            return None

    class B(Mixin, A):
        @field
        def b(self):
            return None

    class C(Mixin, A):
        @field
        def c(self):
            return None

    assert set(get_fields_dict(A)) == {"a"}
    assert set(get_fields_dict(B)) == {"a", "b", "mixin"}
    assert set(get_fields_dict(C)) == {"a", "c", "mixin"}
