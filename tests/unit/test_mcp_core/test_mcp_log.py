"""Tests for mcp_core.mcp_log module."""

import logging

import pytest


class TestLoggerTraceMethod:
    """Tests for logger.trace() method."""

    def test_trace_method_logs_at_trace_level(self, caplog):
        """Test trace() method logs at TRACE level."""
        from mcp_guide.core.mcp_log import TRACE_LEVEL, get_logger

        logger = get_logger("test_trace_logging")
        logger.setLevel(TRACE_LEVEL)

        with caplog.at_level(TRACE_LEVEL):
            logger.trace("test message")

        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == TRACE_LEVEL
        assert caplog.records[0].levelname == "TRACE"
        assert caplog.records[0].message == "test message"

    def test_trace_method_filtered_when_level_higher(self, caplog):
        """Test trace() messages filtered when level is DEBUG."""
        from mcp_guide.core.mcp_log import TRACE_LEVEL, get_logger

        logger = get_logger("test_trace_filter_method")
        logger.setLevel(logging.DEBUG)

        with caplog.at_level(TRACE_LEVEL):
            logger.trace("should not appear")

        assert len(caplog.records) == 0


class TestMessageSanitization:
    """Tests for log message sanitization."""

    @pytest.mark.parametrize(
        "input_msg,expected",
        [
            ("line1\nline2", "line1\\nline2"),  # newlines
            ("line1\rline2", "line1\\rline2"),  # carriage returns
            ("line1\r\nline2", "line1\\r\\nline2"),  # both
            (123, 123),  # non-string integer
            (None, None),  # non-string None
        ],
    )
    def test_sanitize_log_message(self, input_msg, expected):
        """Test log message sanitization for various inputs."""
        from mcp_guide.core.mcp_log import _sanitize_log_message

        assert _sanitize_log_message(input_msg) == expected


class TestRedactedFormatter:
    """Tests for RedactedFormatter."""

    def test_formatter_includes_required_fields(self):
        """Test formatter includes timestamp, level, name, message."""
        import logging

        from mcp_guide.core.mcp_log import RedactedFormatter

        formatter = RedactedFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        assert "INFO" in result
        assert "test.logger" in result
        assert "test message" in result

    def test_formatter_calls_redaction_function(self, monkeypatch):
        """Test formatter calls redaction function."""
        import logging

        from mcp_guide.core.mcp_log import RedactedFormatter

        # A deterministic provider stands in for a future external redaction service.
        def mock_redaction(message: str) -> str:
            return message.replace("sensitive", "[REDACTED]")

        def mock_get_redaction():
            return mock_redaction

        monkeypatch.setattr("mcp_guide.core.mcp_log.get_redaction_function", mock_get_redaction)

        formatter = RedactedFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="sensitive data",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        assert "[REDACTED] data" in output
        assert "sensitive" not in output

    def test_formatter_handles_exceptions(self):
        """Test formatter includes exception info."""
        import logging

        from mcp_guide.core.mcp_log import RedactedFormatter

        formatter = RedactedFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        assert "ValueError" in result
        assert "test error" in result


class TestStructuredJSONFormatter:
    """Tests for StructuredJSONFormatter."""

    def test_json_output_includes_required_fields(self):
        """Test JSON output includes required fields."""
        import json
        import logging

        from mcp_guide.core.mcp_log import StructuredJSONFormatter

        formatter = StructuredJSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
            func="test_func",
        )
        record.module = "test_module"

        result = formatter.format(record)
        data = json.loads(result)

        assert "timestamp" in data
        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "test message"
        assert data["module"] == "test_module"
        assert data["function"] == "test_func"

    def test_json_formatter_calls_redaction(self, monkeypatch):
        """Test JSON formatter calls redaction function."""
        import logging

        from mcp_guide.core.mcp_log import StructuredJSONFormatter

        # A deterministic provider stands in for a future external redaction service.
        def mock_redaction(message: str) -> str:
            return message.replace("sensitive", "[REDACTED]")

        def mock_get_redaction():
            return mock_redaction

        monkeypatch.setattr("mcp_guide.core.mcp_log.get_redaction_function", mock_get_redaction)

        formatter = StructuredJSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="sensitive",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        assert '"message": "[REDACTED]"' in output
        assert "sensitive" not in output

    def test_json_formatter_includes_exception(self):
        """Test JSON formatter includes exception info."""
        import json
        import logging

        from mcp_guide.core.mcp_log import StructuredJSONFormatter

        formatter = StructuredJSONFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="error",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert "exception" in data
        assert "ValueError" in data["exception"]


class TestCreateFileHandler:
    """Tests for create_file_handler platform selection and failure fallback."""

    @pytest.mark.parametrize(
        "platform_name,expected_handler_type,is_watched",
        [
            ("Linux", "WatchedFileHandler", True),
            ("Windows", "FileHandler", False),
        ],
        ids=["non_windows", "windows"],
    )
    def test_file_handler_platform_specific(
        self, monkeypatch, tmp_path, platform_name, expected_handler_type, is_watched
    ):
        """File handler type should vary by platform."""
        import platform
        from logging import handlers

        from mcp_guide.core.mcp_log import create_file_handler

        monkeypatch.setattr(platform, "system", lambda: platform_name)

        log_file = tmp_path / f"test_{platform_name.lower()}.log"
        handler = create_file_handler(str(log_file))

        try:
            if is_watched:
                assert isinstance(handler, handlers.WatchedFileHandler)
            else:
                assert isinstance(handler, logging.FileHandler)
                assert not isinstance(handler, logging.handlers.WatchedFileHandler)
        finally:
            handler.close()

    def test_fallback_to_stream_handler_on_dir_creation_failure(self, monkeypatch, tmp_path):
        """If directory creation fails, fall back to StreamHandler."""
        import platform
        from pathlib import Path

        from mcp_guide.core.mcp_log import create_file_handler

        monkeypatch.setattr(platform, "system", lambda: "Linux")

        original_mkdir = Path.mkdir

        def failing_mkdir(self, *args, **kwargs):
            raise PermissionError("cannot create directory")

        monkeypatch.setattr(Path, "mkdir", failing_mkdir)

        log_file = tmp_path / "subdir" / "test_permission.log"
        handler = create_file_handler(str(log_file))

        try:
            assert isinstance(handler, logging.StreamHandler)
            assert not isinstance(handler, logging.FileHandler)
        finally:
            handler.close()
            monkeypatch.setattr(Path, "mkdir", original_mkdir)

    def test_fallback_to_stream_handler_on_file_handler_failure(self, monkeypatch, tmp_path):
        """If the file handler construction fails, fall back to StreamHandler."""
        import platform

        from mcp_guide.core.mcp_log import create_file_handler

        monkeypatch.setattr(platform, "system", lambda: "Windows")

        original_init = logging.FileHandler.__init__

        def failing_init(self, filename, *args, **kwargs):
            raise OSError("cannot open log file")

        monkeypatch.setattr(logging.FileHandler, "__init__", failing_init)

        log_file = tmp_path / "test_file_failure.log"
        handler = create_file_handler(str(log_file))

        try:
            assert isinstance(handler, logging.StreamHandler)
            assert not isinstance(handler, logging.FileHandler)
        finally:
            handler.close()
            monkeypatch.setattr(logging.FileHandler, "__init__", original_init)
