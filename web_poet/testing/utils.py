from __future__ import annotations

from typing import Any

import _pytest.assertion.util as assertion_util
import pytest


def comparison_error_message(
    config: pytest.Config, op: str, expected: Any, got: Any, prefix: str = ""
) -> str:
    """Generate an error message"""
    lines = [prefix] if prefix else []

    # assertrepr_compare() signature was changed in 9.1.0 in PRs 14418, 14425 and 14546
    if pytest.version_tuple >= (9, 1, 0):
        explanation_lines = list(
            assertion_util.assertrepr_compare(
                op=op,
                left=got,
                right=expected,
                verbose=config.get_verbosity(pytest.Config.VERBOSITY_ASSERTIONS),
                highlighter=assertion_util.dummy_highlighter,
                assertion_text_diff_style=assertion_util.get_assertion_text_diff_style(
                    config
                ),
            )
        )
    else:
        explanation_lines = assertion_util.assertrepr_compare(  # type: ignore[call-arg,assignment]
            config=config, op=op, left=got, right=expected
        )
    if explanation_lines:
        lines.extend(explanation_lines)
    else:
        lines.append(f"Expected: {expected!r}, got: {got!r}")

    return "\n".join(lines)
