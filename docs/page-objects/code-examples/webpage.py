from web_poet import WebPage, field


class FooPage(WebPage[dict]):
    @field
    def foo(self) -> str:
        return self.css(".foo").get()
