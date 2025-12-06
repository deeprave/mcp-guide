"""Tests for main entry point."""

import inspect
import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_async_main_exists() -> None:
    """Test that async_main function exists and is callable."""
    from mcp_guide.main import async_main

    assert callable(async_main)


@pytest.mark.asyncio
async def test_async_main_has_no_parameters() -> None:
    """Test that async_main has no required parameters."""
    from mcp_guide.main import async_main

    sig = inspect.signature(async_main)
    assert len(sig.parameters) == 0


def test_main_exists() -> None:
    """Test that main function exists and is callable."""
    from mcp_guide.main import main

    assert callable(main)


def test_main_has_no_required_parameters() -> None:
    """Test that main function has no required parameters."""
    from mcp_guide.main import main

    sig = inspect.signature(main)
    required_params = [p for p in sig.parameters.values() if p.default == inspect.Parameter.empty]

    assert not required_params


class TestLoggingConfiguration:
    """Tests for logging configuration from ServerConfig."""

    @patch("mcp_core.mcp_log.register_cleanup_handlers")
    @patch("mcp_core.mcp_log.save_logging_config")
    @patch("mcp_core.mcp_log.create_formatter")
    @patch("mcp_core.mcp_log.create_file_handler")
    @patch("mcp_core.mcp_log.create_console_handler")
    @patch("logging.getLogger")
    def test_configure_logging_default_values(
        self,
        mock_get_logger: MagicMock,
        mock_create_console_handler: MagicMock,
        mock_create_file_handler: MagicMock,
        mock_create_formatter: MagicMock,
        mock_save_logging_config: MagicMock,
        mock_register_cleanup: MagicMock,
    ) -> None:
        """Test logging configuration with default values (no file handler)."""
        from mcp_guide.cli import ServerConfig
        from mcp_guide.main import _configure_logging

        mock_console_handler = MagicMock()
        mock_formatter = MagicMock()
        mock_root_logger = MagicMock()

        mock_create_console_handler.return_value = mock_console_handler
        mock_create_formatter.return_value = mock_formatter
        mock_get_logger.return_value = mock_root_logger

        config = ServerConfig()
        _configure_logging(config)

        # Verify handler/formatter creation
        mock_create_console_handler.assert_called_once()
        mock_create_file_handler.assert_not_called()
        mock_create_formatter.assert_called_once_with(False)

        # Verify formatter applied to console handler
        mock_console_handler.setFormatter.assert_called_once_with(mock_formatter)

        # Verify handlers saved (no file handler)
        mock_save_logging_config.assert_called_once_with(mock_console_handler, None)

        # Verify cleanup handlers registered
        mock_register_cleanup.assert_called_once()

    @patch("mcp_core.mcp_log.register_cleanup_handlers")
    @patch("mcp_core.mcp_log.save_logging_config")
    @patch("mcp_core.mcp_log.create_formatter")
    @patch("mcp_core.mcp_log.create_file_handler")
    @patch("mcp_core.mcp_log.create_console_handler")
    @patch("logging.getLogger")
    def test_configure_logging_with_file_handler(
        self,
        mock_get_logger: MagicMock,
        mock_create_console_handler: MagicMock,
        mock_create_file_handler: MagicMock,
        mock_create_formatter: MagicMock,
        mock_save_logging_config: MagicMock,
        mock_register_cleanup: MagicMock,
    ) -> None:
        """Test logging configuration when a log file path is configured."""
        from mcp_guide.cli import ServerConfig
        from mcp_guide.main import _configure_logging

        mock_console_handler = MagicMock()
        mock_file_handler = MagicMock()
        mock_formatter = MagicMock()
        mock_root_logger = MagicMock()

        mock_create_console_handler.return_value = mock_console_handler
        mock_create_file_handler.return_value = mock_file_handler
        mock_create_formatter.return_value = mock_formatter
        mock_get_logger.return_value = mock_root_logger

        log_path = "server.log"
        config = ServerConfig(log_file=log_path, log_json=True)
        _configure_logging(config)

        # Verify handler/formatter creation
        mock_create_console_handler.assert_called_once()
        mock_create_file_handler.assert_called_once_with(log_path)
        mock_create_formatter.assert_called_once_with(True)

        # Verify formatter applied to both handlers
        mock_console_handler.setFormatter.assert_called_once_with(mock_formatter)
        mock_file_handler.setFormatter.assert_called_once_with(mock_formatter)

        # Verify both handlers saved
        mock_save_logging_config.assert_called_once_with(mock_console_handler, mock_file_handler)

        # Verify cleanup handlers registered
        mock_register_cleanup.assert_called_once()


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

    @patch("mcp_core.mcp_log.register_cleanup_handlers")
    @patch("mcp_core.mcp_log.save_logging_config")
    @patch("mcp_core.mcp_log.create_formatter")
    @patch("mcp_core.mcp_log.create_console_handler")
    @patch("logging.getLogger")
    @patch("mcp_core.mcp_log.create_file_handler")
    def test_configure_logging_startup_messages(
        self,
        mock_create_file: MagicMock,
        mock_get_logger: MagicMock,
        mock_create_console: MagicMock,
        mock_create_formatter: MagicMock,
        mock_save_config: MagicMock,
        mock_register_cleanup: MagicMock,
    ) -> None:
        """Test startup logging messages are logged."""
        from mcp_guide.cli import ServerConfig
        from mcp_guide.main import _configure_logging

        mock_logger = MagicMock()
        mock_root_logger = MagicMock()
        mock_file_handler = MagicMock()
        mock_console_handler = MagicMock()
        mock_formatter = MagicMock()

        mock_create_file.return_value = mock_file_handler
        mock_create_console.return_value = mock_console_handler
        mock_create_formatter.return_value = mock_formatter

        # Return different loggers for root and named logger
        def get_logger_side_effect(name=None):
            if name == "mcp_guide.main":
                return mock_logger
            return mock_root_logger

        mock_get_logger.side_effect = get_logger_side_effect

        config = ServerConfig(
            log_level="TRACE",
            log_file="/tmp/test.log",
            log_json=True,
        )
        _configure_logging(config)

        mock_logger.info.assert_called_once_with("Starting mcp-guide server")
        mock_logger.debug.assert_called_once()
        debug_msg = mock_logger.debug.call_args[0][0]
        assert "TRACE" in debug_msg
        assert "/tmp/test.log" in debug_msg
        assert "True" in debug_msg
