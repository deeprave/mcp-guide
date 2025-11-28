"""Reusable MCP logging module with FastMCP integration."""

import logging
from typing import Any, Callable

from mcp_core.mcp_log_filter import get_redaction_function

# Custom TRACE level (below DEBUG=10)
TRACE_LEVEL = 5

# Track if TRACE level has been initialized
_trace_initialized = False


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
        formatted = super().format(record)
        return self._redaction_func(formatted)


class StructuredJSONFormatter(logging.Formatter):
    """JSON formatter for structured logging with PII redaction."""

    def __init__(self) -> None:
        """Initialize JSON formatter with redaction function."""
        super().__init__()
        self._redaction_func: Callable[[str], str] = get_redaction_function()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        import json
        from datetime import datetime

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

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def _get_log_level(level_name: str) -> int:
    """Convert level name to logging level constant."""
    level_upper = level_name.upper()
    if level_upper == "TRACE":
        return TRACE_LEVEL
    return getattr(logging, level_upper, logging.INFO)


def add_file_handler(file_path: str, level: str = "INFO", json_format: bool = False) -> None:
    """Add file handler with rotation support.

    Args:
        file_path: Path to log file
        level: Logging level (TRACE, DEBUG, INFO, WARN, ERROR)
        json_format: Use JSON formatting if True, text if False
    """
    import sys

    # Use WatchedFileHandler on Unix/Linux for rotation support
    if sys.platform != "win32":
        from logging.handlers import WatchedFileHandler

        file_handler = WatchedFileHandler(file_path, mode="a")
    else:
        file_handler = logging.FileHandler(file_path, mode="a")

    file_handler.setLevel(_get_log_level(level))

    formatter: logging.Formatter
    if json_format:
        formatter = StructuredJSONFormatter()
    else:
        formatter = RedactedFormatter()

    file_handler.setFormatter(formatter)

    # Add to root logger and set its level
    root_logger = logging.getLogger()
    root_logger.setLevel(_get_log_level(level))
    root_logger.addHandler(file_handler)


def _initialize_trace_level() -> None:
    """Initialize TRACE level in logging module."""
    global _trace_initialized
    if _trace_initialized:
        return

    logging.addLevelName(TRACE_LEVEL, "TRACE")

    def trace(self: logging.Logger, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log message at TRACE level."""
        if self.isEnabledFor(TRACE_LEVEL):
            sanitized_message = _sanitize_log_message(message)
            self._log(TRACE_LEVEL, sanitized_message, args, **kwargs)

    logging.Logger.trace = trace  # type: ignore
    _trace_initialized = True


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


def get_logger(name: str) -> logging.Logger:
    """Get logger with TRACE support.

    Integrates with FastMCP if available, otherwise uses standard logging.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance with trace() method
    """
    try:
        from fastmcp import get_logger as fastmcp_get_logger  # type: ignore[import-not-found]

        return fastmcp_get_logger(name)  # type: ignore[no-any-return]
    except ImportError:
        return logging.getLogger(name)


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
    _initialize_trace_level()
    add_trace_to_context()

    if file_path:
        add_file_handler(file_path, level=level, json_format=json_format)

    if app_name:
        configure_logger_hierarchy(app_name)


# Initialize TRACE level on module import
_initialize_trace_level()
