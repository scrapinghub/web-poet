from web_poet import BrowserPage, field


class FooPage(BrowserPage[MyItem]):
    @field
    def foo(self) -> str:
        return self.css(".foo").get()
