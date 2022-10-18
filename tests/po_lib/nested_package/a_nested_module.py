from url_matcher import Patterns

from tests.po_lib import POBase
from web_poet import ItemPage, handle_urls


class PONestedModuleOverriden(ItemPage):
    ...


@handle_urls(
    include=["example.com", "example.org"],
    exclude=["/*.jpg|"],
    instead_of=PONestedModuleOverriden,
)
class PONestedModule(POBase):
    expected_instead_of = PONestedModuleOverriden
    expected_patterns = Patterns(
        include=["example.com", "example.org"], exclude=["/*.jpg|"]
    )
    expected_to_return = None
    expected_meta = {}  # type: ignore
