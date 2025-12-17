"""Tests for main entry point."""

import inspect
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

    def test_configure_logging_default_values(self) -> None:
        """Test logging configuration stores config for later use."""
        import mcp_guide.server as server_module
        from mcp_guide.cli import ServerConfig
        from mcp_guide.main import _configure_logging

        config = ServerConfig()
        _configure_logging(config)

        # Verify config is stored for later use
        assert server_module._pending_log_config is config

    def test_configure_logging_with_file_handler(self, tmp_path) -> None:
        """Test logging configuration stores config with file path."""
        import mcp_guide.server as server_module
        from mcp_guide.cli import ServerConfig
        from mcp_guide.main import _configure_logging

        log_path = str(tmp_path / "server.log")
        config = ServerConfig(log_file=log_path, log_json=True)
        _configure_logging(config)

        # Verify config is stored
        assert server_module._pending_log_config is config
        assert server_module._pending_log_config.log_file == log_path
        assert server_module._pending_log_config.log_json is True


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
