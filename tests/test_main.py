"""Tests for main entry point."""

from unittest.mock import MagicMock, patch


class TestHandleCliError:
    """Tests for _handle_cli_error behavior (exit vs. log-and-continue)."""

    @patch("mcp_guide.main.sys.exit")
    @patch("logging.getLogger")
    def test_no_cli_error_no_logging_no_exit(
        self,
        mock_get_logger: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """When cli_error is None, nothing is logged and process does not exit."""
        from mcp_guide.cli import ServerConfig
        from mcp_guide.main import _handle_cli_error

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        config = ServerConfig(
            cli_error=None,
            should_exit=False,
        )

        _handle_cli_error(config)

        mock_sys_exit.assert_not_called()
        mock_logger.info.assert_not_called()
        mock_logger.error.assert_not_called()
        mock_logger.warning.assert_not_called()

    @patch("mcp_guide.main.sys.exit")
    @patch("logging.getLogger")
    def test_cli_error_with_exit_maps_ctrl_c_to_130_and_logs_info(
        self,
        mock_get_logger: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """When cli_error is set and should_exit is True, sys.exit(130) is called and info logged."""
        from mcp_guide.cli import ServerConfig
        from mcp_guide.main import _handle_cli_error

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        config = ServerConfig(
            cli_error=KeyboardInterrupt("Ctrl+C"),
            should_exit=True,
        )

        _handle_cli_error(config)

        mock_sys_exit.assert_called_once_with(130)
        mock_logger.info.assert_called()

    @patch("mcp_guide.main.sys.exit")
    @patch("logging.getLogger")
    def test_cli_error_without_exit_logs_error_and_warning(
        self,
        mock_get_logger: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """When cli_error is set and should_exit is False, errors are logged and process continues."""
        import click

        from mcp_guide.cli import ServerConfig
        from mcp_guide.main import _handle_cli_error

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        cli_error = click.UsageError("Invalid option")
        config = ServerConfig(
            cli_error=cli_error,
            should_exit=False,
        )

        _handle_cli_error(config)

        mock_sys_exit.assert_not_called()
        mock_logger.error.assert_called()
        mock_logger.warning.assert_called()
