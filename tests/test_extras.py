import pytest


def test_simple_framework():
    with pytest.raises(ImportError, match="simple_framework"):
        import web_poet.simple_framework  # noqa: F401,PLC0415
