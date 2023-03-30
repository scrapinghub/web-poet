from web_poet import HttpResponse, Injectable


class FooPage(Injectable):
    def __init__(self, response: HttpResponse):
        self.response = response

    def to_item(self) -> dict:
        return {"foo": self.response.css(".foo").get()}
