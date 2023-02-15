from typing import Type

import attrs
import pytest

from web_poet import HttpResponse, HttpResponseBody, ResponseUrl, WebPage
from web_poet.page_inputs.url import _Url
from web_poet.serialization import (
    SerializedDataFileStorage,
    SerializedLeafData,
    deserialize,
    deserialize_leaf,
    register_serialization,
    serialize,
    serialize_leaf,
)


def _assert_webpages_equal(p1: WebPage, p2: WebPage) -> None:
    assert type(p1) == type(p2)
    assert type(p1.response) == type(p2.response)  # noqa: E721
    assert type(p1.response.body) == type(p2.response.body)  # noqa: E721
    assert type(p1.response.headers) == type(p2.response.headers)  # noqa: E721
    assert p1.response.body == p2.response.body
    assert p1.response.status == p2.response.status
    assert p1.response.headers == p2.response.headers
    assert p1.response._encoding == p2.response._encoding
    _assert_urls_equal(p1.response.url, p2.response.url)


def _assert_urls_equal(u1: _Url, u2: _Url) -> None:
    assert type(u1) == type(u2)
    assert str(u1) == str(u2)


def test_serialization_leaf() -> None:
    leaf = HttpResponseBody(b"foo")
    serialized_data = serialize_leaf(leaf)
    assert isinstance(serialized_data["html"], bytes)
    assert HttpResponseBody(serialized_data["html"]) == leaf
    deserialized_data = deserialize_leaf(HttpResponseBody, serialized_data)
    assert leaf == deserialized_data


def test_serialization_leaf_unsupported() -> None:
    class A:
        pass

    with pytest.raises(
        NotImplementedError, match=r"Serialization .+ is not implemented"
    ):
        serialize_leaf(A())

    with pytest.raises(
        NotImplementedError, match=r"Deserialization .+ is not implemented"
    ):
        deserialize_leaf(A, {})


def test_serialization(book_list_html_response) -> None:
    @attrs.define
    class MyWebPage(WebPage):
        url: ResponseUrl

    url_str = "http://books.toscrape.com/index.html"
    url = ResponseUrl(url_str)

    serialized_deps = serialize([book_list_html_response, url])
    other_json = f"""{{
  "_encoding": "utf-8",
  "headers": [],
  "status": null,
  "url": "{url_str}"
}}""".encode()
    assert serialized_deps == {
        "HttpResponse": {
            "body.html": bytes(book_list_html_response.body),
            "other.json": other_json,
        },
        "ResponseUrl": {
            "txt": url_str.encode(),
        },
    }

    po = MyWebPage(book_list_html_response, url)
    deserialized_po = deserialize(MyWebPage, serialized_deps)
    _assert_webpages_equal(po, deserialized_po)


def test_serialization_injectable(book_list_html_response) -> None:
    with pytest.raises(ValueError, match=r"Injectable type .+ passed"):
        serialize([WebPage(book_list_html_response)])


def test_serialization_httpresponse_encoding(book_list_html) -> None:
    body = HttpResponseBody(bytes(book_list_html, "utf-8"))
    resp_enc = HttpResponse(
        url=ResponseUrl("http://books.toscrape.com/index.html"),
        body=body,
        encoding="utf-8",
    )
    assert resp_enc._encoding == "utf-8"
    deserialized_resp_enc = deserialize_leaf(HttpResponse, serialize_leaf(resp_enc))
    assert deserialized_resp_enc._encoding == "utf-8"

    resp_noenc = HttpResponse(
        url=ResponseUrl("http://books.toscrape.com/index.html"), body=body
    )
    assert resp_noenc._encoding is None
    deserialized_resp_noenc = deserialize_leaf(HttpResponse, serialize_leaf(resp_noenc))
    assert deserialized_resp_noenc._encoding is None


def test_custom_functions() -> None:
    class C:
        value: int

        def __init__(self, value: int):
            self.value = value

    def _serialize(o: C) -> SerializedLeafData:
        return {"bin": o.value.to_bytes((o.value.bit_length() + 7) // 8, "little")}

    def _deserialize(t: Type[C], data: SerializedLeafData) -> C:
        return t(int.from_bytes(data["bin"], "little"))

    register_serialization(_serialize, _deserialize)

    obj = C(22222222222)
    deserialized_obj = deserialize_leaf(C, serialize_leaf(obj))
    assert obj.value == deserialized_obj.value


def test_write_data(book_list_html_response, tmp_path) -> None:
    @attrs.define
    class MyWebPage(WebPage):
        url: ResponseUrl

    url = ResponseUrl("http://example.com")

    directory = tmp_path / "ser"
    directory.mkdir()
    storage = SerializedDataFileStorage(directory)
    serialized_deps = serialize([book_list_html_response, url])
    storage.write(serialized_deps)
    assert (directory / "HttpResponse-body.html").exists()
    assert (directory / "HttpResponse-body.html").read_bytes() == bytes(
        book_list_html_response.body
    )
    assert (directory / "HttpResponse-other.json").exists()
    assert (directory / "ResponseUrl.txt").exists()
    assert (directory / "ResponseUrl.txt").read_text(
        encoding="utf-8"
    ) == "http://example.com"

    read_serialized_deps = storage.read()
    po = MyWebPage(book_list_html_response, url)
    deserialized_po = deserialize(MyWebPage, read_serialized_deps)
    assert type(deserialized_po) == MyWebPage
    _assert_webpages_equal(po, deserialized_po)


def test_extra_files(book_list_html_response, tmp_path) -> None:
    directory = tmp_path / "ser"
    directory.mkdir()
    storage = SerializedDataFileStorage(directory)
    serialized_deps = serialize([book_list_html_response])
    storage.write(serialized_deps)
    (directory / "foo.dir").mkdir()
    (directory / "bar.txt").touch()
    read_serialized_deps = storage.read()
    assert "HttpResponse" in read_serialized_deps
