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
    """Tests for resolve_content_disposition precedence logic."""

    def test_defaults_to_user_information_when_no_files(self):
        assert resolve_content_disposition([]) == "user/information"

    def test_defaults_to_user_information_when_no_frontmatter(self):
        assert resolve_content_disposition([_make_file()]) == "user/information"

    def test_single_user_information(self):
        assert resolve_content_disposition([_make_file({"type": "user/information"})]) == "user/information"

    def test_single_agent_information(self):
        assert resolve_content_disposition([_make_file({"type": "agent/information"})]) == "agent/information"

    def test_single_agent_instruction(self):
        assert resolve_content_disposition([_make_file({"type": "agent/instruction"})]) == "agent/instruction"

    def test_agent_information_outranks_user_information(self):
        files = [_make_file({"type": "user/information"}), _make_file({"type": "agent/information"})]
        assert resolve_content_disposition(files) == "agent/information"

    def test_agent_instruction_outranks_all(self):
        files = [
            _make_file({"type": "user/information"}),
            _make_file({"type": "agent/information"}),
            _make_file({"type": "agent/instruction"}),
        ]
        assert resolve_content_disposition(files) == "agent/instruction"

    def test_unknown_type_ignored(self):
        files = [_make_file({"type": "unknown/type"}), _make_file({"type": "user/information"})]
        assert resolve_content_disposition(files) == "user/information"

    @pytest.mark.parametrize(
        "types,expected",
        [
            (["agent/instruction", "user/information"], "agent/instruction"),
            (["agent/information", "agent/instruction"], "agent/instruction"),
            (["user/information", "user/information"], "user/information"),
        ],
    )
    def test_precedence_combinations(self, types, expected):
        files = [_make_file({"type": t}) for t in types]
        assert resolve_content_disposition(files) == expected


class TestPrependExportFrontmatter:
    """Tests for prepend_export_frontmatter serialisation."""

    def test_returns_none_for_none_content(self):
        assert prepend_export_frontmatter(None, "user/information", None) is None

    def test_prepends_type_only(self):
        result = prepend_export_frontmatter("body", "agent/information", None)
        frontmatter, body_part = result.split("---\n")[1:3]
        assert yaml.safe_load(frontmatter) == {"type": "agent/information"}
        assert body_part == "body"

    def test_prepends_type_and_instruction(self):
        result = prepend_export_frontmatter("body", "user/information", "Display this to the user")
        frontmatter, body_part = result.split("---\n")[1:3]
        parsed = yaml.safe_load(frontmatter)
        assert parsed["type"] == "user/information"
        assert parsed["instruction"] == "Display this to the user"
        assert body_part == "body"

    def test_multiline_instruction(self):
        result = prepend_export_frontmatter("body", "agent/instruction", "Line one\nLine two")
        frontmatter, body_part = result.split("---\n")[1:3]
        parsed = yaml.safe_load(frontmatter)
        assert parsed["type"] == "agent/instruction"
        assert "Line one" in parsed["instruction"]
        assert "Line two" in parsed["instruction"]
        assert body_part == "body"

    def test_no_disposition_no_instruction_returns_content_unchanged(self):
        assert prepend_export_frontmatter("body", None, None) == "body"

    def test_body_preserved_after_frontmatter(self):
        body = "# Title\n\nSome content here."
        result = prepend_export_frontmatter(body, "user/information", None)
        assert result.endswith(body)

    def test_special_yaml_characters_in_instruction(self):
        result = prepend_export_frontmatter("body", "agent/instruction", 'Use key: value and "quotes"')
        frontmatter, body_part = result.split("---\n")[1:3]
        parsed = yaml.safe_load(frontmatter)
        assert parsed["instruction"] == 'Use key: value and "quotes"'
        assert body_part == "body"
