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

    @patch("mcp_core.mcp_log.get_logger")
    @patch("mcp_core.mcp_log.configure")
    def test_configure_logging_default_values(self, mock_configure: MagicMock, mock_get_logger: MagicMock) -> None:
        """Test logging configuration with default values."""
        from mcp_guide.cli import ServerConfig
        from mcp_guide.main import _configure_logging

        config = ServerConfig()
        _configure_logging(config)

        mock_configure.assert_called_once_with(
            level="INFO",
            file_path=None,
            json_format=False,
        )
        mock_get_logger.assert_called_once_with("mcp_guide.main")

    @patch("mcp_core.mcp_log.get_logger")
    @patch("mcp_core.mcp_log.configure")
    def test_configure_logging_from_config(self, mock_configure: MagicMock, mock_get_logger: MagicMock) -> None:
        """Test logging configuration from ServerConfig."""
        from mcp_guide.cli import ServerConfig
        from mcp_guide.main import _configure_logging

        config = ServerConfig(
            log_level="DEBUG",
            log_file="/tmp/test.log",
            log_json=True,
        )
        _configure_logging(config)

        mock_configure.assert_called_once_with(
            level="DEBUG",
            file_path="/tmp/test.log",
            json_format=True,
        )

    @patch("mcp_core.mcp_log.get_logger")
    @patch("mcp_core.mcp_log.configure")
    def test_configure_logging_startup_messages(self, mock_configure: MagicMock, mock_get_logger: MagicMock) -> None:
        """Test startup logging messages are logged."""
        from mcp_guide.cli import ServerConfig
        from mcp_guide.main import _configure_logging

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

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
