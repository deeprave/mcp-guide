"""Reusable MCP logging module with FastMCP integration."""

import atexit
import json
import logging
import signal
import sys
from datetime import datetime
from typing import Any, Callable

from mcp_core.mcp_log_filter import get_redaction_function

# Custom TRACE level (below DEBUG=10)
TRACE_LEVEL = 5
TRACE = TRACE_LEVEL

# Register TRACE level with logging module
logging.addLevelName(TRACE_LEVEL, "TRACE")

# Re-export standard logging levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

# Track if TRACE level has been initialized
_trace_initialized = False

# Module-level storage for logging configuration
_saved_logging_config: dict[str, Any] | None = None

# Guard flag to prevent double-cleanup
_cleanup_done = False


def _cleanup_logging() -> None:
    """Clean up logging handlers on shutdown."""
    global _saved_logging_config, _cleanup_done

    if _cleanup_done:
        return
    _cleanup_done = True

    if _saved_logging_config:
        if _saved_logging_config.get("console_handler"):
            try:
                _saved_logging_config["console_handler"].close()
            except Exception:
                pass
        if _saved_logging_config.get("file_handler"):
            try:
                _saved_logging_config["file_handler"].close()
            except Exception:
                pass

    # Close all root logger handlers
    for handler in logging.getLogger().handlers[:]:
        try:
            handler.close()
            logging.getLogger().removeHandler(handler)
        except Exception:
            pass


def _signal_handler(signum: int, frame: Any) -> None:
    """Handle termination signals."""
    _cleanup_logging()
    sys.exit(128 + signum)


def register_cleanup_handlers() -> None:
    """Register cleanup handlers for graceful shutdown.

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
        """Initialize formatter with redaction function."""
        super().__init__(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        self._redaction_func: Callable[[str], str] = get_redaction_function()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with redaction."""
        # Add extra fields to the message if present
        extra_data = {}
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
                extra_data[key] = value

        formatted = super().format(record)
        if extra_data:
            import json

            formatted += f" - extra: {json.dumps(extra_data)}"

        return self._redaction_func(formatted)


class StructuredJSONFormatter(logging.Formatter):
    """JSON formatter for structured logging with PII redaction."""

    def __init__(self) -> None:
        """Initialize JSON formatter with redaction function."""
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
    return logging.getLogger(name)  # type: ignore[return-value]


def configure_logger_hierarchy(app_name: str) -> None:
    """Configure logger hierarchy to prevent duplication.

    Sets propagate=False on application loggers to prevent FastMCP duplication.
    Handles both direct pattern (app_name.*) and FastMCP pattern (fastmcp.app_name.*).

    Args:
        app_name: Application name (e.g., 'mcp_guide')
    """
    # Configure existing loggers
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        if logger_name.startswith(app_name) or logger_name.startswith(f"fastmcp.{app_name}"):
            logger = logging.getLogger(logger_name)
            logger.propagate = False

    # Configure root application loggers
    for pattern in [app_name, f"fastmcp.{app_name}"]:
        logger = logging.getLogger(pattern)
        logger.propagate = False

    # Store patterns for future logger creation
    if not hasattr(logging, "_mcp_app_patterns"):
        logging._mcp_app_patterns = []  # type: ignore
    logging._mcp_app_patterns.append(app_name)  # type: ignore

    # Monkey-patch getLogger to configure new loggers
    original_getLogger = logging.getLogger

    def patched_getLogger(name: str | None = None) -> logging.Logger:
        logger = original_getLogger(name)
        if name and hasattr(logging, "_mcp_app_patterns"):
            for pattern in logging._mcp_app_patterns:
                if name.startswith(pattern) or name.startswith(f"fastmcp.{pattern}"):
                    logger.propagate = False
                    break
        return logger

    logging.getLogger = patched_getLogger


def create_console_handler() -> logging.Handler:
    """Create console handler with RichHandler if available."""
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
    """Create file handler with external rotation support on non-Windows.

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
    """Create formatter based on configuration."""
    return StructuredJSONFormatter() if json_format else RedactedFormatter()


def save_logging_config(
    console_handler: logging.Handler | None,
    file_handler: logging.Handler | None,
    app_name: str | None = None,
) -> None:
    """Save logging configuration for restoration after FastMCP init.

    Args:
        console_handler: Console handler to save
        file_handler: File handler to save
        app_name: Application name for logger hierarchy (optional)
    """
    global _saved_logging_config
    _saved_logging_config = {
        "console_handler": console_handler,
        "file_handler": file_handler,
        "app_name": app_name,
    }


def _configure_fastmcp_log_levels() -> None:
    """Set FastMCP logger levels to match root logger level.

    Only updates loggers that are more verbose than root level.
    Skips NOTSET loggers to preserve parent inheritance.
    """
    root_level = logging.getLogger().level

    for logger_name in logging.Logger.manager.loggerDict:
        if logger_name.startswith("fastmcp") or logger_name.startswith("mcp."):
            logger = logging.getLogger(logger_name)
            current_level = logger.level

            # Skip NOTSET (0) - it means inherit from parent
            if current_level != logging.NOTSET and current_level < root_level:
                logger.setLevel(root_level)


def restore_logging_config() -> None:
    """Restore logging configuration after FastMCP initialization."""
    global _saved_logging_config

    if _saved_logging_config is None:
        return

    root = logging.getLogger()

    # Add our handlers back
    if _saved_logging_config["console_handler"]:
        root.addHandler(_saved_logging_config["console_handler"])
    if _saved_logging_config["file_handler"]:
        root.addHandler(_saved_logging_config["file_handler"])

    # Configure FastMCP logger levels
    _configure_fastmcp_log_levels()

    # Configure logger hierarchy if app_name was saved
    app_name = _saved_logging_config.get("app_name")
    if app_name:
        configure_logger_hierarchy(app_name)


def add_trace_to_context() -> None:
    """Add trace() method to FastMCP Context class.

    Maps to debug level with [TRACE] prefix for client visibility.
    Handles ImportError gracefully if FastMCP not available.
    """
    try:
        from fastmcp import Context

        async def trace(self: Context, message: str) -> None:  # noqa: F821
            """Log TRACE message via Context (maps to debug with prefix)."""
            sanitized = _sanitize_log_message(message)
            await self.log(level="debug", message=f"[TRACE] {sanitized}")

        Context.trace = trace
    except ImportError:
        pass


def configure(
    file_path: str | None = None, level: str = "INFO", json_format: bool = False, app_name: str | None = None
) -> None:
    """Configure logging system.

    Args:
        file_path: Optional path to log file
        level: Logging level (TRACE, DEBUG, INFO, WARN, ERROR)
        json_format: Use JSON formatting if True
        app_name: Application name for logger hierarchy (e.g., 'mcp_guide')
    """
    add_trace_to_context()

    if file_path:
        handler = create_file_handler(file_path)
        formatter = create_formatter(json_format)
        handler.setFormatter(formatter)
        handler.setLevel(get_log_level(level))
        root = logging.getLogger()
        root.setLevel(get_log_level(level))
        root.addHandler(handler)

    if app_name:
        configure_logger_hierarchy(app_name)
