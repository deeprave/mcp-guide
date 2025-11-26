# Implement ADR 004 Logging Architecture

**Status**: Proposed
**Priority**: High
**Complexity**: Medium
**ADR**: [004-logging-architecture](../../adr/004-logging-architecture.md)
**Phase**: 1 - Foundation (mcp_core)
**Requires**: None
**Blocks**: tool-conventions

> **Note**: This implementation adds reusable logging infrastructure to the **mcp_core** package, making it available for all MCP servers in the project. The mcp_guide server will be the first consumer of this shared logging module.

## Why

mcp-guide currently lacks comprehensive logging infrastructure, making debugging and operational monitoring difficult. ADR 004 defines a logging architecture specifically designed for MCP environments with:

- **Protocol constraints**: MCP stdio uses stdin/stdout for protocol, leaving only stderr for logging
- **Dual logging needs**: Server-side operations vs client-visible tool/prompt logging require different approaches
- **FastMCP integration**: Must work with FastMCP's Rich logger without conflicts
- **Operational requirements**: Need persistent file logging with structured formats for production monitoring
- **Debug capabilities**: Need enhanced debugging with TRACE level below DEBUG

Without proper logging:
- Debugging production issues is difficult
- No persistent audit trail of operations
- Cannot monitor server health effectively
- Missing detailed trace information for complex debugging scenarios
- Tool invocations cannot be tracked

## What Changes

### New Components (mcp_core)

1. **Core Logging Module** (`src/mcp_core/mcp_log.py`)
   - Custom TRACE logging level (level=5, below DEBUG=10)
   - FastMCP integration wrapper
   - File handler management with WatchedFileHandler (Unix/Linux)
   - JSON and text formatters with redaction integration
   - Logger hierarchy separation to prevent duplication
   - Context.trace() method for client-visible logging

2. **PII Redaction Module** (`src/mcp_core/mcp_log_filter.py`)
   - Stub implementation with `get_redaction_function()` API
   - Returns pass-through function initially (no actual filtering)
   - Placeholder for future third-party package integration
   - Provides consistent API for formatters to use

### Modified Components (mcp_guide)

1. **Configuration** (`src/mcp_guide/config.py`)
   - Add `log_level` ConfigOption (default: "INFO", includes TRACE)
   - Add `log_file` ConfigOption (default: "")
   - Add `log_json` ConfigOption (default: False)

2. **Main Entry Point** (`src/mcp_guide/main.py`)
   - Import `mcp_core.mcp_log.configure` and `get_logger`
   - Configure logging from environment variables before server creation
   - Initialize logger after configuration
   - Add server startup logging

### New Documentation

1. **mcp_core Logging Guide** (`docs/mcp_core/logging.md`)
   - API reference for mcp_log module
   - Usage patterns for server-side and client-visible logging
   - Configuration examples

2. **mcp_guide Integration** (update `README.md`)
   - Logging configuration section
   - Environment variable reference
   - Usage examples specific to mcp_guide

### Reference Implementations

- `../mcp-server-atlassian/src/mcp_server_atlassian/mcp_log.py` - Reusable logging module pattern
- `../mcp-server-guide/src/mcp_server_guide/logging_config.py` - CLI integration pattern

## Technical Approach

### TRACE Level Implementation

```python
TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")

def trace(self, message, *args, **kwargs):
    if self.isEnabledFor(TRACE_LEVEL):
        sanitized = _sanitize_log_message(message)
        self._log(TRACE_LEVEL, sanitized, args, **kwargs)

logging.Logger.trace = trace
```

### Logger Hierarchy Separation

Handle both direct and FastMCP-prefixed logger patterns:
- `mcp_guide.*` - Direct application loggers
- `fastmcp.mcp_guide.*` - FastMCP-prefixed loggers

Set `propagate = False` on application loggers to prevent duplication with FastMCP's internal loggers.

### File Logging with WatchedFileHandler

```python
import sys
from logging.handlers import WatchedFileHandler

def add_file_handler(file_path: str, level: str, json_format: bool):
    """Add file handler with rotation support."""
    # Use WatchedFileHandler on Unix/Linux for rotation support
    # Falls back to FileHandler on Windows
    if sys.platform != 'win32':
        file_handler = WatchedFileHandler(file_path, mode='a')
    else:
        file_handler = logging.FileHandler(file_path, mode='a')

    file_handler.setLevel(_get_log_level(level))

    if json_format:
        formatter = StructuredJSONFormatter()
    else:
        formatter = RedactedFormatter()

    file_handler.setFormatter(formatter)
    # Add to application loggers...
```

**WatchedFileHandler behavior:**
- Monitors file inode/device changes
- Automatically reopens file if deleted/rotated externally
- Standard Python logging feature - no custom implementation needed
- Unix/Linux only - Windows uses basic FileHandler

### PII Redaction Integration

```python
# src/mcp_core/mcp_log_filter.py
def get_redaction_function() -> Callable[[str], str]:
    """Return function that redacts PII from log messages.

    Initial implementation returns pass-through function.
    Future: Integrate third-party redaction package.
    """
    def passthrough(message: str) -> str:
        return message

    return passthrough
```

Formatters call `get_redaction_function()` and apply to messages. This provides:
- Consistent API for future enhancement
- No runtime errors if redaction not configured
- Easy integration point for third-party packages

### Context.trace() for Client-Visible Logging

```python
async def trace(self, message, logger_name=None, extra=None):
    """Send TRACE-level message to MCP Client (maps to debug)."""
    sanitized = _sanitize_log_message(message)
    await self.log(
        level="debug",
        message=f"[TRACE] {sanitized}",
        logger_name=logger_name,
        extra=extra,
    )
```

### Configuration Priority

Environment variables → CLI arguments → Defaults:
1. `MG_LOG_LEVEL` (default: "INFO")
2. `MG_LOG_FILE` (default: "")
3. `MG_LOG_JSON` (default: False)

## Decisions

1. **Log rotation**: Deferred to future enhancement
   - Use `WatchedFileHandler` instead of `FileHandler` for Unix/Linux systems
   - Automatically detects when file is deleted/rotated (inode change) and recreates
   - Standard Python logging behavior - no custom implementation needed
   - Falls back to `FileHandler` on Windows (rotation not supported)

2. **PII redaction**: Include stub implementation
   - `mcp_log_filter.py` provides `get_redaction_function()` API
   - Stub returns pass-through function initially
   - Actively used by formatters in `mcp_log.py`
   - Future: integrate third-party package (logredactor, scrubadub, presidio)
   - Not implementing custom redaction - use third-party when ready

3. **Per-module log levels**: Use `__name__` pattern
   - `get_logger(__name__)` passes module name to logging system
   - Python logging module already supports per-module filtering
   - Configuration question, not implementation concern
   - Note: FastMCP prefixes loggers - must account for in filtering configuration
   - Example: `mcp_guide.tools` becomes `fastmcp.mcp_guide.tools`

## Success Criteria

1. ✅ TRACE level available and functional in both server-side and client-visible logging
2. ✅ File logging works with both text and JSON formatting
3. ✅ WatchedFileHandler used on Unix/Linux for automatic file recreation after rotation
4. ✅ Command line arguments and environment variables configure logging correctly
5. ✅ Logger hierarchy prevents duplication between application and FastMCP loggers
6. ✅ Context.trace() available for client-visible TRACE logging
7. ✅ mcp_log_filter.py exists with stub implementation actively used by formatters
8. ✅ get_logger(__name__) pattern supports per-module logging
9. ✅ All tests pass with >80% coverage (mcp_core and mcp_guide)
10. ✅ Documentation complete with usage examples for both packages
11. ✅ No breaking changes to existing functionality
12. ✅ mcp_core logging module is reusable by other MCP servers

## Migration Path

**Phase 1: Core Implementation (mcp_core)**
1. Create `src/mcp_core/mcp_log.py` with TRACE level
2. Create `src/mcp_core/mcp_log_filter.py` with stub implementation
3. Implement file logging with WatchedFileHandler (Unix/Linux) and FileHandler (Windows)
4. Implement JSON and text formatters that use redaction function
5. Add logger hierarchy separation
6. Write unit tests for mcp_core logging

**Phase 2: CLI Integration (mcp_guide)**
1. Add ConfigOptions to `src/mcp_guide/config.py`
2. Update `src/mcp_guide/main.py` to configure logging
3. Test environment variable support
4. Write integration tests for mcp_guide

**Phase 3: Documentation**
1. Create `docs/mcp_core/logging.md` with API reference
2. Update `README.md` with mcp_guide logging section
3. Add usage examples for both server-side and client-visible patterns

**Phase 4: Future Enhancement**
1. Research third-party redaction packages
2. Update `mcp_log_filter.py` with actual redaction implementation
3. Add configuration for redaction patterns

## Dependencies

**No new dependencies required for initial implementation:**
- FastMCP (already present)
- Rich (already present via FastMCP)

**Future dependencies (Phase 4):**
- PII redaction library (TBD - requires research and decision)

## References

- ADR 004: [004-logging-architecture.md](../../adr/004-logging-architecture.md)
- FastMCP Logging: https://github.com/jlowin/fastmcp
- Python Logging: https://docs.python.org/3/library/logging.html
- Python WatchedFileHandler: https://docs.python.org/3/library/logging.handlers.html#watchedfilehandler
- MCP Protocol: https://modelcontextprotocol.io/
