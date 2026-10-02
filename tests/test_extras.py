from importlib.util import find_spec

import pytest


@pytest.mark.skipif(
    find_spec("niquests") is not None, reason="the framework extra is installed"
)
def test_framework():
    with pytest.raises(ImportError, match="web-poet\\[framework\\]"):
        import web_poet.framework  # noqa: F401,PLC0415


@pytest.mark.skipif(
    find_spec("frostwork") is not None, reason="the frostwork extra is installed"
)
def test_frostwork():
    from web_poet import WebPage  # noqa: PLC0415

    with pytest.raises(ImportError, match="web-poet\\[frostwork\\]"):

        class Page(WebPage, declarative_backend="frostwork"):
            pass
