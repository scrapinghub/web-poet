from url_matcher import Patterns

from tests.po_lib import POBase
from web_poet import handle_urls


class POModuleOverriden:
    ...


@handle_urls("example.com", overrides=POModuleOverriden, extra_arg="foo")
class POModule(POBase):
    expected_overrides = POModuleOverriden
    expected_patterns = Patterns(["example.com"])
    expected_meta = {"extra_arg": "foo"}  # type: ignore

