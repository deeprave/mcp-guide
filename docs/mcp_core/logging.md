# mcp_core Logging Module

Reusable logging module for MCP servers with FastMCP integration and TRACE level support.

## Features

- **TRACE Level**: Custom log level (5) below DEBUG for detailed tracing
- **File Logging**: Text and JSON formatting with rotation support
- **PII Redaction**: Stub for future PII redaction integration
- **FastMCP Integration**: Seamless integration with FastMCP's logging system
- **Message Sanitization**: Prevents log injection attacks

## API Reference

### configure()

Configure the logging system with file output and TRACE level support.

```python
from mcp_core.mcp_log import configure

configure(
    file_path="/var/log/myapp.log",  # Optional: path to log file
    level="INFO",                     # Log level: TRACE, DEBUG, INFO, WARN, ERROR
    json_format=False,                # Use JSON formatting if True
    app_name="my_app"                 # Optional: app name for logger hierarchy
)
```

**Parameters:**
- `file_path` (str | None): Path to log file. If None, no file logging.
- `level` (str): Logging level. Default: "INFO"
- `json_format` (bool): Use JSON formatting. Default: False
- `app_name` (str | None): Application name for logger hierarchy configuration

### get_logger()

Get a logger instance with TRACE support.

```python
from mcp_core.mcp_log import get_logger

logger = get_logger(__name__)
logger.trace("Detailed trace message")
logger.debug("Debug message")
logger.info("Info message")
```

**Parameters:**
- `name` (str): Logger name (typically `__name__`)

**Returns:**
- `logging.Logger`: Logger instance with `trace()` method

**Note:** Integrates with FastMCP's `get_logger()` if available, otherwise uses standard logging.

### add_file_handler()

Add file handler to root logger with rotation support.

```python
from mcp_core.mcp_log import add_file_handler

add_file_handler(
    file_path="/var/log/myapp.log",
    level="DEBUG",
    json_format=True
)
```

**Parameters:**
- `file_path` (str): Path to log file
- `level` (str): Logging level. Default: "INFO"
- `json_format` (bool): Use JSON formatting. Default: False

**Note:** Uses `WatchedFileHandler` on Unix/Linux for log rotation support.

## TRACE Level Usage

The TRACE level (5) is below DEBUG (10) and useful for detailed execution tracing:

```python
from mcp_core.mcp_log import get_logger, TRACE_LEVEL

logger = get_logger(__name__)

# Using the trace() method
logger.trace("Entering function with args: %s", args)

# Using the TRACE_LEVEL constant
logger.log(TRACE_LEVEL, "Low-level trace message")

# Check if TRACE is enabled
if logger.isEnabledFor(TRACE_LEVEL):
    logger.trace("Expensive trace operation: %s", compute_trace_data())
```

## PII Redaction

The module includes a redaction stub for future PII detection integration:

```python
from mcp_core.mcp_log_filter import get_redaction_function

# Currently returns pass-through function
redact = get_redaction_function()
message = redact("User email: user@example.com")  # No redaction yet
```

**Future Integration Points:**
- AWS Comprehend PII detection
- Custom regex-based redaction
- Configurable redaction policies

## JSON Formatting

When `json_format=True`, logs are structured JSON:

```json
{
  "timestamp": "2025-11-27T17:30:00.123456",
  "level": "INFO",
  "logger": "mcp_guide.main",
  "message": "Starting server",
  "module": "main",
  "function": "main"
}
```

## Text Formatting

Default text format:

```
2025-11-27 17:30:00 - mcp_guide.main - INFO - Starting server
```

## Examples

### Basic Setup

```python
from mcp_core.mcp_log import configure, get_logger

# Configure logging
configure(level="INFO")

# Get logger
logger = get_logger(__name__)
logger.info("Application started")
```

### File Logging with JSON

```python
from mcp_core.mcp_log import configure, get_logger

configure(
    file_path="/var/log/myapp.log",
    level="DEBUG",
    json_format=True
)

logger = get_logger(__name__)
logger.debug("Debug information")
```

### TRACE Level Debugging

```python
from mcp_core.mcp_log import configure, get_logger

configure(level="TRACE", file_path="/tmp/trace.log")

logger = get_logger(__name__)
logger.trace("Detailed execution trace")
logger.debug("Regular debug message")
```

### FastMCP Integration

```python
from mcp_core.mcp_log import configure, get_logger

# Configure before creating FastMCP server
configure(level="INFO", file_path="/var/log/mcp.log")

# Logger automatically integrates with FastMCP
logger = get_logger(__name__)

# In FastMCP tools, Context.trace() is available
async def my_tool(ctx):
    await ctx.trace("Tool execution trace")
```

## Thread Safety

All logging operations are thread-safe. File handlers use appropriate locking mechanisms.

## Performance

- TRACE level filtering is efficient when disabled
- File handlers buffer writes for performance
- JSON formatting has minimal overhead
