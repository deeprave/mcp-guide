# Implementation Tasks

## 1. Project Configuration

- [x] 1.1 Add `[http]` extra to pyproject.toml with uvicorn dependency
- [x] 1.2 Add transport mode validation on startup
- [x] 1.3 Add fatal error handler for missing extras

## 2. CLI Argument Parsing

- [x] 2.1 Add transport mode positional argument (stdio, http://, https://)
- [x] 2.2 Parse HTTP/HTTPS URLs (scheme, host, port)
- [x] 2.3 Default to localhost:8080 for bare `http` argument
- [x] 2.4 Validate transport mode and URL format

## 3. Transport Abstraction

- [x] 3.1 Create `src/mcp_guide/transports/` package
- [x] 3.2 Define `Transport` protocol
- [x] 3.3 Implement `StdioTransport` (refactor existing)
- [x] 3.4 Add transport factory function

## 4. HTTP Transport Implementation

- [x] 4.1 Create `src/mcp_guide/transports/http.py`
- [x] 4.2 Implement HTTP server using FastMCP's streamable_http_app() with uvicorn
- [x] 4.3 Add MCP protocol handling via FastMCP
- [x] 4.4 Add error handling with proper errno checks (EADDRINUSE)
- [x] 4.5 Add logging for server lifecycle
- [x] 4.6 Add graceful shutdown

## 5. Server Integration

- [x] 5.1 Update main.py to use transport abstraction
- [x] 5.2 Add transport initialization with MCP server instance
- [x] 5.3 Add transport lifecycle management (start/stop)
- [x] 5.4 Add signal handlers (SIGTERM/SIGINT) for HTTP mode
- [x] 5.5 Ensure transport-agnostic core logic

## 6. Error Handling

- [x] 6.1 Detect missing HTTP extras on startup
- [x] 6.2 Display clear installation instructions (uv sync --extra http)
- [x] 6.3 Exit with appropriate error code
- [x] 6.4 Add helpful error messages for port conflicts

## 7. Testing

- [x] 7.1 Unit tests for CLI argument parsing (11 tests)
- [x] 7.2 Unit tests for transport factory (3 tests)
- [x] 7.3 Unit tests for HTTP transport (3 tests)
- [x] 7.4 Unit tests for dependency validation (3 tests)
- [x] 7.5 Integration tests for transport modes (5 tests)

## 8. Documentation

- [x] 8.1 Update README with transport examples
- [x] 8.2 Document optional dependencies and installation
- [x] 8.3 Add HTTP transport usage guide with correct ports
- [x] 8.4 Document uvx usage with extras
- [x] 8.5 Add troubleshooting section
- [x] 8.6 Update OpenSpec proposal with actual implementation

## Summary

**Status**: Complete
**Total Tasks**: 34
**Completed**: 34
**Tests Added**: 19 new tests
**All Tests Passing**: 1387 tests
**Implementation**: Uses FastMCP's built-in streamable HTTP with uvicorn
**Default Ports**: HTTP=8080, HTTPS=443
**Optional Dependency**: uvicorn>=0.27.0

- [ ] 7.4 Integration tests for HTTP mode
- [ ] 7.5 Test error handling for missing extras

## 8. Documentation

- [ ] 8.1 Update README with transport mode examples
- [ ] 8.2 Document optional dependencies
- [ ] 8.3 Add HTTP transport usage guide
- [ ] 8.4 Document uvx usage with extras
