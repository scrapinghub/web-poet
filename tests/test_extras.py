import pytest


def test_framework():
    with pytest.raises(ImportError, match="web-poet\\[framework\\]"):
        import web_poet.framework  # noqa: F401,PLC0415


def test_llm():
    with pytest.raises(ImportError, match="web-poet\\[llm\\]"):
        import web_poet.llm  # noqa: F401,PLC0415
