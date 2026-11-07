"""Instruction resolution preserves explicit priority for the ^-important prefix."""

import pytest

from mcp_guide.render.frontmatter import resolve_instruction


@pytest.mark.parametrize(
    "instruction, expected",
    [
        ("Display this content", ("Display this content", False)),
        ("^ Override parent instruction", ("Override parent instruction", True)),
        ("^   Override with spaces", ("Override with spaces", True)),
        ("^", (None, True)),
    ],
    ids=["explicit", "important", "important-whitespace", "empty-important"],
)
def test_explicit_instruction(instruction, expected):
    assert resolve_instruction({"instruction": instruction}) == expected
