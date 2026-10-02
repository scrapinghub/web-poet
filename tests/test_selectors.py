from __future__ import annotations

import asyncio
import re
from types import SimpleNamespace

import attrs
import parsel
import pytest
from cssselect.parser import SelectorSyntaxError
from cssselect.xpath import ExpressionError
from lxml.etree import XPathSyntaxError  # type: ignore[import-untyped]

from web_poet import (
    BrowserPage,
    BrowserResponse,
    HttpClient,
    HttpResponse,
    ItemPage,
    Returns,
    SelectorExtractor,
    WebPage,
    css,
    field,
    jmespath,
    xpath,
)
from web_poet._selectors import _get_selectors_dict
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
    name = field(css("h1::text").get())
    images = field(css("img::attr(src)").getall())
    brand = field(xpath("//meta[@itemprop='brand']/@content").get())
    missing = field(css(".missing::text").get())
    missing_all = field(css(".missing::text").getall())

    _sku_a = css(".sku::text").get()
    _sku_b = xpath("//meta[@name='sku']/@content").get()

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
    assert page.missing is None
    assert page.missing_all == []
    assert page.sku == "SKU-1"
    assert page.description == "A description"


def test_to_item(response) -> None:
    assert asyncio.run(Page(response=response).to_item()) == {
        "name": " Foo ",
        "images": ["a.png", "b.png"],
        "brand": "Acme",
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
    assert css("h1::text").get() == css("h1::text").get()
    assert css("h1::text").get() != css("h1::text").getall()
    assert css("h1::text").get() != css("h2::text").get()
    assert css("h1").get() != xpath("h1").get()
    assert css("h1::text") != "h1::text"


def test_equal_declarations(response) -> None:
    """Equal declarations of different attributes are extracted once."""

    @attrs.define
    class TwinPage(WebPage):
        a = field(css(".price::text").get())
        b = field(css(".price::text").get())

    page = TwinPage(response=response)
    assert page.a == page.b == "10.00"
    assert len(page._selector_value_cache()) == 1


def test_repr() -> None:
    assert repr(css("img::attr(src)").getall()) == "css('img::attr(src)').getall()"


def test_xpath_function(response) -> None:
    """An XPath expression can be anything XPath supports."""

    @attrs.define
    class FunctionPage(WebPage):
        name = field(xpath("normalize-space(//h1)").get())
        images = field(xpath("count(//img)").get())

    page = FunctionPage(response=response)
    assert page.name == "Foo"
    assert page.images == "2.0"


@pytest.mark.skipif(
    not hasattr(parsel.Selector, "jmespath"),
    reason="parsel < 1.8 doesn't support jmespath",
)
def test_jmespath() -> None:
    @attrs.define
    class JsonPage(WebPage):
        name = field(jmespath("website.name").get())
        price = field(jmespath("price").get())
        tags = field(jmespath("tags").getall())
        missing = field(jmespath("missing").get())

        _website = jmespath("website")

        @field
        def website_name(self) -> str | None:
            return self._website.jmespath("name").get()

    response = HttpResponse(
        "http://example.com",
        b'{"website": {"name": "homepage"}, "price": 10, "tags": ["a", "b"]}',
        encoding="utf-8",
    )
    assert asyncio.run(JsonPage(response=response).to_item()) == {
        "name": "homepage",
        "price": 10,
        "tags": ["a", "b"],
        "missing": None,
        "website_name": "homepage",
    }


@pytest.mark.skipif(
    not hasattr(parsel.Selector, "jmespath"),
    reason="parsel < 1.8 doesn't support jmespath",
)
def test_jmespath_in_html() -> None:
    """A selector declaration can be queried further, e.g. to read JSON
    embedded in a web page with JMESPath."""

    @attrs.define
    class LdJsonPage(WebPage):
        _ld = css('script[type="application/ld+json"]::text')

        @field
        def price(self) -> str | None:
            return self._ld.jmespath("offers.price").get()

        @field
        def currency(self) -> str | None:
            return self._ld.jmespath("offers.currency").get()

    response = HttpResponse(
        "http://example.com",
        b"""<script type="application/ld+json">
        {"offers": {"price": "10.00", "currency": "USD"}}</script>""",
        encoding="utf-8",
    )
    page = LdJsonPage(response=response)
    assert page.price == "10.00"
    assert page.currency == "USD"


def test_additional_request(response) -> None:
    """Declarations apply to the response of their page object class. A page
    object class of its own gives the response of an additional request its own
    declarations."""

    async def download(request):
        return HttpResponse(request.url, b"<h1>Bar</h1>", encoding="utf-8")

    @attrs.define
    class OtherPage(WebPage):
        name = field(css("h1::text").get())

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


def test_selector_declaration(response) -> None:
    """The value of a selector declaration is a parsel selector list, which is
    empty when there is no match."""

    @attrs.define
    class SelectorPage(WebPage):
        price = css(".price")
        missing = css(".missing")
        brand = xpath("//meta[@itemprop='brand']")

    page = SelectorPage(response=response)
    assert page.price.css("::text").get() == "10.00"
    assert page.missing.css("::text").get() is None
    assert page.brand.xpath("@content").get() == "Acme"


def test_field_not_callable() -> None:
    with pytest.raises(TypeError, match="must be used on methods"):
        field(1)  # type: ignore[call-overload]


def test_selector_field_name_before_set_name() -> None:
    """A selector declaration has no method of its own to name a field after,
    unlike a field assigned a plain method outside a class body."""
    descriptor = field(css("h1::text").get())
    assert descriptor.name is None  # type: ignore[attr-defined]

    def name(page):
        return "Foo"

    assert field(name).name == "name"  # type: ignore[attr-defined]


def test_selector_field_outside_class_body(response) -> None:
    @attrs.define
    class LatePage(WebPage):
        pass

    LatePage.name = field(css("h1::text").get())  # type: ignore[attr-defined]
    with pytest.raises(TypeError, match="assigned in a class body"):
        LatePage(response=response).name  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "declaration",
    [css("h1::text").get(), field(css("h1::text").get())],
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
        name = field(css("h1::text").get(), out=[str.strip])
        images = field(css("img::attr(src)").getall(), out=[len])

    page = OutPage(response=response)
    assert page.name == "Foo"
    assert page.images == 2


def test_processors(response) -> None:
    @attrs.define
    class ProcessorsPage(WebPage):
        name = field(css("h1::text").get())

        class Processors:
            name = [str.strip]

    assert ProcessorsPage(response=response).name == "Foo"


def test_meta() -> None:
    from web_poet.fields import get_fields_dict  # noqa: PLC0415

    @attrs.define
    class MetaPage(WebPage):
        name = field(css("h1::text").get(), meta={"expensive": False})

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
            price = field(css(".price::text").get())

        assert _get_selectors_dict(SubPage)["price"].expression == ".price::text"
        assert SubPage(response=response).price == "10.00"
        assert SubPage(response=response).name == " Foo "

    def test_override(self, response) -> None:
        @attrs.define
        class SubPage(Page):
            name = field(css(".price::text").get())

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
    @attrs.define
    class Extractor(SelectorExtractor):
        name = field(css("h1::text").get(), out=[str.strip])

    sel = parsel.Selector(HTML)
    assert asyncio.run(Extractor(sel).to_item()) == {"name": "Foo"}


def test_browser_page() -> None:
    @attrs.define
    class Page(BrowserPage):
        name = field(css("h1::text").get(), out=[str.strip])

    response = BrowserResponse(url="http://example.com", html=HTML)
    assert asyncio.run(Page(response=response).to_item()) == {"name": "Foo"}


def test_extraction_is_lazy(response) -> None:
    """Parsel extracts the read declaration alone, and caches its value."""
    declarations = _get_selectors_dict(Page)
    page = Page(response=response)
    assert page.name == " Foo "
    cache = page._selector_value_cache()
    assert cache == {declarations["name"]: " Foo "}


def test_invalid_expression() -> None:
    """An invalid expression fails on declaration."""
    with pytest.raises(SelectorSyntaxError):
        css("::::")
    with pytest.raises(ExpressionError):
        css("h1::txt")
    with pytest.raises(XPathSyntaxError):
        xpath("//h1[")


def test_invalid_jmespath_expression() -> None:
    exceptions = pytest.importorskip("jmespath.exceptions")
    with pytest.raises(exceptions.ParseError):
        jmespath("website.")


def test_jmespath_unsupported(monkeypatch) -> None:
    monkeypatch.delattr(parsel.Selector, "jmespath", raising=False)
    with pytest.raises(ImportError, match=re.escape("parsel >= 1.8.1")):
        jmespath("website.name")


def test_extraction_error(response) -> None:
    """A declaration that fails on extraction only affects its own field."""

    @attrs.define
    class BrokenPage(WebPage):
        name = field(css("h1::text").get())
        broken = field(xpath("//*[unregistered()]").get())

    page = BrokenPage(response=response)
    assert page.name == " Foo "
    with pytest.raises(ValueError, match="Unregistered function"):
        page.broken


def test_reused_declaration(response) -> None:
    """A declaration can be reused, e.g. by a field that processes its value
    and by a field that composes something else out of the raw value.

    It is extracted once, no matter how many attributes use it."""

    @attrs.define
    class ReusePage(WebPage):
        _raw_price = css(".price::text").get()
        price = field(_raw_price, out=[float])

        @field
        def price_label(self) -> str:
            return f"only {self._raw_price}!"

    page = ReusePage(response=response)
    assert page.price == 10.0
    assert page.price_label == "only 10.00!"
    assert len(page._selector_value_cache()) == 1


def test_shared_declaration(response) -> None:
    """The same declaration object can be used by different classes, e.g. as a
    module-level constant."""
    shared = css(".sku::text").get()

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
        css = field(css("h1::text").get())  # type: ignore[assignment]
        xpath = field(xpath("//h1/text()").get())  # type: ignore[assignment]

    page = QueryPage(response=response)
    assert page.css == " Foo "
    assert page.xpath == " Foo "


def test_cached(response) -> None:
    """Each cached field caches its own value."""

    @attrs.define
    class CachedPage(WebPage):
        name = field(css("h1::text").get(), cached=True)
        price = field(css(".price::text").get(), cached=True)

    page = CachedPage(response=response)
    assert page.name == " Foo "
    assert page.price == "10.00"
    assert page.name == " Foo "


def test_input_validation(response) -> None:
    """Input validation replaces the value of a declared field with the value
    that the validation item has for it."""

    @attrs.define
    class ValidatingPage(WebPage):
        name = field(css("h1::text").get())

        def validate_input(self):
            return SimpleNamespace(name="Bar")

    assert ValidatingPage(response=response).name == "Bar"


def test_no_selector() -> None:
    @attrs.define
    class NoSelectorPage(ItemPage):
        name = field(css("h1::text").get())

    with pytest.raises(TypeError, match="provides no parsel selector"):
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
