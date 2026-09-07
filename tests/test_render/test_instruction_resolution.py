"""Instruction resolution preserves explicit priority and type-based defaults."""

import pytest

from mcp_guide.render.frontmatter import resolve_instruction
from mcp_guide.result_constants import INSTRUCTION_DISPLAY_ONLY


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


@pytest.mark.parametrize(
    "frontmatter, content_type",
    [
        ({"type": "user/information"}, "user/information"),
        ({}, None),
        (None, None),
        ({"instruction": 123}, None),
    ],
    ids=["type-default", "empty", "absent", "non-string"],
)
def test_default_instruction(frontmatter, content_type):
    assert resolve_instruction(frontmatter, content_type) == (INSTRUCTION_DISPLAY_ONLY, False)
