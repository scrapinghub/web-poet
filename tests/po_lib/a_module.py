from url_matcher import Patterns

from tests.po_lib import POBase
from web_poet import ItemPage, handle_urls


class POModuleOverriden(ItemPage):
    ...


@handle_urls("example.com", instead_of=POModuleOverriden, extra_arg="foo")
class POModule(POBase):
    expected_instead_of = POModuleOverriden
    expected_patterns = Patterns(["example.com"])
    expected_to_return = None
    expected_meta = {"extra_arg": "foo"}  # type: ignore
