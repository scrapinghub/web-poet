from url_matcher import Patterns

from web_poet.meta import handle_urls


class PONestedModuleOverriden:
    ...


class PONestedModuleOverridenSecondary:
    ...


@handle_urls(include=["example.com", "example.org"], exclude=["/*.jpg|"], overrides=PONestedModuleOverriden)
@handle_urls("example.com", PONestedModuleOverridenSecondary, namespace="secondary")
class PONestedModule(object):
    expected_overrides = PONestedModuleOverriden
    expected_patterns = Patterns(include=["example.com", "example.org"], exclude=["/*.jpg|"])

