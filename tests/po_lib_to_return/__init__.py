import attrs
from url_matcher import Patterns

from web_poet import Injectable, ItemPage, Returns, field, handle_urls, item_from_fields


@attrs.define
class Product:
    name: str
    price: float


@attrs.define
class ProductSeparate:
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
class ProductFewerFields:
    name: str


@handle_urls("example.com")
class SomePage(ItemPage):
    """A PO which is only marked by the URL pattern."""

    expected_instead_of = None
    expected_patterns = Patterns(["example.com"])
    expected_to_return = None
    expected_meta = {}

    @field
    def name(self) -> str:
        return "some name"


@handle_urls("example.com")
class ProductPage(ItemPage[Product]):
    """A base PO to populate the Product item's fields."""

    expected_instead_of = None
    expected_patterns = Patterns(["example.com"])
    expected_to_return = Product
    expected_meta = {}

    @field
    def name(self) -> str:
        return "name"

    @field
    def price(self) -> float:
        return 12.99


@handle_urls("example.com", instead_of=ProductPage)
class ImprovedProductPage(ProductPage):
    """A custom PO inheriting from a base PO which alters some field values."""

    expected_instead_of = ProductPage
    expected_patterns = Patterns(["example.com"])
    expected_to_return = Product
    expected_meta = {}

    @field
    def name(self) -> str:
        return "improved name"


@handle_urls("example.com", instead_of=ProductPage)
class SeparateProductPage(ItemPage[ProductSeparate]):
    """Same case as with ``ImprovedProductPage`` but it doesn't inherit from
    ``ProductPage``.
    """

    expected_instead_of = ProductPage
    expected_patterns = Patterns(["example.com"])
    expected_to_return = ProductSeparate
    expected_meta = {}

    @field
    def name(self) -> str:
        return "separate name"


@handle_urls("example.com", instead_of=ProductPage)
class SimilarProductPage(ProductPage, Returns[ProductSimilar]):
    """A custom PO inheriting from a base PO returning the same fields but in
    a different item class.
    """

    expected_instead_of = ProductPage
    expected_patterns = Patterns(["example.com"])
    expected_to_return = ProductSimilar
    expected_meta = {}


@handle_urls("example.com", instead_of=ProductPage)
class MoreProductPage(ProductPage, Returns[ProductMoreFields]):
    """A custom PO inheriting from a base PO returning more items using a
    different item class.
    """

    expected_instead_of = ProductPage
    expected_patterns = Patterns(["example.com"])
    expected_to_return = ProductMoreFields
    expected_meta = {}

    @field
    def brand(self) -> str:
        return "brand"


@handle_urls("example.com", instead_of=ProductPage)
class LessProductPage(
    ProductPage, Returns[ProductFewerFields], skip_nonitem_fields=True
):
    """A custom PO inheriting from a base PO returning less items using a
    different item class.
    """

    expected_instead_of = ProductPage
    expected_patterns = Patterns(["example.com"])
    expected_to_return = ProductFewerFields
    expected_meta = {}

    @field
    def brand(self) -> str:
        return "brand"


@handle_urls("example.com", instead_of=ProductPage, to_return=ProductSimilar)
class CustomProductPage(ProductPage, Returns[Product]):
    """A custom PO inheriting from a base PO returning the same fields but in
    a different item class.

    This PO is the same with ``SimilarProductPage`` but passes a ``to_return``
    in the ``@handle_urls`` decorator.

    This tests the case that the type passed via the ``to_return`` parameter
    from ``@handle_urls`` takes priority.
    """

    expected_instead_of = ProductPage
    expected_patterns = Patterns(["example.com"])
    expected_to_return = ProductSimilar
    expected_meta = {}


@handle_urls("example.com", instead_of=ProductPage, to_return=ProductSimilar)
class CustomProductPageNoReturns(ProductPage):
    """Same case as with ``CustomProductPage`` but doesn't inherit from
    ``Returns[Product]``.
    """

    expected_instead_of = ProductPage
    expected_patterns = Patterns(["example.com"])
    expected_to_return = ProductSimilar
    expected_meta = {}


@handle_urls("example.com", to_return=Product)
class CustomProductPageDataTypeOnly(Injectable):
    """A PO that doesn't inherit from ``ItemPage`` and ``WebPage`` which means
    it doesn't inherit from the ``Returns`` class.

    This tests the case that the ``to_return`` parameter in ``@handle_urls``
    should properly use it in the rules.
    """

    expected_instead_of = None
    expected_patterns = Patterns(["example.com"])
    expected_to_return = Product
    expected_meta = {}

    @field
    def name(self) -> str:
        return "name"

    @field
    def price(self) -> float:
        return 12.99

    async def to_item(self) -> Product:
        return await item_from_fields(self, item_cls=Product)
