from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import andi
import attrs
import frostwork
import parsel
import pytest

from web_poet import (
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
    xpath_get,
    xpath_getall,
)
from web_poet import _frostwork as _frostwork_module
from web_poet._frostwork import _get_page
from web_poet._selectors import _get_selectors_dict
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
    assert page._frostwork_values() == {
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


def test_selector_group(response) -> None:
    """A selector group can be built through dependency injection."""
    plan = andi.plan(
        GroupPage, is_injectable=is_injectable, externally_provided={HttpResponse}
    )
    instances: dict[Any, Any] = {HttpResponse: response}
    for cls, kwargs in plan:
        if cls not in instances:
            instances[cls] = cls(**{k: instances[v] for k, v in kwargs.items()})
    page = instances[GroupPage]
    assert isinstance(page, GroupPage)
    assert asyncio.run(page.to_item()) == {"sku": "SKU-1"}


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
    """A document in an encoding that frostwork does not know is left to
    parsel, which decodes it as declared."""

    @attrs.define
    class EncodedPage(WebPage):
        name = field(css_get("h1::text"))

    body = "<html><body><h1>Café</h1></body></html>".encode("cp437")
    page = EncodedPage(
        response=HttpResponse("http://example.com", body, encoding="cp437")
    )
    assert page.name == "Café"
    assert page._frostwork_values() is None


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
    assert page.name == "ก"
    assert page._frostwork_values() is not None


def test_rejection_is_cached(monkeypatch) -> None:
    """A document that frostwork cannot extract is checked once per page
    object."""
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
    @attrs.define
    class NoSelectorPage(ItemPage):
        name = field(css_get("h1::text"))

    with pytest.raises(TypeError, match="provides no response"):
        NoSelectorPage().name


def test_fixture(response, tmp_path) -> None:
    base_dir = tmp_path / "fixtures" / "tests.test_selectors.Page"
    item = asyncio.run(Page(response=response).to_item())
    Fixture.save(base_dir, inputs=[response], item=item)
    fixture = Fixture(base_dir / "test-1")
    fixture.assert_full_item_correct(Page)
    fixture.assert_field_correct("name", Page)
    fixture.assert_no_extra_fields(Page)
    fixture.assert_no_toitem_exceptions(Page)
