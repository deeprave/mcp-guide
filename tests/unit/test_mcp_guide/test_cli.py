"""Tests for CLI argument parsing."""

import os
from unittest.mock import patch

from mcp_guide.cli import parse_args


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
                assert config.tool_prefix == ""
                assert config.use_pwd is False

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
        with patch(
            "sys.argv",
            [
                "mcp-guide",
                "--log-level",
                "DEBUG",
                "--log-json",
                "--tool-prefix",
                "myapp",
                "--log-file",
                "/var/log/mcp.log",
                "--use-pwd",
                "--docroot",
                "/custom/path",
                "--configdir",
                "/custom/config",
            ],
        ):
            with patch.dict(os.environ, {}, clear=True):
                config = parse_args()
                assert config.log_level == "DEBUG"
                assert config.log_json is True
                assert config.tool_prefix == "myapp"
                assert config.log_file == "/var/log/mcp.log"
                assert config.use_pwd is True
                assert config.docroot == "/custom/path"
                assert config.configdir == "/custom/config"

    def test_envvar_override_defaults(self) -> None:
        """Test environment variables override defaults."""
        with patch("sys.argv", ["mcp-guide"]):
            with patch.dict(
                os.environ,
                {
                    "MG_LOG_LEVEL": "WARNING",
                    "MG_LOG_FILE": "/tmp/test.log",
                    "MCP_TOOL_PREFIX": "custom",
                    "MG_USE_PWD": "1",
                },
                clear=True,
            ):
                config = parse_args()
                assert config.log_level == "WARNING"
                assert config.log_file == "/tmp/test.log"
                assert config.tool_prefix == "custom"
                assert config.use_pwd is True

    def test_cli_args_override_envvar(self) -> None:
        """Test CLI arguments override environment variables."""
        with patch("sys.argv", ["mcp-guide", "--log-level", "ERROR"]):
            with patch.dict(os.environ, {"MG_LOG_LEVEL": "DEBUG"}, clear=True):
                config = parse_args()
                assert config.log_level == "ERROR"

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
        levels = ["TRACE", "debug", "INFO", "WARNING", "ERROR"]
        for level in levels:
            with patch("sys.argv", ["mcp-guide", "--log-level", level]):
                with patch.dict(os.environ, {}, clear=True):
                    config = parse_args()
                    assert config.log_level == level.upper()
