"""Tests for export_content path resolution logic."""

import pytest

from mcp_guide.tools.tool_content import _resolve_export_path


class TestResolveExportPath:
    """Tests for _resolve_export_path."""

    @pytest.mark.parametrize(
        "path, agent, flag, expected",
        [
            # Filename only → default export dir + .md
            ("myfile", "", None, ".knowledge/myfile.md"),
            # Filename with extension → default export dir
            ("myfile.md", "", None, ".knowledge/myfile.md"),
            # Filename with non-md extension → default export dir, keeps extension
            ("myfile.txt", "", None, ".knowledge/myfile.txt"),
            # Known agent → agent-specific dir
            ("myfile", "kiro", None, ".kiro/knowledge/myfile.md"),
            ("myfile", "claude-code", None, ".claude/knowledge/myfile.md"),
            ("myfile", "cursor", None, ".cursor/knowledge/myfile.md"),
            ("myfile", "copilot", None, ".github/instructions/knowledge/myfile.md"),
            ("myfile", "goose", None, ".goose/skills/myfile.md"),
            # Unknown agent → default
            ("myfile", "unknown-agent", None, ".knowledge/myfile.md"),
            # path-export flag overrides agent default
            ("myfile", "kiro", ".export/", ".export/myfile.md"),
            ("myfile.md", "kiro", "output/", "output/myfile.md"),
            # Path with directory → use as-is, add .md if missing
            ("docs/myfile", "", None, "docs/myfile.md"),
            ("docs/myfile.md", "", None, "docs/myfile.md"),
            (".docs/output.md", "", None, ".docs/output.md"),
            ("some/deep/path/file", "", None, "some/deep/path/file.md"),
            # Path with directory ignores agent and flag
            ("docs/myfile", "kiro", ".export/", "docs/myfile.md"),
        ],
        ids=[
            "filename-no-ext-default",
            "filename-md-ext-default",
            "filename-txt-ext-default",
            "agent-kiro",
            "agent-claude-code",
            "agent-cursor",
            "agent-copilot",
            "agent-goose",
            "agent-unknown",
            "flag-overrides-agent",
            "flag-with-ext",
            "dir-no-ext",
            "dir-with-ext",
            "dotdir-with-ext",
            "deep-dir-no-ext",
            "dir-ignores-agent-and-flag",
        ],
    )
    def test_resolve_export_path(self, path: str, agent: str, flag: str | None, expected: str) -> None:
        assert _resolve_export_path(path, agent, flag) == expected
