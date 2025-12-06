"""Tests for mcp_core.mcp_log module."""

import logging

import pytest


class TestTraceLevel:
    """Tests for TRACE logging level."""

    def test_trace_level_registered(self):
        """Test TRACE level is registered with logging module."""
        from mcp_core.mcp_log import TRACE_LEVEL

        assert TRACE_LEVEL == 5
        assert logging.getLevelName(TRACE_LEVEL) == "TRACE"

    def test_logger_is_enabled_for_trace(self):
        """Test logger.isEnabledFor() works with TRACE level."""
        from mcp_core.mcp_log import TRACE_LEVEL

        logger = logging.getLogger("test_trace")
        logger.setLevel(TRACE_LEVEL)

        assert logger.isEnabledFor(TRACE_LEVEL)

    def test_logger_filters_trace_when_level_higher(self):
        """Test TRACE messages filtered when level is DEBUG or higher."""
        from mcp_core.mcp_log import TRACE_LEVEL

        logger = logging.getLogger("test_trace_filter")
        logger.setLevel(logging.DEBUG)

        assert not logger.isEnabledFor(TRACE_LEVEL)


class TestLoggerTraceMethod:
    """Tests for logger.trace() method."""

    def test_logger_has_trace_method(self):
        """Test logger has trace() method."""
        import mcp_core.mcp_log  # noqa: F401 - Import to initialize TRACE level

        logger = logging.getLogger("test_trace_method")

        assert hasattr(logger, "trace")
        assert callable(logger.trace)

    def test_trace_method_logs_at_trace_level(self, caplog):
        """Test trace() method logs at TRACE level."""
        from mcp_core.mcp_log import TRACE_LEVEL

        logger = logging.getLogger("test_trace_logging")
        logger.setLevel(TRACE_LEVEL)

        with caplog.at_level(TRACE_LEVEL):
            logger.trace("test message")

        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == TRACE_LEVEL
        assert caplog.records[0].message == "test message"

    def test_trace_method_filtered_when_level_higher(self, caplog):
        """Test trace() messages filtered when level is DEBUG."""
        from mcp_core.mcp_log import TRACE_LEVEL

        logger = logging.getLogger("test_trace_filter_method")
        logger.setLevel(logging.DEBUG)

        with caplog.at_level(TRACE_LEVEL):
            logger.trace("should not appear")

        assert len(caplog.records) == 0


class TestMessageSanitization:
    """Tests for log message sanitization."""

    def test_sanitize_newlines(self):
        """Test newlines are escaped."""
        from mcp_core.mcp_log import _sanitize_log_message

        result = _sanitize_log_message("line1\nline2")
        assert result == "line1\\nline2"

    def test_sanitize_carriage_returns(self):
        """Test carriage returns are escaped."""
        from mcp_core.mcp_log import _sanitize_log_message

        result = _sanitize_log_message("line1\rline2")
        assert result == "line1\\rline2"

    def test_sanitize_both(self):
        """Test both newlines and carriage returns are escaped."""
        from mcp_core.mcp_log import _sanitize_log_message

        result = _sanitize_log_message("line1\r\nline2")
        assert result == "line1\\r\\nline2"

    def test_sanitize_non_string(self):
        """Test non-string values are returned as-is."""
        from mcp_core.mcp_log import _sanitize_log_message

        assert _sanitize_log_message(123) == 123
        assert _sanitize_log_message(None) is None


class TestRedactedFormatter:
    """Tests for RedactedFormatter."""

    def test_formatter_includes_required_fields(self):
        """Test formatter includes timestamp, level, name, message."""
        import logging

        from mcp_core.mcp_log import RedactedFormatter

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

        from mcp_core.mcp_log import RedactedFormatter

        redaction_called = []

        def mock_redaction(message: str) -> str:
            redaction_called.append(message)
            return message

        def mock_get_redaction():
            return mock_redaction

        monkeypatch.setattr("mcp_core.mcp_log.get_redaction_function", mock_get_redaction)

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

        formatter.format(record)
        assert len(redaction_called) > 0

    def test_formatter_handles_exceptions(self):
        """Test formatter includes exception info."""
        import logging

        from mcp_core.mcp_log import RedactedFormatter

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

        from mcp_core.mcp_log import StructuredJSONFormatter

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

        from mcp_core.mcp_log import StructuredJSONFormatter

        redaction_called = []

        def mock_redaction(message: str) -> str:
            redaction_called.append(message)
            return message

        def mock_get_redaction():
            return mock_redaction

        monkeypatch.setattr("mcp_core.mcp_log.get_redaction_function", mock_get_redaction)

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

        formatter.format(record)
        assert "sensitive" in redaction_called

    def test_json_formatter_includes_exception(self):
        """Test JSON formatter includes exception info."""
        import json
        import logging

        from mcp_core.mcp_log import StructuredJSONFormatter

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


class TestLoggerHierarchy:
    """Tests for logger hierarchy configuration."""

    def test_configure_logger_hierarchy_direct_pattern(self):
        """Test logger hierarchy handles mcp_guide.* pattern."""
        from mcp_core.mcp_log import configure_logger_hierarchy

        configure_logger_hierarchy("mcp_guide")

        logger = logging.getLogger("mcp_guide.tools")
        assert logger.propagate is False

    def test_configure_logger_hierarchy_fastmcp_pattern(self):
        """Test logger hierarchy handles fastmcp.mcp_guide.* pattern."""
        from mcp_core.mcp_log import configure_logger_hierarchy

        configure_logger_hierarchy("mcp_guide")

        logger = logging.getLogger("fastmcp.mcp_guide.server")
        assert logger.propagate is False

    def test_logs_appear_once(self):
        """Test logs don't duplicate with hierarchy configuration."""
        import logging
        from io import StringIO

        from mcp_core.mcp_log import TRACE_LEVEL, configure_logger_hierarchy

        configure_logger_hierarchy("mcp_guide")

        # Create a handler to capture logs
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(TRACE_LEVEL)

        logger = logging.getLogger("mcp_guide.test")
        logger.setLevel(TRACE_LEVEL)
        logger.addHandler(handler)

        logger.info("test message")

        # Should appear exactly once in the output
        output = stream.getvalue()
        assert output.count("test message") == 1


class TestContextTrace:
    """Tests for Context.trace() method."""

    def test_add_trace_to_context_without_fastmcp(self):
        """Test add_trace_to_context handles missing FastMCP gracefully."""
        from mcp_core.mcp_log import add_trace_to_context

        # Should not raise even if FastMCP not available
        add_trace_to_context()

    def test_context_trace_method_exists(self):
        """Test Context.trace() method is added if FastMCP available."""
        try:
            from fastmcp import Context

            from mcp_core.mcp_log import add_trace_to_context

            add_trace_to_context()

            # Check if trace method was added
            assert hasattr(Context, "trace")
        except ImportError:
            # FastMCP not available, skip test
            import pytest

            pytest.skip("FastMCP not available")


class TestConfigure:
    """Tests for configure() function."""

    def test_configure_initializes_trace_level(self):
        """Test configure initializes TRACE level."""
        from mcp_core.mcp_log import TRACE_LEVEL, configure

        configure()

        assert logging.getLevelName(TRACE_LEVEL) == "TRACE"

    def test_configure_adds_context_trace(self):
        """Test configure adds Context.trace() method."""
        from mcp_core.mcp_log import configure

        configure()

        # Should not raise even if FastMCP not available
        try:
            from fastmcp import Context

            assert hasattr(Context, "trace")
        except ImportError:
            pass

    def test_configure_with_file_logging(self, tmp_path):
        """Test configure sets up file logging when path provided."""
        from mcp_core.mcp_log import configure

        log_file = tmp_path / "test.log"
        configure(file_path=str(log_file))

        # Verify file handler was added
        root_logger = logging.getLogger()
        file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0
