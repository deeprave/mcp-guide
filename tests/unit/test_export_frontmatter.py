"""Tests for export frontmatter resolution and serialisation."""

from datetime import datetime
from pathlib import Path

import pytest
import yaml

from mcp_guide.content.utils import prepend_export_frontmatter, resolve_content_disposition
from mcp_guide.discovery.files import FileInfo


def _make_file(frontmatter: dict | None = None) -> FileInfo:
    fi = FileInfo(path=Path("test.md"), size=0, content_size=0, mtime=datetime.now(), name="test.md")
    fi.frontmatter = frontmatter or {}
    return fi


class TestResolveContentDisposition:
    """Disposition precedence is independent of input order."""

    @pytest.mark.parametrize(
        "types,expected",
        [
            ([], "user/information"),
            ([None], "user/information"),
            (["user/information"], "user/information"),
            (["agent/information"], "agent/information"),
            (["agent/instruction"], "agent/instruction"),
            (["unknown/type"], None),
            (["unknown/type", "user/information"], "user/information"),
            (["user/information", "agent/information"], "agent/information"),
            (["user/information", "agent/information", "agent/instruction"], "agent/instruction"),
        ],
    )
    def test_precedence(self, types, expected):
        for ordered in (types, list(reversed(types))):
            files = [_make_file({"type": kind}) if kind is not None else _make_file() for kind in ordered]
            assert resolve_content_disposition(files) == expected


class TestPrependExportFrontmatter:
    """Tests for prepend_export_frontmatter serialisation."""

    @staticmethod
    def _parse_frontmatter(result: str) -> tuple[dict, str]:
        frontmatter, body = result.split("---\n")[1:3]
        return yaml.safe_load(frontmatter), body

    def test_returns_none_for_none_content(self):
        assert prepend_export_frontmatter(None, "user/information", None) is None

    def test_prepends_type_only(self):
        content = "# Title\n\nSome content here."
        result = prepend_export_frontmatter(content, "agent/information", None)
        parsed, body = self._parse_frontmatter(result)
        assert parsed == {"type": "agent/information"}
        assert body == content

    def test_prepends_type_and_instruction(self):
        result = prepend_export_frontmatter("body", "user/information", "Display this to the user")
        parsed, body = self._parse_frontmatter(result)
        assert parsed["type"] == "user/information"
        assert parsed["instruction"] == "Display this to the user"
        assert "instruction: Display this to the user" in result
        assert "instruction: >" not in result
        assert body == "body"

    def test_multiline_instruction(self):
        result = prepend_export_frontmatter("body", "agent/instruction", "Line one\nLine two")
        parsed, body = self._parse_frontmatter(result)
        assert parsed["type"] == "agent/instruction"
        assert parsed["instruction"] == "Line one\nLine two"
        assert "instruction: |" in result
        assert body == "body"

    def test_instruction_indentation_and_empty_lines_are_preserved(self):
        result = prepend_export_frontmatter(
            "body",
            "agent/instruction",
            "Line one.\n\n  Line two.\n\tLine three.",
        )
        parsed, body = self._parse_frontmatter(result)
        assert parsed["instruction"] == "Line one.\n\n  Line two.\n\tLine three."
        assert body == "body"

    def test_no_disposition_no_instruction_returns_content_unchanged(self):
        assert prepend_export_frontmatter("body", None, None) == "body"

    def test_special_yaml_characters_in_instruction(self):
        result = prepend_export_frontmatter("body", "agent/instruction", 'Use key: value and "quotes"')
        parsed, body = self._parse_frontmatter(result)
        assert parsed["instruction"] == 'Use key: value and "quotes"'
        assert body == "body"
