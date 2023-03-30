from attrs import define

from web_poet import HttpResponse, Injectable


@define
class FooPage(Injectable):
    response: HttpResponse

    def to_item(self) -> dict:
        return {"foo": self.response.css(".foo").get()}
