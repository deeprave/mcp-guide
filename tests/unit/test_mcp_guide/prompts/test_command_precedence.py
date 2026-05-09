"""Tests for command precedence and filtering behavior."""

from pathlib import Path

import pytest

try:
    from mcp_guide.discovery.files import FileInfo
    from mcp_guide.prompts.guide_prompt import _build_command_context, _merge_alias_kwargs, _resolve_command_alias
    from mcp_guide.render.context import TemplateContext
except AttributeError:
    # Skip tests if mcp is not initialized
    pytest.skip("MCP server not initialized", allow_module_level=True)


class TestCommandPrecedence:
    """Tests for command precedence behavior."""

    def test_resolve_command_alias_returns_original_when_no_alias_found(self):
        """Test that _resolve_command_alias returns original command when no alias is found."""
        # Arrange
        commands = [{"name": "review", "aliases": ["rv"]}, {"name": "help", "aliases": ["h"]}]

        # Act
        result = _resolve_command_alias("unknown", commands)

        # Assert
        assert result.command_path == "unknown"
        assert result.implied_kwargs == {}

    def test_resolve_command_alias_returns_command_name_when_alias_found(self):
        """Test that _resolve_command_alias returns command name when alias is found."""
        # Arrange
        commands = [
            {
                "name": "review",
                "aliases": ["rv", "check?verbose"],
                "alias_metadata": [
                    {"raw": "rv", "path": "rv", "implied_kwargs": {}},
                    {"raw": "check?verbose", "path": "check", "implied_kwargs": {"verbose": True}},
                ],
            },
            {"name": "help", "aliases": ["h"]},
        ]

        # Act
        result = _resolve_command_alias("rv", commands)

        # Assert
        assert result.command_path == "review"
        assert result.implied_kwargs == {}

    def test_resolve_command_alias_returns_alias_implied_kwargs(self):
        """Test that alias metadata supplies default kwargs for the resolved command."""
        commands = [
            {
                "name": "project/project",
                "aliases": ["project?verbose"],
                "alias_metadata": [{"raw": "project?verbose", "path": "project", "implied_kwargs": {"verbose": True}}],
            }
        ]

        result = _resolve_command_alias("project", commands)

        assert result.command_path == "project/project"
        assert result.implied_kwargs == {"verbose": True}

    def test_resolve_command_alias_raw_query_alias_preserves_implied_kwargs(self):
        """Prompt-style raw query aliases should retain their parsed defaults."""
        commands = [
            {
                "name": "handoff",
                "aliases": ["save-context?write"],
                "alias_metadata": [
                    {"raw": "save-context?write", "path": "save-context", "implied_kwargs": {"write": True}}
                ],
            }
        ]

        result = _resolve_command_alias("save-context?write", commands)

        assert result.command_path == "handoff"
        assert result.implied_kwargs == {"write": True}

    def test_resolve_command_alias_allows_additional_query_kwargs(self):
        """Prompt aliases should match by path and preserve extra query kwargs."""
        commands = [
            {
                "name": "handoff",
                "aliases": ["save-context?write"],
                "alias_metadata": [
                    {"raw": "save-context?write", "path": "save-context", "implied_kwargs": {"write": True}}
                ],
            }
        ]

        result = _resolve_command_alias("save-context?write&force", commands)

        assert result.command_path == "handoff"
        assert result.implied_kwargs == {"write": True, "force": True}

    def test_resolve_command_alias_handles_missing_aliases_field(self):
        """Test that _resolve_command_alias handles commands without aliases field."""
        # Arrange
        commands = [
            {"name": "review"},  # No aliases field
            {"name": "help", "aliases": ["h"]},
        ]

        # Act
        result = _resolve_command_alias("h", commands)

        # Assert
        assert result.command_path == "help"
        assert result.implied_kwargs == {}

    def test_merge_alias_kwargs_preserves_explicit_values(self):
        """Explicit caller kwargs should override alias defaults."""
        merged = _merge_alias_kwargs(default_kwargs={"verbose": True, "table": True}, override_kwargs={"verbose": False})

        assert merged == {"verbose": False, "table": True}

    def test_build_command_context_help_matches_raw_alias_metadata(self):
        """Help lookup should match raw query aliases through alias metadata."""
        file_info = FileInfo(path=Path("help.md"), size=0, content_size=0, mtime=0, name="help.md")
        commands = [
            {
                "name": "project/project",
                "aliases": [],
                "alias_metadata": [
                    {"raw": "project?verbose", "path": "project", "implied_kwargs": {"verbose": True}}
                ],
            }
        ]

        context = _build_command_context(
            TemplateContext({}),
            "help",
            file_info,
            kwargs={},
            args=["project?verbose"],
            commands=commands,
        )

        assert context["command_help"]["name"] == "project/project"

    def test_build_command_context_help_matches_alias_with_additional_query(self):
        """Help lookup should normalize query-bearing alias requests."""
        file_info = FileInfo(path=Path("help.md"), size=0, content_size=0, mtime=0, name="help.md")
        commands = [
            {
                "name": "project/project",
                "aliases": [],
                "alias_metadata": [
                    {"raw": "project?verbose", "path": "project", "implied_kwargs": {"verbose": True}}
                ],
            }
        ]

        context = _build_command_context(
            TemplateContext({}),
            "help",
            file_info,
            kwargs={},
            args=["project?verbose&table"],
            commands=commands,
        )

        assert context["command_help"]["name"] == "project/project"


class TestUnderscoreFiltering:
    """Tests for underscore filtering in command discovery."""

    def test_command_validation_excludes_underscore_files(self):
        """Test that command validation excludes underscore-prefixed files."""
        from pathlib import Path

        from mcp_guide.discovery.patterns import is_valid_command

        # Arrange
        normal_file = Path("_commands/review.md")
        underscore_file = Path("_commands/_private.md")

        # Act & Assert
        assert is_valid_command(normal_file) is True
        assert is_valid_command(underscore_file) is False

    def test_command_validation_excludes_underscore_directories(self):
        """Test that command validation excludes files in underscore directories (except _commands)."""
        from pathlib import Path

        from mcp_guide.discovery.patterns import is_valid_command

        # Arrange
        commands_file = Path("_commands/review.md")  # Should be allowed
        private_file = Path("_private/secret.md")  # Should be rejected

        # Act & Assert
        assert is_valid_command(commands_file) is True
        assert is_valid_command(private_file) is False
