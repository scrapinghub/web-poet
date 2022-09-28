import attrs
from url_matcher import Patterns

from web_poet import Injectable, ItemPage, Returns, field, handle_urls, item_from_fields


@attrs.define
class Product:
    name: str
    price: float


@attrs.define
class ProductSimilar:
    name: str
    price: float


@attrs.define
class ProductMoreFields(Product):
    brand: str


@attrs.define
class ProductLessFields:
    name: str


@handle_urls("example.com")
class ProductPage(ItemPage[Product]):
    """A base PO to populate the Product item's fields."""

    expected_overrides = None
    expected_patterns = Patterns(["example.com"])
    expected_data_type = Product
    expected_meta = {}

    @field
    def name(self) -> str:
        return "name"

    @field
    def price(self) -> float:
        return 12.99


@handle_urls("example.com", overrides=ProductPage)
class ImprovedProductPage(ProductPage):
    """A custom PO inheriting from a base PO which alters some field values."""

    expected_overrides = ProductPage
    expected_patterns = Patterns(["example.com"])
    expected_data_type = Product
    expected_meta = {}

    @field
    def name(self) -> str:
        return "improved name"


@handle_urls("example.com", overrides=ProductPage)
class SimilarProductPage(ProductPage, Returns[ProductSimilar]):
    """A custom PO inheriting from a base PO returning the same fields but in
    a different item class.
    """

    expected_overrides = ProductPage
    expected_patterns = Patterns(["example.com"])
    expected_data_type = ProductSimilar
    expected_meta = {}


@handle_urls("example.com", overrides=ProductPage)
class MoreProductPage(ProductPage, Returns[ProductMoreFields]):
    """A custom PO inheriting from a base PO returning more items using a
    different item class.
    """

    expected_overrides = ProductPage
    expected_patterns = Patterns(["example.com"])
    expected_data_type = ProductMoreFields
    expected_meta = {}

    @field
    def brand(self) -> str:
        return "brand"


@handle_urls("example.com", overrides=ProductPage)
class LessProductPage(
    ProductPage, Returns[ProductLessFields], skip_nonitem_fields=True
):
    """A custom PO inheriting from a base PO returning less items using a
    different item class.
    """

    expected_overrides = ProductPage
    expected_patterns = Patterns(["example.com"])
    expected_data_type = ProductLessFields
    expected_meta = {}

    @field
    def brand(self) -> str:
        return "brand"


@handle_urls("example.com", overrides=ProductPage, data_type=ProductSimilar)
class CustomProductPage(ProductPage, Returns[Product]):
    """A custom PO inheriting from a base PO returning the same fields but in
    a different item class.

    This PO is the same with ``SimilarProductPage`` but passes a ``data_type``
    in the ``@handle_urls`` decorator.

    This tests the case that the type inside ``Returns`` should be followed and
    the ``data_type`` parameter from ``@handle_urls`` is ignored.
    """

    expected_overrides = ProductPage
    expected_patterns = Patterns(["example.com"])
    expected_data_type = Product
    expected_meta = {}


@handle_urls("example.com", overrides=ProductPage, data_type=ProductSimilar)
class CustomProductPageNoReturns(ProductPage):
    """Same case as with ``CustomProductPage`` but doesn't inherit from
    ``Returns[Product]``.
    """

    expected_overrides = ProductPage
    expected_patterns = Patterns(["example.com"])
    expected_data_type = Product
    expected_meta = {}


@handle_urls("example.com", data_type=Product)
class CustomProductPageDataTypeOnly(Injectable):
    """A PO that doesn't inherit from ``ItemPage`` and ``WebPage`` which means
    it doesn't inherit from the ``Returns`` class.

    This tests the case that the ``data_Type`` parameter in ``@handle_urls``
    should properly use it in the rules.
    """

    expected_overrides = None
    expected_patterns = Patterns(["example.com"])
    expected_data_type = Product
    expected_meta = {}

    @field
    def name(self) -> str:
        return "name"

    @field
    def price(self) -> float:
        return 12.99

    async def to_item(self) -> Product:
        return await item_from_fields(self, item_cls=Product)
