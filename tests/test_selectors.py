from __future__ import annotations

import asyncio
import gc
from functools import partial
from types import SimpleNamespace
from typing import Any

import andi
import attrs
import frostwork
import parsel
import pytest

from web_poet import (
    AnyResponse,
    BrowserPage,
    BrowserResponse,
    HttpClient,
    HttpResponse,
    ItemPage,
    Returns,
    SelectorExtractor,
    SelectorGroup,
    WebPage,
    css_get,
    css_getall,
    field,
    layout_switch,
    xpath_get,
    xpath_getall,
)
from web_poet import _frostwork as _frostwork_module
from web_poet._frostwork import _get_page
from web_poet._selectors import _get_selectors_dict
from web_poet.mixins import ResponseShortcutsMixin
from web_poet.pages import is_injectable
from web_poet.testing import Fixture

HTML = """
<html>
  <head><meta itemprop="brand" content="Acme"></head>
  <body>
    <h1> Foo </h1>
    <p class="price">10.00</p>
    <img src="a.png"><img src="b.png">
    <div class="sku">SKU-1</div>
    <div class="desc">A description</div>
  </body>
</html>
"""


@pytest.fixture
def response():
    return HttpResponse("http://example.com", HTML.encode("utf-8"), encoding="utf-8")


@attrs.define
class Page(WebPage):
    name = field(css_get("h1::text"))
    images = field(css_getall("img::attr(src)"))
    brand = field(xpath_get("//meta[@itemprop='brand']/@content"))
    sources = field(xpath_getall("//img/@src"))
    missing = field(css_get(".missing::text"))
    missing_all = field(css_getall(".missing::text"))

    _sku_a = css_get(".sku::text")
    _sku_b = xpath_get("//meta[@name='sku']/@content")

    @field
    def sku(self) -> str | None:
        return self._sku_a or self._sku_b

    @field
    def description(self) -> str | None:
        return self.css(".desc::text").get()


def test_values(response) -> None:
    page = Page(response=response)
    assert page.name == " Foo "
    assert page.images == ["a.png", "b.png"]
    assert page.brand == "Acme"
    assert page.sources == ["a.png", "b.png"]
    assert page.missing is None
    assert page.missing_all == []
    assert page.sku == "SKU-1"
    assert page.description == "A description"


def test_to_item(response) -> None:
    assert asyncio.run(Page(response=response).to_item()) == {
        "name": " Foo ",
        "images": ["a.png", "b.png"],
        "brand": "Acme",
        "sources": ["a.png", "b.png"],
        "missing": None,
        "missing_all": [],
        "sku": "SKU-1",
        "description": "A description",
    }


def test_declaration_not_a_field(response) -> None:
    """A bare declaration attribute is readable, but is not an item field."""
    assert "_sku_a" not in asyncio.run(Page(response=response).to_item())


def test_get_selectors_dict_before_instantiation() -> None:
    declarations = _get_selectors_dict(Page)
    assert set(declarations) == {
        "name",
        "images",
        "brand",
        "sources",
        "missing",
        "missing_all",
        "_sku_a",
        "_sku_b",
    }
    assert declarations["name"].expression == "h1::text"
    assert declarations["images"].mode == "getall"
    assert declarations["name"].mode == "get"


def test_class_access() -> None:
    """Accessing a declaration on the class returns the declaration."""
    assert _get_selectors_dict(Page)["_sku_a"] is Page._sku_a


def test_equality() -> None:
    """Declarations of the same query are interchangeable."""
    assert css_get("h1::text") == css_get("h1::text")
    assert css_get("h1::text") != css_getall("h1::text")
    assert css_get("h1::text") != css_get("h2::text")
    assert css_get("h1") != xpath_get("h1")
    assert css_get("h1::text") != "h1::text"


def test_equal_declarations(response) -> None:
    """Equal declarations of different attributes are extracted once."""

    @attrs.define
    class TwinPage(WebPage):
        a = field(css_get(".price::text"))
        b = field(css_get(".price::text"))

    page = TwinPage(response=response)
    assert page.a == page.b == "10.00"
    result = _get_page(TwinPage)
    assert result is not None
    assert list(result[1].values()) == ["a"]


def test_repr() -> None:
    assert repr(css_getall("img::attr(src)")) == "css_getall('img::attr(src)')"


def test_extraction_is_eager(response) -> None:
    """Reading one declaration extracts every other declaration in the same
    pass."""
    page = Page(response=response)
    assert page.name == " Foo "
    assert page._selector_values() == {
        declaration: getattr(page, name)
        for name, declaration in _get_selectors_dict(Page).items()
    }


def test_unsupported_declaration() -> None:
    with pytest.raises(TypeError, match=r"name = ':root h1::text'"):

        class UnsupportedPage(WebPage):
            name = field(css_get(":root h1::text"))
            brand = field(xpath_get("//meta[@itemprop='brand']/@content"))


@pytest.mark.parametrize(
    "declaration", [css_get("::::"), css_get("h1::txt"), xpath_get("//h1[")]
)
def test_invalid_expression(declaration) -> None:
    with pytest.raises(TypeError, match="frostwork cannot extract"):

        class InvalidPage(WebPage):
            name = field(declaration)


def test_over_budget() -> None:
    with pytest.raises(TypeError, match="over budget"):

        class OverBudgetPage(WebPage):
            # Every comma-separated selector counts towards the budget, which
            # is 128 selectors at the time of writing.
            name = field(css_get(", ".join(["h1::text"] * 129)))


def test_additional_request(response) -> None:
    """Declarations apply to the response of their page object class. A page
    object class of its own gives the response of an additional request its own
    declarations."""

    async def download(request):
        return HttpResponse(request.url, b"<h1>Bar</h1>", encoding="utf-8")

    @attrs.define
    class OtherPage(WebPage):
        name = field(css_get("h1::text"))

    @attrs.define
    class MainPage(Page):
        http: HttpClient

        @field
        async def other_name(self) -> str | None:
            response = await self.http.get("http://example.com/other")
            return OtherPage(response=response).name

    page = MainPage(response=response, http=HttpClient(download))
    assert page.name == " Foo "
    assert asyncio.run(page.other_name) == "Bar"


class SkuSelectors(SelectorGroup):
    meta = xpath_get("//meta[@itemprop='sku']/@content")
    text = css_get(".sku::text")


@attrs.define
class GroupPage(WebPage):
    skus: SkuSelectors

    @field
    def sku(self) -> str | None:
        return self.skus.meta or self.skus.text


@attrs.define
class BrowserGroupPage(BrowserPage):
    skus: SkuSelectors

    @field
    def sku(self) -> str | None:
        return self.skus.meta or self.skus.text


@pytest.mark.parametrize(
    ("page_cls", "response", "document_type"),
    [
        (
            GroupPage,
            HttpResponse("http://example.com", HTML.encode(), encoding="utf-8"),
            bytes,
        ),
        (
            BrowserGroupPage,
            BrowserResponse(url="http://example.com", html=HTML),
            str,
        ),
    ],
)
def test_selector_group(page_cls, response, document_type) -> None:
    """A selector group can be built through dependency injection, and reads
    the response of the page object."""
    plan = andi.plan(
        page_cls,
        is_injectable=is_injectable,
        externally_provided={type(response), AnyResponse},
    )
    instances: dict[Any, Any] = {
        type(response): response,
        AnyResponse: AnyResponse(response=response),
    }
    for cls, kwargs in plan:
        if cls not in instances:
            instances[cls] = cls(**{k: instances[v] for k, v in kwargs.items()})
    page = instances[page_cls]
    assert isinstance(page, page_cls)
    assert asyncio.run(page.to_item()) == {"sku": "SKU-1"}
    assert isinstance(page.skus._selector_document()[0], document_type)


def test_selector_group_other_document(monkeypatch) -> None:
    """A page object without declarations does not decode its document for a
    selector group that reads another one."""

    def decodes_as_declared(document):
        assert isinstance(document[0], str)
        return _frostwork_module._decodes_as_declared(document)

    monkeypatch.setattr("web_poet.mixins._decodes_as_declared", decodes_as_declared)
    browser_response = BrowserResponse(url="http://example.com", html=HTML)
    page = GroupPage(
        response=HttpResponse("http://example.com", HTML.encode(), encoding="cp437"),
        skus=SkuSelectors(AnyResponse(response=browser_response)),
    )
    assert page.sku == "SKU-1"


@pytest.fixture
def passes(monkeypatch) -> list[Any]:
    """Return a list that gets an item for each frostwork pass."""
    calls: list[Any] = []

    def counting_extract(*args):
        calls.append(args)
        return _frostwork_module._extract(*args)

    monkeypatch.setattr("web_poet.mixins._frostwork_extract", counting_extract)
    return calls


@attrs.define
class MixedPage(GroupPage):
    name = field(css_get("h1::text"))


@pytest.mark.parametrize("group_first", [False, True])
def test_selector_group_single_pass(passes, response, group_first) -> None:
    """The declarations of a page object and of its selector groups are
    extracted in a single pass, whichever is read first."""
    page = MixedPage(response=response, skus=SkuSelectors(AnyResponse(response)))
    if group_first:
        assert page.skus.text == "SKU-1"
    assert asyncio.run(page.to_item()) == {"sku": "SKU-1", "name": " Foo "}
    assert len(passes) == 1


@pytest.mark.parametrize("inner_first", [False, True])
def test_nested_dependency_single_pass(passes, response, inner_first) -> None:
    @attrs.define
    class OuterPage(WebPage):
        inner: GroupPage
        name = field(css_get("h1::text"))

        @field
        def sku(self) -> str | None:
            return self.inner.skus.text

    inner = GroupPage(response, SkuSelectors(AnyResponse(response)))
    page = OuterPage(response=response, inner=inner)
    if inner_first:
        assert inner.sku == "SKU-1"
    assert asyncio.run(page.to_item()) == {"name": " Foo ", "sku": "SKU-1"}
    assert len(passes) == 1


@attrs.define
class PricePage(WebPage):
    price = field(css_get(".price::text"))


@pytest.mark.parametrize("price_first", [False, True])
def test_unrelated_page_objects_single_pass(passes, response, price_first) -> None:
    """Page objects over the same response share a single pass, even if
    neither depends on the other."""
    page = MixedPage(response=response, skus=SkuSelectors(AnyResponse(response)))
    price_page = PricePage(response=response)
    if price_first:
        assert price_page.price == "10.00"
    assert page.name == " Foo "
    assert price_page.price == "10.00"
    assert len(passes) == 1


def test_other_response_other_pass(passes) -> None:
    """Page objects over different response objects get a pass each, even if
    the responses are equal."""
    pages = [
        PricePage(HttpResponse("http://example.com", HTML.encode(), encoding="utf-8"))
        for _ in range(2)
    ]
    assert [page.price for page in pages] == ["10.00", "10.00"]
    assert len(passes) == 2


def test_page_object_built_after_the_pass(passes, response) -> None:
    """A page object built after the first read over its response gets a pass
    of its own."""
    page = PricePage(response=response)
    assert page.price == "10.00"
    assert PricePage(response=response).price == "10.00"
    assert len(passes) == 2


def _budget_half() -> int:
    budget_probe = frostwork.Page()
    budget_probe.field("name", "h1")
    return budget_probe.check().max_members // 2 + 1


def _declaring_class(name: str, base: type, **attributes: Any) -> Any:
    """Return a subclass of *base* with over half the frostwork budget in
    declarations."""
    return type(
        name,
        (base,),
        {
            **{
                f"{name}{i}": css_get(f".{name}{i}::text")
                for i in range(_budget_half())
            },
            **attributes,
        },
    )


def test_dependencies_over_budget() -> None:
    """A page object class and its dependencies must fit in a single pass
    together."""
    group_cls = _declaring_class("Group", SelectorGroup)
    with pytest.raises(
        TypeError, match=r"of BigPage, Group together:\n  - over budget"
    ):
        _declaring_class("BigPage", WebPage, __annotations__={"group": group_cls})


def test_dependencies_over_budget_without_page_declarations() -> None:
    group_classes = [
        _declaring_class(name, SelectorGroup) for name in ("Group1", "Group2")
    ]
    with pytest.raises(
        TypeError, match=r"of Group1, Group2 together:\n  - over budget"
    ):
        type(
            "PlainPage",
            (ItemPage,),
            {
                "__annotations__": {
                    "group1": group_classes[0],
                    "group2": group_classes[1],
                }
            },
        )


def test_dependencies_over_budget_other_response_kinds() -> None:
    """Dependencies that read a different kind of response are extracted in a
    pass of their own."""
    browser_cls = _declaring_class("BrowserLayout", BrowserPage)
    http_cls = _declaring_class("HttpLayout", WebPage)
    type(
        "SwitchPage",
        (ItemPage,),
        {"__annotations__": {"browser": browser_cls, "http": http_cls}},
    )


def test_unresolvable_dependency_annotation() -> None:
    @attrs.define
    class ForwardPage(WebPage):
        later: Later  # type: ignore[name-defined]  # noqa: F821
        name = field(css_get("h1::text"))

    assert _frostwork_module._dependency_classes(ForwardPage) == ()


@pytest.mark.parametrize("first", ["a", "b"])
def test_page_objects_over_budget(response, first) -> None:
    """Page objects over the same response that do not fit in a single pass
    together cannot be extracted, whichever is read first."""
    page_a = _declaring_class("A", WebPage)(response=response)
    page_b = _declaring_class("B", WebPage)(response=response)
    page = page_a if first == "a" else page_b
    with pytest.raises(TypeError, match=r"of A, B together:\n  - over budget"):
        getattr(page, f"{type(page).__name__}0")


@attrs.define
class Product:
    title: str | None


class ProductLayout(WebPage[Product]):
    pass


class ProductLayoutA(ProductLayout):
    title = field(css_get("h1::text"))


class ProductLayoutB(ProductLayout):
    title = field(css_get(".desc::text"))


@layout_switch()
@attrs.define
class ProductPage(ItemPage[Product]):
    response: HttpResponse
    layout_a: ProductLayoutA
    layout_b: ProductLayoutB

    def get_layout(self) -> ItemPage[Product]:
        return self.layout_b if self.response.css(".desc") else self.layout_a


def test_layouts_single_pass(passes, response) -> None:
    page = ProductPage(
        response=response,
        layout_a=ProductLayoutA(response=response),
        layout_b=ProductLayoutB(response=response),
    )
    assert asyncio.run(page.to_item()) == Product(title="A description")
    assert len(passes) == 1


def test_layout_built_at_run_time(passes, response) -> None:
    """A layout that a field builds is extracted in a pass of its own, so the
    layouts that it picks from do not need to fit in a single pass
    together."""
    big_a = _declaring_class("BigA", ProductLayout, title=field(css_get("h1::text")))
    big_b = _declaring_class("BigB", ProductLayout, title=field(css_get(".desc::text")))

    @layout_switch(layouts=[big_a, big_b])
    @attrs.define
    class RunTimeProductPage(ItemPage[Product]):
        response: HttpResponse
        group: SkuSelectors

        def get_layout(self) -> ItemPage[Product]:
            layout_cls = big_b if self.response.css(".desc") else big_a
            return layout_cls(response=self.response)

    page = RunTimeProductPage(
        response=response, group=SkuSelectors(AnyResponse(response))
    )
    assert asyncio.run(page.to_item()) == Product(title="A description")
    assert len(passes) == 2


@attrs.define
class InheritingPage(WebPage, SkuSelectors):
    @field
    def sku(self) -> str | None:
        return self.meta or self.text


def test_inherited_selector_group(passes, response) -> None:
    page = InheritingPage(response=response)
    assert page.sku == "SKU-1"
    assert isinstance(page.response, HttpResponse)
    assert set(_get_selectors_dict(InheritingPage)) == {"meta", "text"}


def test_inherited_selector_group_init(response) -> None:
    """Page object classes must inherit __init__ from their page object base
    class."""

    class WrongOrderPage(SkuSelectors, WebPage):
        pass

    with pytest.raises(TypeError, match="List SelectorGroup subclasses after"):
        WrongOrderPage(response)

    @attrs.define
    class AttrsWrongOrderPage(SkuSelectors, WebPage):
        pass

    assert AttrsWrongOrderPage(response=response).text == "SKU-1"


def test_unread_page_object_is_not_kept_alive(response) -> None:
    page = PricePage(response=response)
    key = id(page)
    assert key in _frostwork_module._unsorted
    del page
    gc.collect()
    assert key not in _frostwork_module._unsorted


def test_read_page_object_is_not_kept_alive(response) -> None:
    """An unread page object sorted by response by the read of another one
    is forgotten when garbage-collected."""
    page = PricePage(response=response)
    key = id(page)
    other = PricePage(HttpResponse("http://example.com", b"", encoding="utf-8"))
    assert other.price is None
    assert key in _frostwork_module._response_keys
    del page
    gc.collect()
    assert key not in _frostwork_module._response_keys
    assert id(response) not in _frostwork_module._by_response


def test_pending_objects_are_resolved_once(monkeypatch) -> None:
    """Each pending object has its response looked up once, however many
    page objects over other responses are read meanwhile."""
    pages = [
        PricePage(HttpResponse("http://example.com", b"", encoding="utf-8"))
        for _ in range(10)
    ]
    lookups: list[Any] = []
    original = _frostwork_module._response_or_none

    def counting_response_or_none(obj):
        lookups.append(obj)
        return original(obj)

    monkeypatch.setattr(
        _frostwork_module, "_response_or_none", counting_response_or_none
    )
    for page in pages:
        assert page.price is None
    assert len(lookups) == 2 * len(pages)


def test_reassigned_response(response) -> None:
    """A page object whose response is set again after another read sorted
    it by response is extracted over its new response."""
    empty = HttpResponse("http://example.com", b"", encoding="utf-8")
    page = PricePage(response=empty)
    assert PricePage(response=response).price == "10.00"
    page.response = response
    assert PricePage(response=empty).price is None
    assert page.price == "10.00"


def test_field_not_callable() -> None:
    with pytest.raises(TypeError, match="must be used on methods"):
        field(1)  # type: ignore[call-overload]


def test_selector_field_name_before_set_name() -> None:
    """A selector declaration has no method of its own to name a field after,
    unlike a field assigned a plain method outside a class body."""
    descriptor = field(css_get("h1::text"))
    assert descriptor.name is None  # type: ignore[attr-defined]

    def name(page):
        return "Foo"

    assert field(name).name == "name"  # type: ignore[attr-defined]


@pytest.mark.parametrize("cached", [False, True])
def test_nameless_field_outside_class_body(response, cached) -> None:
    @attrs.define
    class LatePage(WebPage):
        pass

    def get_value(page, value):
        return value

    LatePage.name = field(partial(get_value, value="Foo"), cached=cached)  # type: ignore[attr-defined]
    assert LatePage(response=response).name == "Foo"  # type: ignore[attr-defined]


def test_selector_field_outside_class_body(response) -> None:
    @attrs.define
    class LatePage(WebPage):
        pass

    LatePage.name = field(css_get("h1::text"))  # type: ignore[attr-defined]
    with pytest.raises(TypeError, match="assigned in a class body"):
        LatePage(response=response).name  # type: ignore[attr-defined]


def test_declaration_outside_class_body(response) -> None:
    """A bare declaration set on a class after its creation is extracted on
    its own."""

    @attrs.define
    class LatePage(WebPage):
        brand = field(xpath_get("//meta[@itemprop='brand']/@content"))

    @attrs.define
    class LateOnlyPage(WebPage):
        pass

    LatePage.name = css_get("h1::text")  # type: ignore[attr-defined]
    LateOnlyPage.name = css_get("h1::text")  # type: ignore[attr-defined]
    page = LatePage(response=response)
    assert page.name == " Foo "  # type: ignore[attr-defined]
    assert page.brand == "Acme"
    assert LateOnlyPage(response=response).name == " Foo "  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "declaration",
    [css_get("h1::text"), field(css_get("h1::text"))],
    ids=["declaration", "field"],
)
def test_annotated_declaration(declaration) -> None:
    # Python < 3.12 wraps errors from __set_name__ in a RuntimeError.
    with pytest.raises((TypeError, RuntimeError)) as exc_info:

        class AnnotatedPage(WebPage):
            name: str = declaration

    error: BaseException | None = exc_info.value
    if isinstance(error, RuntimeError):
        error = error.__cause__
    assert isinstance(error, TypeError)
    assert "AnnotatedPage.name is a selector declaration" in str(error)


def test_field_metadata() -> None:
    assert Page.name.__name__ == "name"
    assert Page.name.__qualname__ == "Page.name"


def test_out(response) -> None:
    @attrs.define
    class OutPage(WebPage):
        name = field(css_get("h1::text"), out=[str.strip])
        images = field(css_getall("img::attr(src)"), out=[len])

    page = OutPage(response=response)
    assert page.name == "Foo"
    assert page.images == 2


def test_processors(response) -> None:
    @attrs.define
    class ProcessorsPage(WebPage):
        name = field(css_get("h1::text"))

        class Processors:
            name = [str.strip]

    assert ProcessorsPage(response=response).name == "Foo"


def test_meta() -> None:
    from web_poet.fields import get_fields_dict  # noqa: PLC0415

    @attrs.define
    class MetaPage(WebPage):
        name = field(css_get("h1::text"), meta={"expensive": False})

    assert get_fields_dict(MetaPage)["name"].meta == {"expensive": False}


def test_extra_dependency(response) -> None:
    """Attrs recreates the class, dropping the temporary markers that
    ``__init_subclass__`` relies on. Declarations must survive that, including
    when the subclass adds a dependency.

    See https://github.com/scrapinghub/web-poet/issues/141
    """

    @attrs.define
    class SubPage(Page):
        http: HttpClient

    page = SubPage(response=response, http=HttpClient())
    assert set(_get_selectors_dict(SubPage)) == set(_get_selectors_dict(Page))
    assert page.name == " Foo "


class TestInheritance:
    def test_add(self, response) -> None:
        @attrs.define
        class SubPage(Page, Returns[dict]):
            price = field(css_get(".price::text"))

        assert _get_selectors_dict(SubPage)["price"].expression == ".price::text"
        assert SubPage(response=response).price == "10.00"
        assert SubPage(response=response).name == " Foo "

    def test_override(self, response) -> None:
        @attrs.define
        class SubPage(Page):
            name = field(css_get(".price::text"))

        assert SubPage(response=response).name == "10.00"
        assert Page(response=response).name == " Foo "

    def test_shadow_with_a_method(self, response) -> None:
        @attrs.define
        class SubPage(Page):
            @field
            def name(self) -> str:
                return "hardcoded"

        assert "name" not in _get_selectors_dict(SubPage)
        assert "name" in _get_selectors_dict(Page)
        assert SubPage(response=response).name == "hardcoded"

    def test_remove(self, response) -> None:
        @attrs.define
        class SubPage(Page):
            _sku_a = None

            @field
            def sku(self) -> str | None:
                return self._sku_b

        assert "_sku_a" not in _get_selectors_dict(SubPage)
        assert SubPage(response=response).sku is None


def test_selector_extractor() -> None:
    """An extractor built on a selector provides no document to scan."""
    with pytest.raises(TypeError, match="no response"):

        class Extractor(SelectorExtractor):
            name = field(css_get("h1::text"))

    class PlainExtractor(SelectorExtractor):
        @field
        def name(self) -> str | None:
            return self.css("h1::text").get()

    assert PlainExtractor(parsel.Selector(HTML)).name == " Foo "


def test_browser_page() -> None:
    """A browser response provides no bytes to scan, but its HTML can be
    scanned as it is."""

    @attrs.define
    class Page(BrowserPage):
        name = field(css_get("h1::text"), out=[str.strip])

    response = BrowserResponse(url="http://example.com", html=HTML)
    assert asyncio.run(Page(response=response).to_item()) == {"name": "Foo"}


def test_unknown_encoding() -> None:
    """A document in an encoding that frostwork does not know is decoded as
    declared, and then extracted by frostwork."""

    @attrs.define
    class EncodedPage(WebPage):
        name = field(css_get("h1::text"))

    body = "<html><body><h1>Café</h1></body></html>".encode("cp437")
    page = EncodedPage(
        response=HttpResponse("http://example.com", body, encoding="cp437")
    )
    assert page._selector_values() != {}
    assert page.name == "Café"


def test_python_codec_name() -> None:
    """A document in an encoding that Python and frostwork name differently is
    extracted by frostwork."""

    @attrs.define
    class EncodedPage(WebPage):
        name = field(css_get("h1::text"))

    body = "<html><body><h1>ก</h1></body></html>".encode("cp874")
    page = EncodedPage(
        response=HttpResponse("http://example.com", body, encoding="cp874")
    )
    assert page._selector_values() != {}
    assert page.name == "ก"


class _OverridingMixin:
    @property
    def html(self) -> str:
        return "<h1>Bar</h1>"

    @property
    def selector(self) -> parsel.Selector:
        return parsel.Selector(text="<h1>Baz</h1>")


@attrs.define
class OverridingWebPage(_OverridingMixin, WebPage):
    name = field(css_get("h1::text"))


@attrs.define
class OverridingBrowserPage(_OverridingMixin, BrowserPage):
    name = field(css_get("h1::text"))


@pytest.mark.parametrize(
    ("page_cls", "response"),
    [
        (
            OverridingWebPage,
            HttpResponse("http://example.com", HTML.encode(), encoding=encoding),
        )
        for encoding in ["utf-8", "cp437"]
    ]
    + [
        (
            OverridingBrowserPage,
            BrowserResponse(url="http://example.com", html=HTML),
        )
    ],
)
def test_selector_override(page_cls, response) -> None:
    """Declarations read the response, even if the page object overrides
    its HTML or its selector, both from its body and from its decoded text."""
    page = page_cls(response=response)
    assert page.name == " Foo "
    assert page.css("h1::text").get() == "Baz"


@pytest.mark.parametrize("encoding", ["hz", "iso2022_kr"])
def test_replacement_encoding(encoding: str) -> None:
    """A document in an encoding that WHATWG maps to the replacement encoding
    is decoded as declared."""

    @attrs.define
    class EncodedPage(WebPage):
        name = field(css_get("h1::text"))

    body = "<html><body><h1>Foo</h1></body></html>".encode(encoding)
    page = EncodedPage(
        response=HttpResponse("http://example.com", body, encoding=encoding)
    )
    assert page.name == "Foo"


def test_rejection_is_cached(monkeypatch) -> None:
    """A document that frostwork cannot decode as declared is checked once
    per page object."""
    calls = []
    resolve_label = frostwork.resolve_label

    def counting_resolve_label(*args):
        calls.append(args)
        return resolve_label(*args)

    monkeypatch.setattr(_frostwork_module, "resolve_label", counting_resolve_label)

    @attrs.define
    class EncodedPage(WebPage):
        name = field(css_get("h1::text"))
        brand = field(xpath_get("//meta[@itemprop='brand']/@content"))

    body = "<html><body><h1>Café</h1></body></html>".encode("cp437")
    page = EncodedPage(
        response=HttpResponse("http://example.com", body, encoding="cp437")
    )
    assert page.name == "Café"
    assert page.brand is None
    assert len(calls) == 1


def test_fallback_is_cached(monkeypatch, response) -> None:
    """A declaration that parsel extracts is extracted once per page
    object."""
    calls = []
    css = parsel.Selector.css

    def counting_css(self, query):
        calls.append(query)
        return css(self, query)

    monkeypatch.setattr(parsel.Selector, "css", counting_css)

    @attrs.define
    class LatePage(WebPage):
        pass

    LatePage.name = css_get("h1::text")  # type: ignore[attr-defined]
    page = LatePage(response=response)
    assert page.name == " Foo "  # type: ignore[attr-defined]
    assert page.name == " Foo "  # type: ignore[attr-defined]
    assert calls == ["h1::text"]


def test_no_declarations(response) -> None:
    """The fields of a page object without declarations do not read its
    document."""

    @attrs.define
    class PlainPage(WebPage):
        @field
        def name(self) -> str | None:
            return self.css("h1::text").get()

        def _selector_document(self):
            raise AssertionError

    assert PlainPage(response=response).name == " Foo "


def test_not_attrs(response) -> None:
    """Declarations work on page objects that are not attrs classes."""

    class CustomPage(ResponseShortcutsMixin):
        name = css_get("h1::text")

        def __init__(self, response):
            self.response = response

    assert CustomPage(response).name == " Foo "


def test_reused_declaration(response) -> None:
    """A declaration can be reused, e.g. by a field that processes its value
    and by a field that composes something else out of the raw value."""

    @attrs.define
    class ReusePage(WebPage):
        _raw_price = css_get(".price::text")
        price = field(_raw_price, out=[float])

        @field
        def price_label(self) -> str:
            return f"only {self._raw_price}!"

    page = ReusePage(response=response)
    assert page.price == 10.0
    assert page.price_label == "only 10.00!"


def test_shared_declaration(response) -> None:
    """The same declaration object can be used by different classes, e.g. as a
    module-level constant."""
    shared = css_get(".sku::text")

    @attrs.define
    class PageA(WebPage):
        a = field(shared)

    @attrs.define
    class PageB(WebPage):
        b = field(shared)

    assert PageA(response=response).a == "SKU-1"
    assert PageB(response=response).b == "SKU-1"


def test_query_method_name(response) -> None:
    """A field can be named after a query method."""

    @attrs.define
    class QueryPage(WebPage):
        css = field(css_get("h1::text"))  # type: ignore[assignment]
        xpath = field(xpath_get("//h1/text()"))  # type: ignore[assignment]

    page = QueryPage(response=response)
    assert page.css == " Foo "
    assert page.xpath == " Foo "


def test_cached(response) -> None:
    """Each cached field caches its own value."""

    @attrs.define
    class CachedPage(WebPage):
        name = field(css_get("h1::text"), cached=True)
        price = field(css_get(".price::text"), cached=True)

    page = CachedPage(response=response)
    assert page.name == " Foo "
    assert page.price == "10.00"
    assert page.name == " Foo "


def test_input_validation(response) -> None:
    """Input validation replaces the value of a declared field with the value
    that the validation item has for it."""

    @attrs.define
    class ValidatingPage(WebPage):
        name = field(css_get("h1::text"))

        def validate_input(self):
            return SimpleNamespace(name="Bar")

    assert ValidatingPage(response=response).name == "Bar"


def test_no_selector() -> None:
    with pytest.raises(TypeError, match="no response"):

        @attrs.define
        class NoSelectorPage(ItemPage):
            name = field(css_get("h1::text"))


def test_no_selector_on_read() -> None:
    class NoSelectorPage:
        name = css_get("h1::text")

    with pytest.raises(TypeError, match="provides no response"):
        NoSelectorPage().name


def test_getall_copies(response) -> None:
    """Changing a list value in place leaves other reads intact."""

    @attrs.define
    class AppendingPage(WebPage):
        _images = css_getall("img::attr(src)")

        @field
        def mutated(self) -> list[str]:
            images = self._images
            images.append("x")
            return images

    page = AppendingPage(response=response)
    assert page.mutated == ["a.png", "b.png", "x"]
    assert page.mutated == ["a.png", "b.png", "x"]
    assert page._images == ["a.png", "b.png"]


def test_fixture(response, tmp_path) -> None:
    base_dir = tmp_path / "fixtures" / "tests.test_selectors.Page"
    item = asyncio.run(Page(response=response).to_item())
    Fixture.save(base_dir, inputs=[response], item=item)
    fixture = Fixture(base_dir / "test-1")
    fixture.assert_full_item_correct(Page)
    fixture.assert_field_correct("name", Page)
    fixture.assert_no_extra_fields(Page)
    fixture.assert_no_toitem_exceptions(Page)
