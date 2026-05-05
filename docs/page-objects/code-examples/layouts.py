import attrs

from web_poet import HttpResponse, ItemPage, WebPage, field, layout_switch


@attrs.define
class Product:
    title: str
    price: str


class ProductLayoutA(WebPage[Product]):
    @field
    def title(self):
        return self.css("h1::text").get()

    @field
    def price(self):
        return self.css(".price::text").get()


class ProductLayoutB(WebPage[Product]):
    @field
    def title(self):
        return self.css(".title::text").get()


@layout_switch()
@attrs.define
class ProductPage(ItemPage[Product]):
    response: HttpResponse
    layout_a: ProductLayoutA
    layout_b: ProductLayoutB

    def get_layout(self) -> ItemPage[Product]:
        if self.response.css(".layout-a"):
            return self.layout_a
        return self.layout_b

    @field
    def price(self):
        return "N/A"
