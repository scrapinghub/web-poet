from url_matcher import Patterns

from tests.po_lib import POBase
from web_poet import ItemPage, handle_urls


class PONestedPkgOverriden(ItemPage):
    ...


@handle_urls(
    include=["example.com", "example.org"],
    exclude=["/*.jpg|"],
    overrides=PONestedPkgOverriden,
)
class PONestedPkg(POBase):
    expected_overrides = PONestedPkgOverriden
    expected_patterns = Patterns(["example.com", "example.org"], ["/*.jpg|"])
    expected_data_type = None
    expected_meta = {}  # type: ignore
