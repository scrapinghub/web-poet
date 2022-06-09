from url_matcher import Patterns

from tests.po_lib import POBase
from web_poet import handle_urls


class PONestedModuleOverriden:
    ...


@handle_urls(include=["example.com", "example.org"], exclude=["/*.jpg|"], overrides=PONestedModuleOverriden)
class PONestedModule(POBase):
    expected_overrides = PONestedModuleOverriden
    expected_patterns = Patterns(include=["example.com", "example.org"], exclude=["/*.jpg|"])
    expected_meta = {}  # type: ignore
