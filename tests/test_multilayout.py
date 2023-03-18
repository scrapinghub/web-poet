"""Proof of concept of an approach to multi-layout support that involves
documenting best practices on how to handle it with the existing API, rather
than providing a new API for it."""

import attrs
import pytest

from web_poet import HttpResponse, ItemPage, field


@attrs.define
class Item:
    title: str
    text: str


@attrs.define
class Title:
    title: str


@attrs.define
class Text:
    text: str


@pytest.mark.asyncio
async def test_multiple_inheritance():

    html = b"""
        <!doctype html>
        <html>
        <head>
            <title>foo</title>
        </head>
            <text id="a">bar</text>
        </html>
    """

    @attrs.define
    class TitleAPage(ItemPage[Title]):
        response: HttpResponse

        @field
        def title(self):
            return self.response.css("title::text").get()

    @attrs.define
    class TitleBPage(ItemPage[Title]):
        response: HttpResponse

        @field
        def title(self):
            return self.response.css("h1::text").get()

    @attrs.define
    class TitleMultiLayout(ItemPage[Item]):
        response: HttpResponse
        title_a: TitleAPage
        title_b: TitleBPage

        # TODO: cache the result
        def __get_layout(self):
            if self.response.css("#a"):
                return self.title_a
            return self.title_b

        @field
        def title(self):
            return self.__get_layout().title

    @attrs.define
    class TextAPage(ItemPage[Text]):
        response: HttpResponse

        @field
        def text(self):
            return self.response.css("#a::text").get()

    @attrs.define
    class TextBPage(ItemPage[Text]):
        response: HttpResponse

        @field
        def text(self):
            return self.response.css("#b::text").get()

    @attrs.define
    class TitleAndTextMultiLayout(TitleMultiLayout):
        text_a: TextAPage
        text_b: TextBPage

        # TODO: cache the result
        def __get_layout(self):
            if self.response.css("#a"):
                return self.text_a
            return self.text_b

        @field
        def text(self):
            return self.__get_layout().text

    response = HttpResponse("https://example.com", body=html, encoding="utf8")
    title_a = TitleAPage(response=response)
    title_b = TitleBPage(response=response)
    text_a = TextAPage(response=response)
    text_b = TextBPage(response=response)
    layout = TitleAndTextMultiLayout(
        response=response,
        title_a=title_a,
        title_b=title_b,
        text_a=text_a,
        text_b=text_b,
    )

    assert await layout.to_item() == Item(title="foo", text="bar")
