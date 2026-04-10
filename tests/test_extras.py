import pytest


def test_framework():
    with pytest.raises(ImportError, match="web-poet\\[framework\\]"):
        import web_poet.framework  # noqa: F401,PLC0415
