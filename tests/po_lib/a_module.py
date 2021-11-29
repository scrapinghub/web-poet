from url_matcher import Patterns

from web_poet.meta import handle_urls


class POModuleOverriden:
    ...


@handle_urls("example.com", overrides=POModuleOverriden)
class POModule(object):
    expected_overrides = POModuleOverriden
    expected_patterns = Patterns(["example.com"])

