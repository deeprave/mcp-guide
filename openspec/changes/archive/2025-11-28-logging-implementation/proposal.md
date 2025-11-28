# Change: Logging Implementation

## Why

MCP servers using STDIO transport have limited logging options (stderr only), and need structured, file-based logging for debugging and monitoring. The FastMCP framework provides basic logging but lacks TRACE level support, file output, JSON formatting, and proper logger hierarchy separation to prevent duplication.

## What Changes

- Add reusable `mcp_core.mcp_log` module with TRACE level support
- Implement file logging with text and JSON formatting
- Add PII redaction stub for future integration
- Integrate with FastMCP's logging system when available
- Configure logging via environment variables (MG_LOG_LEVEL, MG_LOG_FILE, MG_LOG_JSON)
- Prevent log duplication through proper logger hierarchy configuration
- Add comprehensive unit and integration tests
- Document API and usage patterns

## Impact

**Affected specs:**
- logging (new capability)

**Affected code:**
- `src/mcp_core/mcp_log.py` (new)
- `src/mcp_core/mcp_log_filter.py` (new)
- `src/mcp_guide/main.py` (modified - add logging configuration)
- `tests/mcp_core/test_mcp_log.py` (new)
- `tests/integration/test_logging_integration.py` (new)
- `tests/test_main.py` (modified - add logging tests)
- `docs/mcp_core/logging.md` (new)
- `README.md` (modified - add user documentation)
- `CONTRIBUTING.md` (new - developer documentation)

**Breaking changes:** None - this is a new capability

**Dependencies:**
- No new external dependencies (uses stdlib logging)
- Optional integration with FastMCP (already a dependency)
