from web_poet import WebPage, field, handle_urls


@handle_urls("example.com")
class FooPage(WebPage[MyItem]):
    @field
    def foo(self) -> str:
        return self.css(".foo").get()
