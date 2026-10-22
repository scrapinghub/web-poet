from __future__ import annotations

import gzip
import re
from typing import TYPE_CHECKING, Any

import attrs
import pytest

from benchmarks.conftest import FIXTURES
from benchmarks.pages import (
    ArticlePage,
    JmesPathArticlePage,
    JobPostingPage,
    JsonLdArticlePage,
    MinimalPage,
    ProductDetailsPage,
    ProductPage,
)
from web_poet import HttpResponse, ItemPage

if TYPE_CHECKING:
    import asyncio

    from benchmarks.conftest import PageBuilder

#: Page object class and fixture name of every benchmark, keyed by benchmark
#: name. Results are tracked by name over time, so a name is meant to outlive
#: changes to the page object it measures.
BENCHMARKS: dict[str, tuple[type[ItemPage], str]] = {
    "product_imperative": (ProductPage, "product"),
    "product_details_nodes": (ProductDetailsPage, "product"),
    "article_imperative": (ArticlePage, "article"),
    "article_jsonld": (JsonLdArticlePage, "article"),
    "article_jmespath": (JmesPathArticlePage, "article"),
    "job_imperative": (JobPostingPage, "job"),
    "minimal": (MinimalPage, "minimal"),
}


def _extract(loop: asyncio.AbstractEventLoop, page: PageBuilder, name: str) -> Any:
    page_cls, fixture = BENCHMARKS[name]
    return loop.run_until_complete(page(page_cls, fixture).to_item())


@pytest.mark.parametrize("name", list(BENCHMARKS))
def test_extraction(benchmark, loop, page, name: str) -> None:
    benchmark(_extract, loop, page, name)


@pytest.mark.parametrize("name", list(BENCHMARKS))
def test_every_field_is_extracted(loop, page, name: str) -> None:
    """Guard the benchmarks against measuring extraction that no longer
    extracts anything."""
    item = _extract(loop, page, name)
    empty = [
        field.name
        for field in attrs.fields(type(item))
        if not getattr(item, field.name)
    ]
    assert not empty


_META_CHARSET_RE = re.compile(rb"<meta[^>]*charset[^>]*>", re.IGNORECASE)


def _encoding_cases() -> dict[str, tuple[bytes, dict[str, str]]]:
    """Return the body and headers of each encoding benchmark, for every
    combination of where the page declares its encoding and which encoding
    it is."""
    cases = {}
    for encoding, fixture in (
        ("utf-8", "article"),
        ("windows-1252", "windows-1252"),
        ("shift_jis", "shift_jis"),
    ):
        body = gzip.decompress((FIXTURES / f"{fixture}.html.gz").read_bytes())
        undeclared = _META_CHARSET_RE.sub(b"", body)
        cases |= {
            f"header-{encoding}": (
                undeclared,
                {"Content-Type": f"text/html; charset={encoding}"},
            ),
            f"meta-{encoding}": (body, {"Content-Type": "text/html"}),
            f"undeclared-{encoding}": (undeclared, {}),
        }
    return cases


ENCODING_CASES = _encoding_cases()


def _decode(body: bytes, headers: dict[str, str]) -> str:
    response = HttpResponse("https://example.com", body=body, headers=headers)
    response.encoding
    return response.text


@pytest.mark.parametrize(
    ("body", "headers"), ENCODING_CASES.values(), ids=ENCODING_CASES
)
def test_encoding(benchmark, body: bytes, headers: dict[str, str]) -> None:
    benchmark(_decode, body, headers)
