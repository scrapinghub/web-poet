from url_matcher import Patterns

from web_poet import handle_urls


class PONestedPkgOverriden:
    ...


@handle_urls(include=["example.com", "example.org"], exclude=["/*.jpg|"], overrides=PONestedPkgOverriden)
class PONestedPkg(object):
    expected_overrides = PONestedPkgOverriden
    expected_patterns = Patterns(["example.com", "example.org"], ["/*.jpg|"])
    expected_meta = {}
