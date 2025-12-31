"""Tests for command precedence and filtering behavior."""

from mcp_guide.prompts.guide_prompt import _resolve_command_alias


class TestCommandPrecedence:
    """Tests for command precedence behavior."""

    def test_resolve_command_alias_returns_original_when_no_alias_found(self):
        """Test that _resolve_command_alias returns original command when no alias is found."""
        # Arrange
        commands = [{"name": "review", "aliases": ["rv"]}, {"name": "help", "aliases": ["h", "?"]}]

        # Act
        result = _resolve_command_alias("unknown", commands)

        # Assert
        assert result == "unknown"

    def test_resolve_command_alias_returns_command_name_when_alias_found(self):
        """Test that _resolve_command_alias returns command name when alias is found."""
        # Arrange
        commands = [{"name": "review", "aliases": ["rv", "check"]}, {"name": "help", "aliases": ["h", "?"]}]

        # Act
        result = _resolve_command_alias("rv", commands)

        # Assert
        assert result == "review"

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
        assert result == "help"


class TestUnderscoreFiltering:
    """Tests for underscore filtering in command discovery."""

    def test_command_validation_excludes_underscore_files(self):
        """Test that command validation excludes underscore-prefixed files."""
        from pathlib import Path

        from mcp_guide.utils.pattern_matching import is_valid_command

        # Arrange
        normal_file = Path("_commands/review.md")
        underscore_file = Path("_commands/_private.md")

        # Act & Assert
        assert is_valid_command(normal_file) is True
        assert is_valid_command(underscore_file) is False

    def test_command_validation_excludes_underscore_directories(self):
        """Test that command validation excludes files in underscore directories (except _commands)."""
        from pathlib import Path

        from mcp_guide.utils.pattern_matching import is_valid_command

        # Arrange
        commands_file = Path("_commands/review.md")  # Should be allowed
        private_file = Path("_private/secret.md")  # Should be rejected

        # Act & Assert
        assert is_valid_command(commands_file) is True
        assert is_valid_command(private_file) is False
