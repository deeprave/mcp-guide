# ADR-004: Logging Architecture in MCP Environment

**Date:** 2025-11-25
**Status:** Accepted

## Context

In an MCP (Model Context Protocol) environment, logging presents unique constraints and requirements:

1. **stdio Protocol Constraint**: MCP stdio uses stdin/stdout for protocol communication, leaving only stderr available for logging
2. **FastMCP Integration**: The FastMCP framework controls root logging and uses Rich for enhanced output
3. **Dual Logging Needs**: Server-side operations vs client-visible tool/prompt logging require different approaches
4. **Structured Logging**: Need for both human-readable and machine-parseable log formats
5. **File Logging**: Need for persistent log storage with optional JSON formatting
6. **Logger Separation**: Need to prevent log duplication between application and framework loggers

## Decision

We adopt a reusable logging module (`mcp_log.py`) that integrates with FastMCP while providing enhanced logging capabilities including file output, structured logging, and optional filtering.

### Core Logging Module

The `mcp_log` module should provide a reusable interface that wraps FastMCP logging:

```python
from .mcp_log import configure, get_logger, add_file_handler

# Basic configuration
configure(level="DEBUG")

# Optional file logging with JSON support
add_file_handler("/path/to/logfile.log", level="INFO", json_format=True)

# Usage in application code
logger = get_logger(__name__)
logger.info("Server operation completed")
logger.trace("Detailed debugging information")  # Custom TRACE level
```

### Client-Visible Logging

For tool and prompt operations where logs should be visible to MCP clients:

```python
from fastmcp import Context

@mcp.tool()
async def process_data(data: list[float], ctx: Context) -> dict:
    await ctx.debug("Processing data", {"count": len(data)})
    await ctx.trace("Detailed trace information")  # Enhanced with TRACE support
    await ctx.info("Data processed successfully")
    return {"result": "processed"}
```

### Logger Separation

The module implements proper logger hierarchy separation to prevent duplication:
- Application loggers use patterns: `<mcp_server_name>.*` and `fastmcp.<mcp_server_name>.*`
- Each pattern has `propagate = False` to prevent cross-contamination with FastMCP's internal loggers
- File handlers are added only to application logger hierarchies

### Optional Features

#### Structured Logging

JSON formatting can be enabled for file outputs:
```python
add_file_handler("app.log", json_format=True)
```

#### Structured Data with Extra Parameter

For diagnostic and debugging information that is already structured or easily structured, use the `extra` parameter to provide machine-parseable context:

```python
logger.warning(
    "Dropping non-string key in template context: %r (type: %s)",
    key, type(key).__name__,
    extra={
        "dropped_key": key,
        "key_type": type(key).__name__,
        "component": "template_context"
    }
)
```

**Benefits of `extra` parameter:**
- **Human readable**: Standard formatters show the message normally
- **Machine parseable**: Extra fields available for filtering/indexing in log aggregators
- **Future-proof**: Easy migration to structured logging without code changes
- **Automatic handling**: Python logging processes extra fields transparently

**Recommended `extra` fields:**
- `component`: Module or subsystem name (e.g., "template_context", "file_discovery")
- Context-specific fields: Error codes, file paths, user IDs, operation types
- Avoid PII in extra fields unless redaction is configured

#### Log Filtering/Redaction

Optional PII redaction via a separate `mcp_log_filter.py` module:
- Automatically imported if available
- Gracefully skipped if not present
- Provides basic patterns for emails, phone numbers, API keys
- Can be extended with dedicated packages like `logredactor`

## Consequences

### Positive

- **Protocol Compliance**: Only uses stderr, preserving stdin/stdout for MCP protocol
- **Rich Integration**: Leverages FastMCP's Rich logger for enhanced server-side output
- **Client Visibility**: Tools and prompts can send logs directly to MCP clients
- **File Persistence**: Supports persistent logging with optional JSON formatting
- **Reusable Module**: Can be used in other applications with FastMCP dependency
- **Logger Separation**: Prevents log duplication between application and framework
- **Optional Features**: Structured logging and redaction are configurable
- **TRACE Level**: Enhanced debugging with custom TRACE level support
- **Structured Context**: `extra` parameter provides machine-parseable diagnostic data without changing log format

### Negative

- **FastMCP Dependency**: Requires FastMCP framework (acceptable for MCP applications)
- **Configuration Timing**: Must configure after FastMCP server creation due to framework override behavior

### Neutral

- **stderr Only**: Acceptable constraint given MCP protocol requirements
- **Rich Dependency**: Aligns with FastMCP's existing dependencies

## Implementation Notes

### Key Principles

1. **Reusable module**: `mcp_log.py` provides framework-agnostic interface
2. **Logger hierarchy**: Proper separation prevents duplication with FastMCP loggers
3. **Optional features**: Structured logging and redaction are conditionally enabled
4. **Configuration timing**: Must happen after FastMCP server initialization
5. **Integration points**: Configuration can be driven by CLI, environment, or direct API calls
6. **Structured context**: Use `extra` parameter for diagnostic data that is already structured or easily structured

### Logger Hierarchy Details

FastMCP's `configure_logging()` creates loggers with `fastmcp.` prefix, requiring our module to handle both:
- Direct application loggers: `<mcp_server_name>.*`
- FastMCP-prefixed loggers: `fastmcp.<mcp_server_name>.*`

This dual-pattern approach ensures all application logs are captured while maintaining separation from FastMCP's internal logging.

### File Logging Features

- Configurable date formatting
- Optional JSON structured output, either/or stderr (container logging) and file
- Automatic file creation and permissions handling as required
- Handler management (add/remove capabilities)

## Status

Accepted - to be implemented in mcp-guide v2 as part of mcp_core package.

This architecture ensures proper MCP protocol compliance while providing comprehensive, reusable logging capabilities for both server operations and client-visible tool execution.
