from typing import get_type_hints

import pytest

import web_poet

EXPORTED = [getattr(web_poet, t) for t in dir(web_poet) if not t.startswith("_")]
EXPORTED_TYPES = [t for t in EXPORTED if isinstance(t, type)]


@pytest.mark.parametrize("t", EXPORTED_TYPES)
def test_get_type_hints(t: type) -> None:
    """Test that get_type_hints() works for all exported types."""
    get_type_hints(t)
