from url_matcher import Patterns

from tests.po_lib import POBase
from web_poet import ItemPage, handle_urls


class PONestedPkgOverriden(ItemPage):
    ...


@handle_urls(
    include=["example.com", "example.org"],
    exclude=["/*.jpg|"],
    instead_of=PONestedPkgOverriden,
)
class PONestedPkg(POBase):
    expected_instead_of = PONestedPkgOverriden
    expected_patterns = Patterns(["example.com", "example.org"], ["/*.jpg|"])
    expected_to_return = None
    expected_meta = {}  # type: ignore
