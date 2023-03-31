from web_poet import HttpResponse, ItemPage, field


class FooPage(ItemPage[MyItem]):
    def __init__(self, response: HttpResponse):
        self.response = response

    @field
    def foo(self) -> str:
        return self.response.css(".foo").get()
