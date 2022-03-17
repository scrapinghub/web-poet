import pytest
import asyncio

from web_poet.page_inputs import ResponseData, Meta


def test_html_response():
    response = ResponseData("url", "content")
    assert response.url == "url"
    assert response.html == "content"
    assert response.status is None
    assert response.headers is None

    response = ResponseData("url", "content", 200, {"User-Agent": "test agent"})
    assert response.status == 200
    assert response.headers["User-Agent"] == "test agent"


def test_meta_restriction():
    # Any value that conforms with `Meta.restrictions` raises an error
    with pytest.raises(ValueError) as err:
        Meta(func=lambda x: x + 1)

    with pytest.raises(ValueError) as err:
        Meta(class_=ResponseData)

    # These are allowed though
    m = Meta(x="hi", y=2.2, z={"k": "v"})
    m["allowed"] = [1, 2, 3]

    with pytest.raises(ValueError) as err:
        m["not_allowed"] = asyncio.sleep(1)
