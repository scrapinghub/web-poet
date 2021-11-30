from url_matcher import Patterns

from web_poet import handle_urls


class POModuleOverriden:
    ...


@handle_urls("example.com", overrides=POModuleOverriden, extra_arg="foo")
class POModule(object):
    expected_overrides = POModuleOverriden
    expected_patterns = Patterns(["example.com"])
    expected_meta = {"extra_arg": "foo"}

