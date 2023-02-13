import pytest
from _pytest.assertion.util import assertrepr_compare


def comparison_error_message(
    config: "pytest.Config", op: str, expected, got, prefix: str = ""
) -> str:
    """Generate an error message"""
    lines = [prefix] if prefix else []

    explanation_lines = assertrepr_compare(
        config=config, op=op, left=got, right=expected
    )
    if explanation_lines:
        lines.extend(explanation_lines)
    else:
        lines.append(f"Expected: {expected!r}, got: {got!r}")

    return "\n".join(lines)
