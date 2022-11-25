from typing import Optional, Type

import attrs
import pytest

from web_poet import (
    HttpResponse,
    HttpResponseBody,
    Injectable,
    RequestUrl,
    ResponseUrl,
    WebPage,
)
from web_poet.page_inputs.url import _Url
from web_poet.serialization import (
    SerializedData,
    deserialize,
    read_serialized_data,
    register_serialization,
    serialize,
    write_serialized_data,
)


def _compare_webpages(p1: WebPage, p2: WebPage) -> None:
    assert p1.response.body == p2.response.body
    assert p1.response.status == p2.response.status
    assert p1.response.headers == p2.response.headers
    assert p1.response._encoding == p2.response._encoding
    _compare_urls(p1.response.url, p2.response.url)


def _compare_urls(u1: _Url, u2: _Url) -> None:
    assert type(u1) == type(u2)
    assert str(u1) == str(u2)


def test_serialization() -> None:
    data = {"a": "b", "c": 42}
    serialized_data = serialize(data)
    deserialized_data = deserialize(dict, serialized_data)
    assert data == deserialized_data


def test_serialization_unsup() -> None:
    class A:
        pass

    with pytest.raises(NotImplementedError):
        serialize(A())

    with pytest.raises(NotImplementedError):
        deserialize(A, {})


def test_serialization_webpage(book_list_html_response) -> None:
    po = WebPage(book_list_html_response)
    serialized_po = serialize(po)
    deserialized_po = deserialize(WebPage, serialized_po)
    _compare_webpages(po, deserialized_po)


def test_serialization_httpresponse_encoding(book_list_html) -> None:
    body = HttpResponseBody(bytes(book_list_html, "utf-8"))
    resp_enc = HttpResponse(
        url=ResponseUrl("http://books.toscrape.com/index.html"),
        body=body,
        encoding="utf-8",
    )
    assert resp_enc._encoding == "utf-8"
    deserialized_resp_enc = deserialize(HttpResponse, serialize(resp_enc))
    assert deserialized_resp_enc._encoding == "utf-8"

    resp_noenc = HttpResponse(
        url=ResponseUrl("http://books.toscrape.com/index.html"), body=body
    )
    assert resp_noenc._encoding is None
    deserialized_resp_noenc = deserialize(HttpResponse, serialize(resp_noenc))
    assert deserialized_resp_noenc._encoding is None


def test_serialization_misc_types(book_list_html_response) -> None:
    @attrs.define
    class MyWebPage(WebPage):
        f1: str
        f2: bytes
        f3: RequestUrl
        f4: Optional[str]
        f5: Optional[str]

    po = MyWebPage(
        response=book_list_html_response,
        f1="foo",
        f2=b"bar",
        f3=RequestUrl("http://example.com"),
        f4=None,
        f5="baz",
    )
    serialized_po = serialize(po)
    deserialized_po = deserialize(MyWebPage, serialized_po)
    assert type(deserialized_po) == MyWebPage
    assert deserialized_po.f1 == "foo"
    assert deserialized_po.f2 == b"bar"
    assert type(deserialized_po.f3) == RequestUrl
    assert str(deserialized_po.f3) == "http://example.com"
    assert deserialized_po.f4 is None
    assert deserialized_po.f5 == "baz"


def test_custom_functions() -> None:
    class C:
        value: int

        def __init__(self, value: int):
            self.value = value

    def _serialize(o: C) -> SerializedData:
        return {"bin": o.value.to_bytes((o.value.bit_length() + 7) // 8, "little")}

    def _deserialize(t: Type[C], data: SerializedData) -> C:
        return t(int.from_bytes(data["bin"], "little"))

    register_serialization(_serialize, _deserialize)

    obj = C(22222222222)
    deserialized_obj = deserialize(C, serialize(obj))
    assert obj.value == deserialized_obj.value


def test_extra_attrs():
    @attrs.define
    class C(Injectable):
        f1: Optional[str]
        f2: Optional[str]

    obj = C(f1="foo", f2="bar")
    serialized_obj = serialize(obj)
    del serialized_obj["f1"]
    deserialized_obj = deserialize(C, serialized_obj)
    assert deserialized_obj.f1 is None
    assert deserialized_obj.f2 == "bar"


def test_write_data(book_list_html_response, tmp_path) -> None:
    directory = tmp_path / "ser"
    directory.mkdir()
    po = WebPage(book_list_html_response)
    serialized_po = serialize(po)
    write_serialized_data(serialized_po, directory)
    assert (directory / "response.body.html").exists()
    read_serialized_po = read_serialized_data(directory)
    deserialized_po = deserialize(WebPage, read_serialized_po)
    assert type(deserialized_po) == WebPage
    _compare_webpages(po, deserialized_po)
