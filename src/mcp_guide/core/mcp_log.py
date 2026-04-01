"""Reusable MCP logging module with FastMCP integration."""

import atexit
import contextlib
import json
import logging
import signal
import sys
from datetime import datetime
from typing import Any, Callable

from mcp_guide.core.mcp_log_filter import get_redaction_function

# Custom TRACE level (below DEBUG=10)
TRACE_LEVEL = 5
TRACE = TRACE_LEVEL

# Register TRACE level with the logging module
logging.addLevelName(TRACE_LEVEL, "TRACE")

# Re-export standard logging levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

# Track if the TRACE level has been initialised
_trace_initialized = False

# Guard flag to prevent double-cleanup
_cleanup_done = False


class StartupBufferingHandler(logging.Handler):
    """Buffers log records emitted before logging is fully configured.

    Attach to the root logger at module load time. After real handlers are
    configured, call ``flush_startup_buffer()`` to replay the buffered
    records (with their original timestamps) through those handlers.
    """

    def __init__(self) -> None:
        super().__init__(level=TRACE_LEVEL)
        self.buffer: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.buffer.append(record)


# Install startup buffering only if the root logger has no handlers yet,
# to avoid duplicate output from both immediate handling and later replay.
_startup_handler: StartupBufferingHandler | None = None
_original_root_level: int | None = None
_root_logger = logging.getLogger()
if not _root_logger.handlers:
    _startup_handler = StartupBufferingHandler()
    _original_root_level = _root_logger.level
    _root_logger.addHandler(_startup_handler)
    if _root_logger.level == logging.NOTSET or _root_logger.level > TRACE_LEVEL:
        _root_logger.setLevel(TRACE_LEVEL)


def flush_startup_buffer() -> None:
    """Replay buffered startup records through the now-configured handlers, then remove the buffer."""
    global _startup_handler, _original_root_level
    if _startup_handler is None:
        return
    root = logging.getLogger()
    root.removeHandler(_startup_handler)
    # Replay only to file handlers — stream handlers may write to stderr
    # which is the MCP stdio transport channel
    file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
    for record in _startup_handler.buffer:
        for handler in file_handlers:
            if record.levelno >= handler.level:
                handler.handle(record)
    _startup_handler.buffer.clear()
    _startup_handler = None  # type: ignore[assignment]
    # Restore root logger level if we lowered it
    if _original_root_level is not None:
        root.setLevel(_original_root_level)
    _original_root_level = None


def _cleanup_logging() -> None:
    """Clean up logging handlers on shutdown."""
    global _cleanup_done

    if _cleanup_done:
        return
    _cleanup_done = True

    # Close all root logger handlers
    for handler in logging.getLogger().handlers[:]:
        with contextlib.suppress(Exception):
            handler.close()
            logging.getLogger().removeHandler(handler)


# noinspection PyUnusedLocal
def _signal_handler(signum: int, frame: Any) -> None:  # noqa
    """Handle termination signals."""
    _cleanup_logging()
    sys.exit(128 + signum)


def register_cleanup_handlers() -> None:
    """Register cleanup handlers for a graceful shutdown.

    Call this explicitly from your application's main entry point
    to enable automatic cleanup of logging resources on exit.
    """
    import platform

    atexit.register(_cleanup_logging)
    if platform.system() != "Windows":
        signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)


def _sanitize_log_message(message: Any) -> Any:
    """Sanitize log message to prevent log injection."""
    if isinstance(message, str):
        return message.replace("\n", "\\n").replace("\r", "\\r")
    return message


class RedactedFormatter(logging.Formatter):
    """Log formatter with PII redaction support."""

    def __init__(self) -> None:
        """Initialise the formatter with a redaction function."""
        super().__init__(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        self._redaction_func: Callable[[str], str] = get_redaction_function()

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with redaction."""
        extra_data = {
            key: value
            for key, value in record.__dict__.items()
            if key
            not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
                "message",
            }
        }
        formatted = super().format(record)
        if extra_data:
            formatted += f" - extra: {json.dumps(extra_data)}"

        return self._redaction_func(formatted)


class StructuredJSONFormatter(logging.Formatter):
    """JSON formatter for structured logging with PII redaction."""

    def __init__(self) -> None:
        """Initialise JSON formatter with a redaction function."""
        super().__init__()
        self._redaction_func: Callable[[str], str] = get_redaction_function()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        message = record.getMessage()
        message = self._redaction_func(message)

        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "module": record.module,
            "function": record.funcName,
        }

        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
                "message",
            }:
                log_entry[key] = value

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def get_log_level(level_name: str) -> int:
    """Convert level name to logging level constant.

    Supports standard levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    and custom TRACE level.
    """
    level_upper = level_name.upper()
    if level_upper == "TRACE":
        return TRACE_LEVEL
    return getattr(logging, level_upper, logging.INFO)


class LoggerWithTrace(logging.Logger):
    """Logger subclass that includes the trace method."""

    def trace(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'TRACE'."""
        if self.isEnabledFor(TRACE_LEVEL):
            sanitized_message = _sanitize_log_message(message)
            self._log(TRACE_LEVEL, sanitized_message, args, **kwargs)


# Set our custom logger class as the default for all loggers
logging.setLoggerClass(LoggerWithTrace)


def get_logger(name: str) -> LoggerWithTrace:
    """Get a logger with trace method support."""
    return logging.getLogger(name)  # ty: ignore[invalid-return-type]


def create_console_handler() -> logging.Handler:
    """Create a console handler with RichHandler if available."""
    try:
        # Import here as rich is an optional dependency
        from rich.console import Console
        from rich.logging import RichHandler

        return RichHandler(
            console=Console(stderr=True),
            rich_tracebacks=True,
            show_time=True,
            show_path=True,
        )
    except ImportError:
        return logging.StreamHandler()


def create_file_handler(log_file: str) -> logging.Handler:
    """Create a file handler with external rotation support on non-Windows.

    Falls back to StreamHandler if file creation fails.
    """
    import platform
    import sys
    from pathlib import Path

    log_path = Path(log_file).expanduser()

    # Ensure parent directory exists
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        print(f"WARNING: Cannot create log directory {log_path.parent}: {e}", file=sys.stderr)
        print("Falling back to console-only logging", file=sys.stderr)
        return logging.StreamHandler()

    try:
        if platform.system() == "Windows":
            return logging.FileHandler(log_path, mode="a")

        from logging.handlers import WatchedFileHandler

        return WatchedFileHandler(log_path, mode="a")
    except (OSError, PermissionError) as e:
        print(f"WARNING: Cannot create log file {log_path}: {e}", file=sys.stderr)
        print("Falling back to console-only logging", file=sys.stderr)
        return logging.StreamHandler()


def create_formatter(json_format: bool = False) -> logging.Formatter:
    """Create a formatter based on configuration."""
    return StructuredJSONFormatter() if json_format else RedactedFormatter()


def get_uvicorn_log_config(log_level: str = "info", use_json: bool = False) -> dict[str, Any]:
    """Get uvicorn logging configuration using our formatters.

    Args:
        log_level: Log level (debug, info, warning, error, critical)
        use_json: Whether to use JSON formatting

    Returns:
        Uvicorn log config dict

    Raises:
        ValueError: If log_level is not valid
    """
    valid_levels = {"trace", "debug", "info", "warning", "error", "critical"}
    if log_level.lower() not in valid_levels:
        raise ValueError(f"Invalid log level: {log_level}. Must be one of: {', '.join(sorted(valid_levels))}")

    formatter_class = (
        "mcp_guide.core.mcp_log.StructuredJSONFormatter" if use_json else "mcp_guide.core.mcp_log.RedactedFormatter"
    )

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": formatter_class,
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["default"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["default"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["default"],
                "level": log_level.upper(),
                "propagate": False,
            },
        },
    }


def add_trace_to_context() -> None:
    """Add a trace () method to the FastMCP Context class.

    Maps to debug level with [TRACE] prefix for client visibility.
    Handles ImportError gracefully if FastMCP not available.
    """
    try:
        from fastmcp import Context

        async def trace(self: Context, message: str) -> None:  # noqa: F821
            """Log TRACE message via Context (maps to debug with prefix)."""
            sanitized = _sanitize_log_message(message)
            await self.log(level="debug", message=f"[TRACE] {sanitized}")

        Context.trace = trace  # ty: ignore[unresolved-attribute]
    except ImportError:
        pass
