import pytest

from web_poet import RequestUrl, ResponseUrl
from web_poet.page_inputs.url import _Url


def test_url_base_class() -> None:
    url_str = "http://example.com"
    url = _Url(url_str)
    assert str(url) == url_str
    assert repr(url) == "_Url('http://example.com')"


def test_url_init_validation() -> None:
    with pytest.raises(TypeError):
        _Url(123)  # type: ignore[arg-type]


def test_url_subclasses() -> None:
    url_str = "http://example.com"

    class MyUrl(_Url):
        pass

    class MyUrl2(_Url):
        pass

    url = MyUrl(url_str)
    assert str(url) == url_str
    assert url._url == url_str
    assert repr(url) == "MyUrl('http://example.com')"

    url2 = MyUrl2(url)
    assert str(url2) == str(url)


@pytest.mark.parametrize("url_cls", [_Url, RequestUrl, ResponseUrl])
def test_str_equality(url_cls) -> None:
    url_str = "http://example.com#foo"
    url = url_cls(url_str)
    assert url != url_str
    assert str(url) == url_str


def test_url_classes_eq() -> None:
    url_str = "http://example.com#foo"
    request_url = RequestUrl(url_str)
    response_url = ResponseUrl(url_str)

    assert request_url != response_url
    assert str(request_url) == str(response_url)
