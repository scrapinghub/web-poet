from __future__ import annotations

import asyncio

import attrs
import pytest

from web_poet import (
    BrowserPage,
    BrowserResponse,
    HttpResponse,
    SelectorExtractor,
    WebPage,
    _frostwork,
    css,
    field,
    jmespath,
    xpath,
)
from web_poet._frostwork import _get_page
from web_poet._selectors import _get_selectors_dict

frostwork = pytest.importorskip("frostwork")

HTML = """
<html>
  <head>
    <meta itemprop="brand" content="Acme">
    <script type="application/ld+json">{"sku": "SKU-1"}</script>
  </head>
  <body>
    <h1> Foo </h1>
    <p class="price">10.00</p>
    <img src="a.png"><img src="b.png">
    <div class="desc">A description</div>
  </body>
</html>
"""


@pytest.fixture
def response():
    return HttpResponse("http://example.com", HTML.encode("utf-8"), encoding="utf-8")


@attrs.define
class Page(WebPage, declarative_backend="frostwork"):
    name = field(css("h1::text").get())
    images = field(css("img::attr(src)").getall())
    brand = field(xpath("//meta[@itemprop='brand']/@content").get())
    sources = field(xpath("//img/@src").getall())
    missing = field(css(".missing::text").get())

    description = field(css(".desc:contains('description')::text").get())

    # Neither a selector list nor JMESPath is something that frostwork can
    # extract.
    price = field(css(".price::text"), out=[lambda value: value.get()])
    sku = field(jmespath("sku").get())


EXPECTED = {
    "name": " Foo ",
    "images": ["a.png", "b.png"],
    "brand": "Acme",
    "sources": ["a.png", "b.png"],
    "missing": None,
    "price": "10.00",
    "sku": None,
    "description": "A description",
}


def test_extractable_declarations() -> None:
    page = _get_page(Page)
    assert page is not None
    assert set(page[1].values()) == {
        "name",
        "images",
        "brand",
        "sources",
        "missing",
        "description",
    }


def test_unsupported_declaration() -> None:
    with pytest.raises(TypeError, match=r"name = ':root h1::text'"):

        class UnsupportedPage(WebPage, declarative_backend="frostwork"):
            name = field(css(":root h1::text").get())
            brand = field(xpath("//meta[@itemprop='brand']/@content").get())


def test_over_budget() -> None:
    with pytest.raises(TypeError, match="over budget"):

        class OverBudgetPage(WebPage, declarative_backend="frostwork"):
            # Every comma-separated selector counts towards the budget, which
            # is 128 selectors at the time of writing.
            name = field(css(", ".join(["h1::text"] * 129)).get())


def test_invalid_backend() -> None:
    with pytest.raises(ValueError, match="'lxml'"):

        class InvalidPage(WebPage, declarative_backend="lxml"):  # type: ignore[arg-type]
            pass


def test_default_backend(response) -> None:
    """Without declarative_backend, parsel extracts every declaration."""

    @attrs.define
    class ParselPage(WebPage):
        name = field(css("h1::text").get())
        brand = field(xpath("//meta[@itemprop='brand']/@content").get())

    page = ParselPage(response=response)
    assert page.name == " Foo "
    assert set(page._selector_value_cache()) == {
        _get_selectors_dict(ParselPage)["name"]
    }


def test_inheritance(response) -> None:
    """Subclasses inherit declarative_backend, and can set it back to
    parsel."""

    class SubPage(Page):
        pass

    class ParselPage(Page, declarative_backend="parsel"):
        pass

    sub_page = SubPage(response=response)
    assert sub_page.name == " Foo "
    assert len(sub_page._selector_value_cache()) == 6
    parsel_page = ParselPage(response=response)
    assert parsel_page.name == " Foo "
    assert len(parsel_page._selector_value_cache()) == 1


def test_no_extractable_declarations(response) -> None:
    @attrs.define
    class JmesPathPage(WebPage, declarative_backend="frostwork"):
        _ld = css('script[type="application/ld+json"]::text')

        @field
        def sku(self) -> str | None:
            return self._ld.jmespath("sku").get()

    assert _get_page(JmesPathPage) is None
    assert JmesPathPage(response=response).sku == "SKU-1"


def test_values(response) -> None:
    assert asyncio.run(Page(response=response).to_item()) == EXPECTED


def test_parsel_agreement(response) -> None:
    """Every declaration has the same value with either backend."""

    class ParselPage(Page, declarative_backend="parsel"):
        pass

    assert asyncio.run(ParselPage(response=response).to_item()) == EXPECTED


def test_extraction_is_eager(response) -> None:
    """Reading one declaration that frostwork extracts extracts every other
    declaration that frostwork extracts, in the same pass."""
    page = Page(response=response)
    assert page.name == " Foo "
    declarations = _get_selectors_dict(Page)
    assert set(page._selector_value_cache()) == {
        declarations[name]
        for name in ("name", "images", "brand", "sources", "missing", "description")
    }


def test_fallback_is_lazy(response) -> None:
    """A declaration that frostwork cannot extract does not trigger a scan."""
    page = Page(response=response)
    assert page.sku is None
    assert set(page._selector_value_cache()) == {_get_selectors_dict(Page)["sku"]}


def test_reused_declaration(response) -> None:
    """A declaration used by more than one attribute is extracted once."""

    @attrs.define
    class ReusePage(WebPage, declarative_backend="frostwork"):
        _raw_price = css(".price::text").get()
        price = field(_raw_price, out=[float])

    result = _get_page(ReusePage)
    assert result is not None
    assert set(result[1].values()) == {"_raw_price"}
    assert ReusePage(response=response).price == 10.0


def test_unknown_encoding() -> None:
    """A document in an encoding that frostwork does not know is left to
    parsel, which decodes it as declared."""

    @attrs.define
    class EncodedPage(WebPage, declarative_backend="frostwork"):
        name = field(css("h1::text").get())
        brand = field(xpath("//meta[@itemprop='brand']/@content").get())

    body = "<html><body><h1>Caf\u00e9</h1></body></html>".encode("cp437")
    page = EncodedPage(
        response=HttpResponse("http://example.com", body, encoding="cp437")
    )
    assert page.name == "Caf\u00e9"
    assert set(page._selector_value_cache()) == {
        _get_selectors_dict(EncodedPage)["name"]
    }


def test_python_codec_name() -> None:
    """A document in an encoding that Python and frostwork name differently is
    extracted by frostwork."""

    @attrs.define
    class EncodedPage(WebPage, declarative_backend="frostwork"):
        name = field(css("h1::text").get())
        brand = field(xpath("//meta[@itemprop='brand']/@content").get())

    body = "<html><body><h1>\u0e01</h1></body></html>".encode("cp874")
    page = EncodedPage(
        response=HttpResponse("http://example.com", body, encoding="cp874")
    )
    assert page.name == "\u0e01"
    assert set(page._selector_value_cache()) == set(
        _get_selectors_dict(EncodedPage).values()
    )


def test_browser_page() -> None:
    """A browser response provides no bytes to scan, but its HTML can be
    scanned as it is."""

    @attrs.define
    class BrowserPageSubclass(BrowserPage, declarative_backend="frostwork"):
        name = field(css("h1::text").get())

    response = BrowserResponse(url="http://example.com", html=HTML)
    assert asyncio.run(BrowserPageSubclass(response=response).to_item()) == {
        "name": " Foo "
    }


def test_selector_extractor() -> None:
    """An extractor built on a selector provides no document to scan."""
    with pytest.raises(TypeError, match="no response"):

        class Extractor(SelectorExtractor, declarative_backend="frostwork"):
            name = field(css("h1::text").get())


def test_rejection_is_cached(monkeypatch) -> None:
    """A document that frostwork cannot extract is checked once per page
    object."""
    calls = []
    resolve_label = frostwork.resolve_label

    def counting_resolve_label(*args):
        calls.append(args)
        return resolve_label(*args)

    monkeypatch.setattr(_frostwork, "resolve_label", counting_resolve_label)

    @attrs.define
    class EncodedPage(WebPage, declarative_backend="frostwork"):
        name = field(css("h1::text").get())
        brand = field(xpath("//meta[@itemprop='brand']/@content").get())

    body = "<html><body><h1>Café</h1></body></html>".encode("cp437")
    page = EncodedPage(
        response=HttpResponse("http://example.com", body, encoding="cp437")
    )
    assert page.name == "Café"
    assert page.brand is None
    assert len(calls) == 1
