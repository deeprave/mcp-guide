"""Tests for CLI argument parsing."""

import os
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from mcp_guide.cli import ServerConfig, parse_args


class TestServerConfig:
    """Tests for ServerConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ServerConfig()
        assert config.log_level == "INFO"
        assert config.log_file is None
        assert config.log_json is False
        assert config.tool_prefix == "guide"
        assert config.cli_error is None
        assert config.should_exit is False


class TestParseArgs:
    """Tests for parse_args function."""

    def test_defaults_no_args_no_env(self) -> None:
        """Test default values when no args or env vars provided."""
        with patch("sys.argv", ["mcp-guide"]):
            with patch.dict(os.environ, {}, clear=True):
                config = parse_args()
                assert config.log_level == "INFO"
                assert config.log_file is None
                assert config.log_json is False
                assert config.tool_prefix == "guide"

    def test_help_sets_should_exit_and_no_error(self) -> None:
        """`--help` should mark config for exit without an error."""
        with patch("sys.argv", ["mcp-guide", "--help"]):
            config = parse_args()
            assert config.should_exit is True
            assert config.cli_error is None

    def test_version_sets_should_exit_and_no_error(self) -> None:
        """`--version` should mark config for exit without an error."""
        with patch("sys.argv", ["mcp-guide", "--version"]):
            config = parse_args()
            assert config.should_exit is True
            assert config.cli_error is None

    def test_click_abort_populates_cli_error_and_sets_should_exit(self) -> None:
        """Simulate Ctrl+C (click.Abort) and ensure it is captured on the config."""
        import click

        def aborting_invoke(self, ctx):
            raise click.Abort()

        with patch.object(click.Command, "invoke", aborting_invoke):
            with patch("sys.argv", ["mcp-guide"]):
                config = parse_args()

                assert isinstance(config.cli_error, click.Abort)
                assert config.should_exit is True

    def test_cli_args_override_defaults(self) -> None:
        """Test CLI arguments override default values."""
        with patch("sys.argv", ["mcp-guide", "--log-level", "DEBUG", "--log-json"]):
            with patch.dict(os.environ, {}, clear=True):
                config = parse_args()
                assert config.log_level == "DEBUG"
                assert config.log_json is True

    def test_envvar_override_defaults(self) -> None:
        """Test environment variables override defaults."""
        with patch("sys.argv", ["mcp-guide"]):
            with patch.dict(
                os.environ,
                {"MG_LOG_LEVEL": "WARNING", "MG_LOG_FILE": "/tmp/test.log"},
                clear=True,
            ):
                config = parse_args()
                assert config.log_level == "WARNING"
                assert config.log_file == "/tmp/test.log"

    def test_cli_args_override_envvar(self) -> None:
        """Test CLI arguments override environment variables."""
        with patch("sys.argv", ["mcp-guide", "--log-level", "ERROR"]):
            with patch.dict(os.environ, {"MG_LOG_LEVEL": "DEBUG"}, clear=True):
                config = parse_args()
                assert config.log_level == "ERROR"

    def test_no_tool_prefix_flag(self) -> None:
        """Test --no-tool-prefix sets empty string."""
        with patch("sys.argv", ["mcp-guide", "--no-tool-prefix"]):
            with patch.dict(os.environ, {}, clear=True):
                config = parse_args()
                assert config.tool_prefix == ""

    def test_no_tool_prefix_overrides_envvar(self) -> None:
        """Test --no-tool-prefix overrides environment variable."""
        with patch("sys.argv", ["mcp-guide", "--no-tool-prefix"]):
            with patch.dict(os.environ, {"MCP_TOOL_PREFIX": "custom"}, clear=True):
                config = parse_args()
                assert config.tool_prefix == ""

    def test_tool_prefix_cli_arg(self) -> None:
        """Test --tool-prefix sets custom prefix."""
        with patch("sys.argv", ["mcp-guide", "--tool-prefix", "myapp"]):
            with patch.dict(os.environ, {}, clear=True):
                config = parse_args()
                assert config.tool_prefix == "myapp"

    def test_tool_prefix_envvar(self) -> None:
        """Test MCP_TOOL_PREFIX environment variable."""
        with patch("sys.argv", ["mcp-guide"]):
            with patch.dict(os.environ, {"MCP_TOOL_PREFIX": "custom"}, clear=True):
                config = parse_args()
                assert config.tool_prefix == "custom"

    def test_mutual_exclusion_error(self) -> None:
        """Test error when both --tool-prefix and --no-tool-prefix provided."""
        import click

        with patch("sys.argv", ["mcp-guide", "--tool-prefix", "test", "--no-tool-prefix"]):
            with patch.dict(os.environ, {}, clear=True):
                config = parse_args()
                # Should have error stored
                assert config.cli_error is not None
                assert isinstance(config.cli_error, click.UsageError)
                assert "Cannot use both" in config.cli_error.format_message()
                # Should not exit (invalid args, not help/version)
                assert config.should_exit is False

    def test_invalid_log_level_error(self) -> None:
        """Test invalid log level stores BadParameter exception."""
        import click

        with patch("sys.argv", ["mcp-guide", "--log-level", "INVALID"]):
            with patch.dict(os.environ, {}, clear=True):
                config = parse_args()
                # Should have error stored
                assert config.cli_error is not None
                assert isinstance(config.cli_error, click.BadParameter)
                # Should not exit
                assert config.should_exit is False

    def test_all_log_levels(self) -> None:
        """Test all valid log levels."""
        levels = ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR"]
        for level in levels:
            with patch("sys.argv", ["mcp-guide", "--log-level", level]):
                with patch.dict(os.environ, {}, clear=True):
                    config = parse_args()
                    assert config.log_level == level.upper()

    def test_log_level_case_insensitive(self) -> None:
        """Test log level is case insensitive."""
        with patch("sys.argv", ["mcp-guide", "--log-level", "debug"]):
            with patch.dict(os.environ, {}, clear=True):
                config = parse_args()
                assert config.log_level == "DEBUG"

    def test_log_file_path(self) -> None:
        """Test --log-file sets file path."""
        with patch("sys.argv", ["mcp-guide", "--log-file", "/var/log/mcp.log"]):
            with patch.dict(os.environ, {}, clear=True):
                config = parse_args()
                assert config.log_file == "/var/log/mcp.log"
