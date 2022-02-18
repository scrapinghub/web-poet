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


def test_meta():
    meta = Meta(x="hi", y=2.2, z={"k": "v"})
    assert meta.x == "hi"
    assert meta.y == 2.2
    assert meta.z == {"k": "v"}
    assert meta.not_existing_field is None

    del meta.z
    assert meta.z is None

    # Deleting non-existing fields should not err out.
    del meta.no_existing_field
    assert meta.not_existing_field is None

    meta.new_field = "new"
    assert meta.new_field == "new"

    str(meta) == "Meta(x='hi', y=2.2, new='new')"
