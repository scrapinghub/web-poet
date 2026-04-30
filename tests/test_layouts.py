from __future__ import annotations

from typing import Annotated

import attrs
import pytest

from web_poet import HttpResponse, ItemPage, WebPage, field, layout_switch
from web_poet.exceptions import Retry, UseFallback
from web_poet.fields import get_fields_dict


@attrs.define
class NameItem:
    name: str


@attrs.define
class ProductItem:
    title: str
    price: str


class ModuleAnnotatedNameLayout(WebPage[NameItem]):
    @field
    def name(self):
        return "annotated"


class ModuleUnionNameLayoutA(WebPage[NameItem]):
    @field
    def name(self):
        return "union-a"


class ModuleUnionNameLayoutB(WebPage[NameItem]):
    @field
    def name(self):
        return "union-b"


@pytest.mark.asyncio
async def test_layout_switch_default_get_layout() -> None:
    class LayoutA(WebPage[NameItem]):
        @field
        def name(self):
            return "a"

    class LayoutB(WebPage[NameItem]):
        @field
        def name(self):
            return "b"

    @layout_switch()
    @attrs.define
    class ProductPage(ItemPage[NameItem]):
        response: HttpResponse
        layout_a: LayoutA
        layout_b: LayoutB
        switch_calls: int = 0

        async def get_layout(self) -> ItemPage[NameItem]:
            self.switch_calls += 1
            if self.response.css(".layout-a"):
                return self.layout_a
            return self.layout_b

    response = HttpResponse("https://example.com", body=b"<div class='layout-a'></div>")
    page = ProductPage(
        response=response,
        layout_a=LayoutA(response=response),
        layout_b=LayoutB(response=response),
    )

    assert await page.name == "a"  # type: ignore[attr-defined]
    assert await page.name == "a"  # type: ignore[attr-defined]
    assert await page.to_item() == NameItem(name="a")
    assert page.switch_calls == 1


@pytest.mark.asyncio
async def test_layout_switch_without_parentheses() -> None:
    class LayoutA(WebPage[NameItem]):
        @field
        def name(self):
            return "a"

    @layout_switch
    @attrs.define
    class ProductPage(ItemPage[NameItem]):
        response: HttpResponse
        layout_a: LayoutA

        def get_layout(self) -> ItemPage[NameItem]:
            return self.layout_a

    response = HttpResponse("https://example.com", body=b"<html></html>")
    page = ProductPage(response=response, layout_a=LayoutA(response=response))

    assert page.name == "a"  # type: ignore[attr-defined]
    assert await page.to_item() == NameItem(name="a")


@pytest.mark.asyncio
async def test_layout_switch_custom_switch_method_sync() -> None:
    class LayoutA(WebPage[NameItem]):
        @field
        def name(self):
            return "a"

    class LayoutB(WebPage[NameItem]):
        @field
        def name(self):
            return "b"

    @layout_switch(switch_method="pick_layout")
    @attrs.define
    class ProductPage(ItemPage[NameItem]):
        response: HttpResponse
        layout_a: LayoutA
        layout_b: LayoutB
        switch_calls: int = 0

        def pick_layout(self) -> ItemPage[NameItem]:
            self.switch_calls += 1
            if self.response.css(".layout-a"):
                return self.layout_a
            return self.layout_b

    response = HttpResponse("https://example.com", body=b"<div class='layout-a'></div>")
    page = ProductPage(
        response=response,
        layout_a=LayoutA(response=response),
        layout_b=LayoutB(response=response),
    )

    assert page.name == "a"  # type: ignore[attr-defined]
    assert page.name == "a"  # type: ignore[attr-defined]
    assert await page.to_item() == NameItem(name="a")
    assert page.switch_calls == 1


@pytest.mark.asyncio
async def test_layout_switch_layout_priority_with_page_fallback() -> None:
    class LayoutA(WebPage[ProductItem]):
        @field
        def title(self):
            return "title-a"

        @field
        def price(self):
            return "$10"

    class LayoutB(WebPage[ProductItem]):
        @field
        def title(self):
            return "title-b"

    @layout_switch()
    @attrs.define
    class ProductPage(ItemPage[ProductItem]):
        response: HttpResponse
        layout_a: LayoutA
        layout_b: LayoutB

        def get_layout(self) -> ItemPage[ProductItem]:
            if self.response.css(".layout-a"):
                return self.layout_a
            return self.layout_b

        @field
        def price(self):
            return "$42"

        @field
        def title(self):
            return "title-fallback"

    response_a = HttpResponse(
        "https://example.com/a", body=b"<div class='layout-a'></div>"
    )
    response_b = HttpResponse("https://example.com/b", body=b"<html></html>")

    page_a = ProductPage(
        response=response_a,
        layout_a=LayoutA(response=response_a),
        layout_b=LayoutB(response=response_a),
    )
    page_b = ProductPage(
        response=response_b,
        layout_a=LayoutA(response=response_b),
        layout_b=LayoutB(response=response_b),
    )

    fields = get_fields_dict(ProductPage)
    assert set(fields.keys()) == {"price", "title"}
    assert await page_a.to_item() == ProductItem(title="title-a", price="$10")
    assert await page_b.to_item() == ProductItem(title="title-b", price="$42")


def test_layout_switch_default_uses_item_type_fields() -> None:
    @attrs.define
    class TitleOnlyItem:
        title: str

    class LayoutA(WebPage[TitleOnlyItem]):
        @field
        def title(self):
            return "title-a"

        @field
        def price(self):
            return "$10"

    class LayoutB(WebPage[TitleOnlyItem]):
        @field
        def title(self):
            return "title-b"

    @layout_switch()
    @attrs.define
    class ProductPage(ItemPage[TitleOnlyItem]):
        response: HttpResponse
        layout_a: LayoutA
        layout_b: LayoutB

        def get_layout(self) -> ItemPage[TitleOnlyItem]:
            return self.layout_a

    fields = get_fields_dict(ProductPage)
    assert "title" in fields
    assert "price" not in fields


def test_layout_switch_missing_switch_method() -> None:
    class LayoutA(WebPage[NameItem]):
        @field
        def name(self):
            return "a"

    with pytest.raises(
        AttributeError, match=r"'ProductPage' has no attribute 'get_layout'"
    ):

        @layout_switch()
        @attrs.define
        class ProductPage(ItemPage[NameItem]):
            response: HttpResponse
            layout_a: LayoutA


@pytest.mark.asyncio
async def test_layout_switch_does_not_require_layout_annotations() -> None:
    class LayoutA(WebPage[NameItem]):
        @field
        def name(self):
            return "a"

    @layout_switch()
    @attrs.define
    class ProductPage(ItemPage[NameItem]):
        response: HttpResponse
        layout_value: object

        def get_layout(self):
            return self.layout_value

    response = HttpResponse("https://example.com", body=b"<html></html>")
    page = ProductPage(response=response, layout_value=LayoutA(response=response))
    assert page.name == "a"  # type: ignore[attr-defined]
    assert await page.to_item() == NameItem(name="a")


def test_layout_switch_requires_explicit_layouts_for_dict_items() -> None:
    with pytest.raises(
        ValueError, match="output item type does not expose field names"
    ):

        @layout_switch()
        class ProductPage(ItemPage[dict]):
            def get_layout(self):
                return self


@pytest.mark.asyncio
async def test_layout_switch_supports_dict_items_with_explicit_layouts() -> None:
    class LayoutA(WebPage[dict]):
        @field
        def name(self):
            return "a"

    @layout_switch(layouts=[LayoutA])
    @attrs.define
    class ProductPage(ItemPage[dict]):
        response: HttpResponse
        layout_a: LayoutA

        def get_layout(self):
            return self.layout_a

    response = HttpResponse("https://example.com", body=b"<html></html>")
    page = ProductPage(response=response, layout_a=LayoutA(response=response))

    fields = get_fields_dict(ProductPage)
    assert set(fields.keys()) == {"name"}
    assert page.name == "a"  # type: ignore[attr-defined]
    assert await page.to_item() == {"name": "a"}


def test_layout_switch_explicit_layouts_use_layout_union() -> None:
    @attrs.define
    class TitleOnlyItem:
        title: str

    class LayoutA(WebPage[TitleOnlyItem]):
        @field
        def title(self):
            return "title-a"

        @field
        def price(self):
            return "$10"

    class LayoutB(WebPage[TitleOnlyItem]):
        @field
        def title(self):
            return "title-b"

    @layout_switch(layouts=[LayoutA, LayoutB])
    @attrs.define
    class ProductPage(ItemPage[TitleOnlyItem]):
        response: HttpResponse
        layout_a: LayoutA
        layout_b: LayoutB

        def get_layout(self) -> ItemPage[TitleOnlyItem]:
            return self.layout_a

    fields = get_fields_dict(ProductPage)
    assert "title" in fields
    assert "price" in fields


@pytest.mark.asyncio
async def test_layout_switch_discovers_module_layout_hints_with_annotated_and_union() -> (
    None
):
    @layout_switch()
    @attrs.define
    class ProductPage(ItemPage[NameItem]):
        response: HttpResponse
        annotated_layout: Annotated[ModuleAnnotatedNameLayout, "primary"]
        duplicate_layout: ModuleAnnotatedNameLayout
        variant_layout: ModuleUnionNameLayoutA | ModuleUnionNameLayoutB

        def get_layout(self) -> ItemPage[NameItem]:
            if self.response.css(".variant"):
                return self.variant_layout
            return self.annotated_layout

    response_default = HttpResponse(
        "https://example.com/default", body=b"<html></html>"
    )
    page_default = ProductPage(
        response=response_default,
        annotated_layout=ModuleAnnotatedNameLayout(response=response_default),
        duplicate_layout=ModuleAnnotatedNameLayout(response=response_default),
        variant_layout=ModuleUnionNameLayoutB(response=response_default),
    )

    assert page_default.name == "annotated"  # type: ignore[attr-defined]
    assert await page_default.to_item() == NameItem(name="annotated")

    response_variant = HttpResponse(
        "https://example.com/variant", body=b"<div class='variant'></div>"
    )
    page_variant = ProductPage(
        response=response_variant,
        annotated_layout=ModuleAnnotatedNameLayout(response=response_variant),
        duplicate_layout=ModuleAnnotatedNameLayout(response=response_variant),
        variant_layout=ModuleUnionNameLayoutA(response=response_variant),
    )

    assert page_variant.name == "union-a"  # type: ignore[attr-defined]
    assert await page_variant.to_item() == NameItem(name="union-a")


@pytest.mark.asyncio
async def test_layout_switch_forwards_async_layout_field_with_sync_switch() -> None:
    class AsyncNameLayout(WebPage[NameItem]):
        @field
        async def name(self):
            return "async-name"

    @layout_switch(layouts=[AsyncNameLayout])
    @attrs.define
    class ProductPage(ItemPage[NameItem]):
        response: HttpResponse
        layout_a: AsyncNameLayout
        switch_calls: int = 0

        def get_layout(self) -> ItemPage[NameItem]:
            self.switch_calls += 1
            return self.layout_a

    response = HttpResponse("https://example.com", body=b"<html></html>")
    page = ProductPage(response=response, layout_a=AsyncNameLayout(response=response))

    assert await page.name == "async-name"  # type: ignore[attr-defined]
    assert await page.name == "async-name"  # type: ignore[attr-defined]
    assert await page.to_item() == NameItem(name="async-name")
    assert page.switch_calls == 1


@pytest.mark.asyncio
async def test_layout_switch_runs_main_input_validation_before_switch() -> None:
    class LayoutA(WebPage[NameItem]):
        @field
        def name(self):
            return "a"

    @layout_switch()
    @attrs.define
    class ProductPage(ItemPage[NameItem]):
        response: HttpResponse
        layout_a: LayoutA
        switch_calls: int = 0

        def validate_input(self):
            raise Retry

        def get_layout(self) -> ItemPage[NameItem]:
            self.switch_calls += 1
            return self.layout_a

    response = HttpResponse("https://example.com", body=b"<html></html>")
    page = ProductPage(response=response, layout_a=LayoutA(response=response))
    with pytest.raises(Retry):
        await page.name  # type: ignore[attr-defined]
    assert page.switch_calls == 0


@pytest.mark.asyncio
async def test_layout_switch_runs_selected_layout_validation() -> None:
    class LayoutA(WebPage[NameItem]):
        def validate_input(self):
            raise UseFallback

        @field
        def name(self):
            return "a"

    @layout_switch()
    @attrs.define
    class ProductPage(ItemPage[NameItem]):
        response: HttpResponse
        layout_a: LayoutA

        def get_layout(self) -> ItemPage[NameItem]:
            return self.layout_a

    response = HttpResponse("https://example.com", body=b"<html></html>")
    page = ProductPage(response=response, layout_a=LayoutA(response=response))
    with pytest.raises(UseFallback):
        await page.name  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_layout_switch_raises_without_layout_field_or_page_fallback() -> None:
    @attrs.define
    class TitlePriceItem:
        title: str
        price: str

    class LayoutA(WebPage[TitlePriceItem]):
        @field
        def title(self):
            return "title-a"

    class LayoutB(WebPage[TitlePriceItem]):
        @field
        def title(self):
            return "title-b"

        @field
        def price(self):
            return "$11"

    @layout_switch()
    @attrs.define
    class ProductPage(ItemPage[TitlePriceItem]):
        response: HttpResponse
        layout_a: LayoutA
        layout_b: LayoutB

        def get_layout(self) -> ItemPage[TitlePriceItem]:
            return self.layout_a

    response = HttpResponse("https://example.com", body=b"<html></html>")
    page = ProductPage(
        response=response,
        layout_a=LayoutA(response=response),
        layout_b=LayoutB(response=response),
    )

    with pytest.raises(AttributeError, match="does not define field 'price'"):
        await page.price  # type: ignore[attr-defined]
