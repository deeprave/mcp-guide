"""Tests for server logging configuration."""

import logging
from unittest.mock import MagicMock, patch

import mcp_guide.server as server_module
from mcp_guide.cli import ServerConfig


class TestConfigureLoggingAfterFastmcp:
    """Tests for _configure_logging_after_fastmcp function."""

    def test_configure_logging_after_fastmcp_calls_trace_helpers(self) -> None:
        """Test that trace helpers are always called."""
        from mcp_guide.server import _configure_logging_after_fastmcp

        config = ServerConfig(log_level="debug", log_json=True, log_file="test.log")
        server_module._pending_log_config = config

        with (
            patch("mcp_core.mcp_log.initialize_trace_level") as mock_init_trace,
            patch("mcp_core.mcp_log.add_trace_to_context") as mock_add_trace,
            patch("mcp_core.mcp_log.register_cleanup_handlers") as mock_register,
            patch("mcp_core.mcp_log.get_log_level", return_value=10),
            patch("mcp_core.mcp_log.create_console_handler") as mock_console,
            patch("mcp_core.mcp_log.create_file_handler") as mock_file,
            patch("mcp_core.mcp_log.create_formatter"),
        ):
            # Create handlers with proper level attribute
            console_handler = MagicMock()
            console_handler.level = 10
            file_handler = MagicMock()
            file_handler.level = 10

            mock_console.return_value = console_handler
            mock_file.return_value = file_handler

            _configure_logging_after_fastmcp()

        # Assert trace helpers were called
        mock_init_trace.assert_called_once()
        mock_add_trace.assert_called_once()
        mock_register.assert_called_once()

    def test_configure_logging_after_fastmcp_creates_handlers(self) -> None:
        """Test that handlers are created with correct parameters."""
        from mcp_guide.server import _configure_logging_after_fastmcp

        config = ServerConfig(log_level="debug", log_json=True, log_file="test.log")
        server_module._pending_log_config = config

        with (
            patch("mcp_core.mcp_log.initialize_trace_level"),
            patch("mcp_core.mcp_log.add_trace_to_context"),
            patch("mcp_core.mcp_log.register_cleanup_handlers"),
            patch("mcp_core.mcp_log.get_log_level", return_value=10) as mock_get_level,
            patch("mcp_core.mcp_log.create_console_handler") as mock_console,
            patch("mcp_core.mcp_log.create_file_handler") as mock_file,
            patch("mcp_core.mcp_log.create_formatter") as mock_formatter,
        ):
            # Create handlers with proper level attribute
            console_handler = MagicMock()
            console_handler.level = 10
            file_handler = MagicMock()
            file_handler.level = 10

            mock_console.return_value = console_handler
            mock_file.return_value = file_handler
            mock_formatter.return_value = MagicMock()

            _configure_logging_after_fastmcp()

        # Assert log level was retrieved
        mock_get_level.assert_called_once_with(config.log_level)

        # Assert handlers were created
        mock_console.assert_called_once()
        mock_file.assert_called_once_with(config.log_file)
        mock_formatter.assert_called_once_with(config.log_json)

    def test_configure_logging_after_fastmcp_no_file_handler(self) -> None:
        """Test logging configuration without file handler."""
        from mcp_guide.server import _configure_logging_after_fastmcp

        config = ServerConfig(log_level="info", log_json=False, log_file=None)
        server_module._pending_log_config = config

        with (
            patch("mcp_core.mcp_log.initialize_trace_level"),
            patch("mcp_core.mcp_log.add_trace_to_context"),
            patch("mcp_core.mcp_log.register_cleanup_handlers"),
            patch("mcp_core.mcp_log.get_log_level", return_value=20),
            patch("mcp_core.mcp_log.create_console_handler") as mock_console,
            patch("mcp_core.mcp_log.create_file_handler") as mock_file,
            patch("mcp_core.mcp_log.create_formatter"),
        ):
            # Create handler with proper level attribute
            console_handler = MagicMock()
            console_handler.level = 20
            mock_console.return_value = console_handler

            _configure_logging_after_fastmcp()

        # Assert file handler not created when log_file is None
        mock_file.assert_not_called()

    def test_configure_logging_after_fastmcp_no_pending_config(self) -> None:
        """Test logging configuration when no pending config is set."""
        from mcp_guide.server import _configure_logging_after_fastmcp

        server_module._pending_log_config = None

        with (
            patch("mcp_core.mcp_log.initialize_trace_level") as mock_init_trace,
            patch("mcp_core.mcp_log.add_trace_to_context") as mock_add_trace,
            patch("mcp_core.mcp_log.get_log_level") as mock_get_level,
        ):
            _configure_logging_after_fastmcp()

        # Assert trace helpers still called
        mock_init_trace.assert_called_once()
        mock_add_trace.assert_called_once()

        # Assert no log level configuration attempted
        mock_get_level.assert_not_called()

    def test_configure_logging_uses_get_effective_level(self) -> None:
        """Test that logger level adjustment uses getEffectiveLevel."""
        from mcp_guide.server import _configure_logging_after_fastmcp

        config = ServerConfig(log_level="warning", log_json=False, log_file=None)
        server_module._pending_log_config = config

        # Create mock loggers
        mock_verbose_logger = MagicMock(spec=logging.Logger)
        mock_verbose_logger.getEffectiveLevel.return_value = 10  # DEBUG

        mock_appropriate_logger = MagicMock(spec=logging.Logger)
        mock_appropriate_logger.getEffectiveLevel.return_value = 30  # WARNING

        # Not a Logger instance
        mock_placeholder = MagicMock()

        with (
            patch("mcp_core.mcp_log.initialize_trace_level"),
            patch("mcp_core.mcp_log.add_trace_to_context"),
            patch("mcp_core.mcp_log.register_cleanup_handlers"),
            patch("mcp_core.mcp_log.get_log_level", return_value=30),  # WARNING
            patch("mcp_core.mcp_log.create_console_handler", return_value=MagicMock()),
            patch("mcp_core.mcp_log.create_formatter", return_value=MagicMock()),
            patch("logging.Logger.manager") as mock_manager,
            patch("logging.getLogger") as mock_get_logger,
        ):
            # Mock loggerDict
            mock_manager.loggerDict = {
                "verbose_logger": None,
                "appropriate_logger": None,
                "placeholder": None,
            }

            # Mock getLogger to return our test loggers
            def get_logger_side_effect(name=""):
                if name == "":
                    return MagicMock()
                elif name == "verbose_logger":
                    return mock_verbose_logger
                elif name == "appropriate_logger":
                    return mock_appropriate_logger
                elif name == "placeholder":
                    return mock_placeholder
                return MagicMock()

            mock_get_logger.side_effect = get_logger_side_effect

            _configure_logging_after_fastmcp()

        # Assert verbose logger level was adjusted
        mock_verbose_logger.setLevel.assert_called_once_with(30)

        # Assert appropriate logger level was NOT adjusted
        mock_appropriate_logger.setLevel.assert_not_called()

        # Assert placeholder was skipped (no setLevel call)
        assert not hasattr(mock_placeholder, "setLevel") or not mock_placeholder.setLevel.called
