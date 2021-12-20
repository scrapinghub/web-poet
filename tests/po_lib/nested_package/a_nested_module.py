from url_matcher import Patterns

from tests.po_lib import POBase, secondary_registry
from web_poet import handle_urls


class PONestedModuleOverriden:
    ...


class PONestedModuleOverridenSecondary:
    ...


@handle_urls(include=["example.com", "example.org"], exclude=["/*.jpg|"], overrides=PONestedModuleOverriden)
@secondary_registry.handle_urls("example.com", PONestedModuleOverridenSecondary)
class PONestedModule(POBase):
    expected_overrides = PONestedModuleOverriden
    expected_patterns = Patterns(include=["example.com", "example.org"], exclude=["/*.jpg|"])
    expected_meta = {}  # type: ignore

