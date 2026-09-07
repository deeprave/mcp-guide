"""Flag selection is checked through formatted output, not concrete classes."""

from datetime import datetime
from email import policy
from email.parser import Parser
from pathlib import Path

import pytest

from mcp_guide.content.formatters.selection import (
    ContentFormat,
    TemplateStyling,
    get_formatter_from_flag,
    get_styling_variables,
)
from mcp_guide.discovery.files import FileInfo
from mcp_guide.models import Category


@pytest.mark.anyio
@pytest.mark.parametrize("flag", ["none", "plain", "mime"])
async def test_content_flag_selects_the_requested_output(flag, tmp_path):
    files = [
        FileInfo(
            path=Path(name),
            name=name,
            content=content,
            size=len(content),
            content_size=len(content),
            mtime=datetime(2026, 1, 1),
            category=Category(name="docs", dir="docs", patterns=["*.txt"]),
        )
        for name, content in [("one.txt", "First"), ("two.txt", "Second")]
    ]
    result = await get_formatter_from_flag(ContentFormat.from_flag_value(flag)).format(files, tmp_path.joinpath)
    if flag == "none":
        assert result == "First\nSecond"
    elif flag == "plain":
        assert result == "--- one.txt ---\nFirst\n--- two.txt ---\nSecond"
    else:
        message = Parser(policy=policy.default).parsestr(result)
        assert message.get_content_type() == "multipart/mixed"
        parts = list(message.iter_parts())
        assert [part.get_payload().strip() for part in parts] == ["First", "Second"]
        assert [part["Content-Location"] for part in parts] == [
            "guide://docs/one.txt",
            "guide://docs/two.txt",
        ]


@pytest.mark.parametrize(
    "flag,bold,italic,headings",
    [("plain", "", "", False), ("headings", "", "", True), ("full", "**", "*", True)],
    ids=["plain", "headings", "full"],
)
def test_style_flag_produces_requested_markers(flag, bold, italic, headings):
    expected = {"b": bold, "i": italic}
    expected.update({f"h{level}": "#" * level + " " if headings else "" for level in range(1, 7)})
    assert get_styling_variables(TemplateStyling.from_flag_value(flag)) == expected


def test_missing_and_invalid_flags_use_unformatted_defaults():
    for value in (None, "invalid", "", 123):
        assert ContentFormat.from_flag_value(value) == ContentFormat.NONE
        assert TemplateStyling.from_flag_value(value) == TemplateStyling.PLAIN
