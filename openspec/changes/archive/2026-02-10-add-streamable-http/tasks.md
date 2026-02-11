# Implementation Tasks

## Phase 1: Core HTTP Transport
- [x] Add HTTP/HTTPS transport modes to CLI
- [x] Implement URL parsing (scheme, host, port)
- [x] Create HttpTransport class using FastMCP's streamable_http_app()
- [x] Add transport factory support for HTTP/HTTPS
- [x] Configure uvicorn server with SSL support
- [x] Add optional [http] dependency group

## Phase 2: SSL Configuration
- [x] Add --ssl-certfile and --ssl-keyfile CLI options
- [x] Pass SSL configuration to HttpTransport
- [x] Configure uvicorn with SSL certificates
- [x] Validate SSL configuration at server start
- [x] Support combined certificate bundles (cert + key in one file)
- [x] Make ssl_keyfile optional when key is in certfile

## Phase 3: Path Prefix Support
- [x] Extend URL parsing to extract path component
- [x] Add path_prefix parameter to HttpTransport
- [x] Mount MCP app at custom path using Starlette
- [x] Normalize paths (strip leading/trailing slashes)
- [x] Handle paths ending with "mcp" (no duplication)
- [x] Update endpoint logging to show full path

## Phase 4: Error Handling
- [x] Wrap Starlette imports for consistent MissingDependencyError
- [x] Validate ssl_keyfile requires ssl_certfile
- [x] Add clear error messages for SSL configuration
- [x] Handle port already in use errors
- [x] Validate HTTPS requires ssl_certfile

## Phase 5: Testing
- [x] Add tests for URL parsing with paths
- [x] Add tests for path normalization (trailing slashes)
- [x] Add tests for /mcp path handling
- [x] Add tests for HTTP transport lifecycle
- [x] Add tests for SSL configuration
- [x] Verify all 1395 tests passing

## Phase 6: Documentation
- [x] Document HTTP/HTTPS transport modes in README
- [x] Add examples for path prefixes
- [x] Document SSL certificate configuration
- [x] Document combined certificate bundles
- [x] Add endpoint URL examples
- [x] Document self-signed certificate usage

## Summary

All tasks completed. HTTP/HTTPS transport fully implemented with:
- Streamable HTTP protocol (FastMCP default)
- Configurable path prefixes for API versioning
- Flexible SSL configuration (separate or combined files)
- Comprehensive error handling and validation
- Full test coverage (1395 tests passing)
