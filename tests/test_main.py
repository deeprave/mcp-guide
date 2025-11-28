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
    """Tests for logging configuration from environment variables."""

    @patch("mcp_core.mcp_log.get_logger")
    @patch("mcp_core.mcp_log.configure")
    def test_configure_logging_default_values(self, mock_configure: MagicMock, mock_get_logger: MagicMock) -> None:
        """Test logging configuration with default values."""
        from mcp_guide.main import _configure_logging

        # Clear environment variables
        env_backup = {k: v for k, v in os.environ.items() if k.startswith("MG_LOG_")}
        for key in list(os.environ.keys()):
            if key.startswith("MG_LOG_"):
                del os.environ[key]

        try:
            _configure_logging()

            mock_configure.assert_called_once_with(
                level="INFO",
                file_path=None,
                json_format=False,
            )
            mock_get_logger.assert_called_once_with("mcp_guide.main")
        finally:
            # Restore environment
            os.environ.update(env_backup)

    @patch("mcp_core.mcp_log.get_logger")
    @patch("mcp_core.mcp_log.configure")
    def test_configure_logging_from_env_vars(self, mock_configure: MagicMock, mock_get_logger: MagicMock) -> None:
        """Test logging configuration reads environment variables."""
        from mcp_guide.main import _configure_logging

        env_backup = {k: v for k, v in os.environ.items() if k.startswith("MG_LOG_")}
        try:
            os.environ["MG_LOG_LEVEL"] = "DEBUG"
            os.environ["MG_LOG_FILE"] = "/tmp/test.log"
            os.environ["MG_LOG_JSON"] = "true"

            _configure_logging()

            mock_configure.assert_called_once_with(
                level="DEBUG",
                file_path="/tmp/test.log",
                json_format=True,
            )
        finally:
            # Restore environment
            for key in list(os.environ.keys()):
                if key.startswith("MG_LOG_"):
                    del os.environ[key]
            os.environ.update(env_backup)

    @patch("mcp_core.mcp_log.get_logger")
    @patch("mcp_core.mcp_log.configure")
    def test_configure_logging_json_variants(self, mock_configure: MagicMock, mock_get_logger: MagicMock) -> None:
        """Test MG_LOG_JSON accepts various true values."""
        from mcp_guide.main import _configure_logging

        env_backup = {k: v for k, v in os.environ.items() if k.startswith("MG_LOG_")}

        for value in ["true", "1", "yes", "TRUE", "Yes"]:
            try:
                os.environ["MG_LOG_JSON"] = value
                mock_configure.reset_mock()

                _configure_logging()

                assert mock_configure.call_args[1]["json_format"] is True
            finally:
                for key in list(os.environ.keys()):
                    if key.startswith("MG_LOG_"):
                        del os.environ[key]
                os.environ.update(env_backup)

    @patch("mcp_core.mcp_log.get_logger")
    @patch("mcp_core.mcp_log.configure")
    def test_configure_logging_startup_messages(self, mock_configure: MagicMock, mock_get_logger: MagicMock) -> None:
        """Test startup logging messages are logged."""
        from mcp_guide.main import _configure_logging

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        env_backup = {k: v for k, v in os.environ.items() if k.startswith("MG_LOG_")}
        try:
            os.environ["MG_LOG_LEVEL"] = "TRACE"
            os.environ["MG_LOG_FILE"] = "/tmp/test.log"
            os.environ["MG_LOG_JSON"] = "true"

            _configure_logging()

            mock_logger.info.assert_called_once_with("Starting mcp-guide server")
            mock_logger.debug.assert_called_once()
            debug_msg = mock_logger.debug.call_args[0][0]
            assert "TRACE" in debug_msg
            assert "/tmp/test.log" in debug_msg
            assert "True" in debug_msg
        finally:
            for key in list(os.environ.keys()):
                if key.startswith("MG_LOG_"):
                    del os.environ[key]
            os.environ.update(env_backup)
