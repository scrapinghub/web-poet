import asyncio
import random
import warnings
from collections import defaultdict
from typing import DefaultDict, Optional

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
    Injectable,
    ItemPage,
    SelectFields,
    field,
    item_from_fields,
    item_from_fields_sync,
)
from web_poet.fields import FieldInfo, get_fields_dict


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
        def name(self):  # noqa: D102
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
        async def name(self):  # noqa: D102
            return "  name\t "

    page = Page()
    assert await page.name == "namex"


def test_field_mixin() -> None:
    class A(ItemPage):
        @field
        def a(self):
            return None

    class Mixin:
        @field
        def mixin(self):
            return None

    class B(Mixin, A):
        @field
        def b(self):
            return None

    assert set(get_fields_dict(B)) == {"a", "b", "mixin"}


@pytest.mark.asyncio
async def test_field_disabled() -> None:
    @attrs.define
    class Item:
        x: int
        y: Optional[int] = None
        z: Optional[int] = None

    class Page(ItemPage[Item]):
        @field
        def x(self) -> int:
            return 1

        @field(disabled=False)
        def y(self) -> int:
            return 2

        @field(disabled=True)
        def z(self) -> int:
            return 3

    page = Page()
    assert await page.to_item() == Item(x=1, y=2)
    assert page.x == 1
    assert page.y == 2
    assert page.z == 3

    fields_dict_instance = get_fields_dict(page)
    fields_dict_class = get_fields_dict(Page)

    for info in [fields_dict_class, fields_dict_instance]:
        assert info["x"] == FieldInfo(name="x", meta=None, out=None, disabled=False)
        assert info["y"] == FieldInfo(name="y", meta=None, out=None, disabled=False)

    fields_dict_instance = get_fields_dict(page, include_disabled=True)
    fields_dict_class = get_fields_dict(Page, include_disabled=True)

    for info in [fields_dict_class, fields_dict_instance]:
        assert info["x"] == FieldInfo(name="x", meta=None, out=None, disabled=False)
        assert info["y"] == FieldInfo(name="y", meta=None, out=None, disabled=False)
        assert info["z"] == FieldInfo(name="z", meta=None, out=None, disabled=True)

    # The subclass should properly reflect any changes to the ``disable`` value

    class SubPage(Page):
        """Flicks the switch for ``y`` and ``z``."""

        @field(disabled=True)
        def y(self) -> int:
            return 2

        @field(disabled=False)
        def z(self) -> int:
            return 3

    subpage = SubPage()
    assert await subpage.to_item() == Item(x=1, z=3)
    assert subpage.x == 1
    assert subpage.y == 2
    assert subpage.z == 3

    fields_dict_instance = get_fields_dict(subpage)
    fields_dict_class = get_fields_dict(SubPage)

    for info in [fields_dict_class, fields_dict_instance]:
        assert info["x"] == FieldInfo(name="x", meta=None, out=None, disabled=False)
        assert info["z"] == FieldInfo(name="z", meta=None, out=None, disabled=False)

    fields_dict_instance = get_fields_dict(subpage, include_disabled=True)
    fields_dict_class = get_fields_dict(SubPage, include_disabled=True)

    for info in [fields_dict_class, fields_dict_instance]:
        assert info["x"] == FieldInfo(name="x", meta=None, out=None, disabled=False)
        assert info["y"] == FieldInfo(name="y", meta=None, out=None, disabled=True)
        assert info["z"] == FieldInfo(name="z", meta=None, out=None, disabled=False)

    # Disabling fields that are required in the item cls would error out.

    class BadSubPage(Page):
        @field(disabled=True)
        def x(self) -> int:
            return 1

    badsubpage = BadSubPage()

    with pytest.raises(TypeError):
        await badsubpage.to_item()

    assert badsubpage.x == 1
    assert badsubpage.y == 2
    assert badsubpage.z == 3

    fields_dict_instance = get_fields_dict(badsubpage)
    fields_dict_class = get_fields_dict(BadSubPage)

    for info in [fields_dict_class, fields_dict_instance]:
        assert info["y"] == FieldInfo(name="y", meta=None, out=None, disabled=False)

    fields_dict_instance = get_fields_dict(badsubpage, include_disabled=True)
    fields_dict_class = get_fields_dict(BadSubPage, include_disabled=True)

    for info in [fields_dict_class, fields_dict_instance]:
        assert info["x"] == FieldInfo(name="x", meta=None, out=None, disabled=True)
        assert info["y"] == FieldInfo(name="y", meta=None, out=None, disabled=False)
        assert info["z"] == FieldInfo(name="z", meta=None, out=None, disabled=True)


@attrs.define
class BigItem:
    x: int
    y: Optional[int] = None
    z: Optional[int] = None


@attrs.define
class SmallItem:
    """Same with ``BigItem`` but removes the required ``x`` field."""

    y: Optional[int] = None
    z: Optional[int] = None


@attrs.define
class BigPage(ItemPage[BigItem]):
    select_fields: Optional[SelectFields] = None
    call_counter: DefaultDict = attrs.field(factory=lambda: defaultdict(int))

    @field
    def x(self):
        self.call_counter["x"] += 1
        return 1

    @field
    def y(self):
        self.call_counter["y"] += 1
        return 2

    @field
    def z(self):
        self.call_counter["z"] += 1
        return 3


@pytest.mark.asyncio
async def test_select_fields_include() -> None:
    # Basic case
    page = BigPage(SelectFields(include=["x", "y"]))
    item = await page.to_item()
    assert item == BigItem(x=1, y=2, z=None)
    assert page.call_counter == {"x": 1, "y": 1}

    # Repeated fields are ignored
    page = BigPage(SelectFields(include=["x", "x"]))
    item = await page.to_item()
    assert item == BigItem(x=1, y=None, z=None)
    assert page.call_counter == {"x": 1}

    # Passing None value results in all fields to be extracted.
    # Note that this is different when [] is passed. See test below.
    page = BigPage(SelectFields(include=None))
    item = await page.to_item()
    assert item == BigItem(x=1, y=2, z=3)
    assert page.call_counter == {"x": 1, "y": 1, "z": 1}

    # Required fields from the item cls which are not included raise an TypeError
    expected_type_error_msg = (
        r"__init__\(\) missing 1 required positional argument: 'x'"
    )
    page = BigPage(SelectFields(include=[]))
    with pytest.raises(TypeError, match=expected_type_error_msg):
        item = await page.to_item()
    assert page.call_counter == {}

    page = BigPage(SelectFields(include=["y", "z"]))
    with pytest.raises(TypeError, match=expected_type_error_msg):
        await page.to_item()
    assert page.call_counter == {"y": 1, "z": 1}

    # The remaining tests below checks the different behaviors when encountering a
    # field which doesn't existing in the PO
    fields = ["x", "not_existing"]
    expected_attribute_error_msg = (
        "Field 'not_existing' isn't available in tests.test_fields.BigPage"
    )

    # Unknown field raises an AttributeError by default
    page = BigPage(SelectFields(include=fields))
    with pytest.raises(AttributeError, match=expected_attribute_error_msg):
        await page.to_item()

    page = BigPage(SelectFields(include=fields, on_unknown_field="raise"))
    with pytest.raises(AttributeError, match=expected_attribute_error_msg):
        await page.to_item()

    # It should safely ignore it if page object has set skip_nonitem_fields
    page = BigPage(SelectFields(include=fields, on_unknown_field="ignore"))
    with warnings.catch_warnings(record=True) as caught_warnings:
        item = await page.to_item()
        assert item == BigItem(x=1, y=None, z=None)
        assert not caught_warnings
    assert page.call_counter == {"x": 1}

    # When 'warn' is used, the same msg when 'raise' is used.
    page = BigPage(SelectFields(include=fields, on_unknown_field="warn"))
    with warnings.catch_warnings(record=True) as caught_warnings:
        item = await page.to_item()
        assert item == BigItem(x=1, y=None, z=None)
        assert any(
            [
                True
                for w in caught_warnings
                if expected_attribute_error_msg in str(w.message)
            ]
        )
    assert page.call_counter == {"x": 1}


@pytest.mark.asyncio
async def test_select_fields_on_unknown_field_bad_value() -> None:
    # When SelectFields receive an invalid 'on_unknown_field' value, it should
    # error out as well.
    invalid_val = "invalid val"
    expected_value_error_msg = (
        f"web_poet.SelectFields only accepts 'ignore', 'warn', and 'raise' "
        f"values. Received unrecognized '{invalid_val}' value which it treats as "
        f"'ignore'."
    )
    with pytest.raises(ValueError, match=expected_value_error_msg):
        await BigPage(
            # ignore mypy error since it's expecting a value inside the Literal.
            SelectFields(include=["y", "not_existing"], on_unknown_field=invalid_val)  # type: ignore[arg-type]
        ).to_item()


@pytest.mark.asyncio
async def test_select_fields_exclude() -> None:
    # Basic case
    page = BigPage(SelectFields(exclude=["y", "z"]))
    item = await page.to_item()
    assert item == BigItem(x=1, y=None, z=None)
    assert page.call_counter == {"x": 1}

    # Repeated fields are ignored
    page = BigPage(SelectFields(exclude=["y", "y"]))
    item = await page.to_item()
    assert item == BigItem(x=1, y=None, z=3)
    assert page.call_counter == {"x": 1, "z": 1}

    # A value of None would return all fields
    page = BigPage(SelectFields(exclude=None))
    item = await page.to_item()
    assert item == BigItem(x=1, y=2, z=3)
    assert page.call_counter == {"x": 1, "y": 1, "z": 1}

    # Using an empty list returns all fields
    page = BigPage(SelectFields(exclude=[]))
    item = await page.to_item()
    assert item == BigItem(x=1, y=2, z=3)
    assert page.call_counter == {"x": 1, "y": 1, "z": 1}

    # Required fields from the item cls which are not included raise an TypeError
    expected_type_error_msg = (
        r"__init__\(\) missing 1 required positional argument: 'x'"
    )
    with pytest.raises(TypeError, match=expected_type_error_msg):
        page = BigPage(SelectFields(exclude=["x"]))
        await page.to_item()
        assert page.call_counter == {"y": 1, "z": 1}

    # Unlike the test setup in ``test_select_fields_include()``, we don't
    # expect any errors here since 'exclude' actually removes them. However, if
    # include and exclude were used together, and include introduced an unknown
    # field which exclude hasn't removed, it should err out.
    # See ``test_select_fields_include_exclude()``.
    fields = ["y", "not_existing"]

    page = BigPage(SelectFields(exclude=fields))
    item = await page.to_item()
    assert item == BigItem(x=1, y=None, z=3)
    assert page.call_counter == {"x": 1, "z": 1}

    page = BigPage(SelectFields(exclude=fields, on_unknown_field="raise"))
    item = await page.to_item()
    assert item == BigItem(x=1, y=None, z=3)
    assert page.call_counter == {"x": 1, "z": 1}

    page = BigPage(SelectFields(exclude=fields, on_unknown_field="ignore"))
    item = await page.to_item()
    assert item == BigItem(x=1, y=None, z=3)
    assert page.call_counter == {"x": 1, "z": 1}

    with warnings.catch_warnings(record=True) as caught_warnings:
        page = BigPage(SelectFields(exclude=fields, on_unknown_field="warn"))
        item = await page.to_item()
        assert item == BigItem(x=1, y=None, z=3)
        assert not caught_warnings
    assert page.call_counter == {"x": 1, "z": 1}


@pytest.mark.asyncio
async def test_select_fields_include_exclude() -> None:
    page = BigPage(SelectFields(include=["x", "y"], exclude=["y"]))
    item = await page.to_item()
    assert item == BigItem(x=1, y=None, z=None)
    assert page.call_counter == {"x": 1}

    # If the fields cancel out, then any required field should error out.
    expected_type_error_msg = (
        r"__init__\(\) missing 1 required positional argument: 'x'"
    )
    page = BigPage(SelectFields(include=["x", "y"], exclude=["x", "y"]))
    with pytest.raises(TypeError, match=expected_type_error_msg):
        item = await page.to_item()
    assert page.call_counter == {}

    page = BigPage(
        SelectFields(include=["x", "not_existing"], exclude=["not_existing"])
    )
    item = await page.to_item()
    assert item == BigItem(x=1, y=None, z=None)
    assert page.call_counter == {"x": 1}

    page = BigPage(SelectFields(include=["x", "y", "not_existing"], exclude=["y"]))
    expected_attribute_error_msg = (
        "Field 'not_existing' isn't available in tests.test_fields.BigPage"
    )
    with pytest.raises(AttributeError, match=expected_attribute_error_msg):
        await page.to_item()

    page = BigPage(SelectFields(include=None, exclude=["y"]))
    item = await page.to_item()
    assert item == BigItem(x=1, y=None, z=3)
    assert page.call_counter == {"x": 1, "z": 1}

    page = BigPage(SelectFields(include=None, exclude=None))
    item = await page.to_item()
    assert item == BigItem(x=1, y=2, z=3)
    assert page.call_counter == {"x": 1, "y": 1, "z": 1}

    page = BigPage(SelectFields(include=None, exclude=[]))
    item = await page.to_item()
    assert item == BigItem(x=1, y=2, z=3)
    assert page.call_counter == {"x": 1, "y": 1, "z": 1}

    for exclude in (["y"], [], None):
        # Ignore some of the types below since mypy is not expecting an empty list

        page = BigPage(SelectFields(include=[], exclude=exclude))  # type: ignore[arg-type]
        with pytest.raises(TypeError, match=expected_type_error_msg):
            item = await page.to_item()
        assert page.call_counter == {}

        page = BigPage(SelectFields(include=["x", "z"], exclude=exclude))  # type: ignore[arg-type]
        item = await page.to_item()
        assert item == BigItem(x=1, y=None, z=3)
        assert page.call_counter == {"x": 1, "z": 1}


@pytest.mark.asyncio
async def test_select_fields_swap_item_cls() -> None:
    # Basic case
    page = BigPage(SelectFields(exclude=["x"], swap_item_cls=SmallItem))
    item = await page.to_item()
    assert item == SmallItem(y=2, z=3)
    assert page.call_counter == {"y": 1, "z": 1}

    page = BigPage(SelectFields(include=["y", "z"], swap_item_cls=SmallItem))
    item = await page.to_item()
    assert item == SmallItem(y=2, z=3)
    assert page.call_counter == {"y": 1, "z": 1}

    # If page object supplies the new item class with unknown fields, it should
    # raise an error
    expected_type_error_msg = r"__init__\(\) got an unexpected keyword argument 'x'"
    page = BigPage(SelectFields(swap_item_cls=SmallItem))
    with pytest.raises(TypeError, match=expected_type_error_msg):
        await page.to_item()
