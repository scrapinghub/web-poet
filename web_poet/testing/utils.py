from __future__ import annotations

from typing import TYPE_CHECKING, Any

from _pytest.assertion.util import (
    assertrepr_compare,
    dummy_highlighter,
    get_assertion_text_diff_style,
)

if TYPE_CHECKING:
    import pytest


def comparison_error_message(
    config: pytest.Config, op: str, expected: Any, got: Any, prefix: str = ""
) -> str:
    """Generate an error message"""
    lines = [prefix] if prefix else []

    explanation_lines = list(
        assertrepr_compare(
            op=op,
            left=got,
            right=expected,
            verbose=getattr(config.option, "verbose", 0),
            highlighter=dummy_highlighter,
            assertion_text_diff_style=get_assertion_text_diff_style(config),
        )
    )
    if explanation_lines:
        lines.extend(explanation_lines)
    else:
        lines.append(f"Expected: {expected!r}, got: {got!r}")

    return "\n".join(lines)
