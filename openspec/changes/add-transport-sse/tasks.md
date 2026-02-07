# Implementation Tasks

## 1. Project Configuration

- [ ] 1.1 Add `[sse]` extra to pyproject.toml with SSE dependencies
- [ ] 1.2 Add SSE mode validation on startup
- [ ] 1.3 Add fatal error handler for missing SSE extras

## 2. CLI Argument Parsing

- [ ] 2.1 Add `sse` shorthand argument
- [ ] 2.2 Detect `/sse` path suffix in HTTP URLs
- [ ] 2.3 Default to localhost:8080/sse for bare `sse` argument
- [ ] 2.4 Validate SSE mode configuration

## 3. SSE Transport Implementation

- [ ] 3.1 Create `src/mcp_guide/transports/sse.py` (optional module)
- [ ] 3.2 Implement SSE server with streaming support
- [ ] 3.3 Add SSE event formatting
- [ ] 3.4 Add connection management for multiple clients
- [ ] 3.5 Add heartbeat/keepalive mechanism
- [ ] 3.6 Add graceful shutdown with client notification

## 4. Server Integration

- [ ] 4.1 Extend transport factory for SSE mode
- [ ] 4.2 Add SSE transport initialization
- [ ] 4.3 Add streaming response handling
- [ ] 4.4 Ensure transport-agnostic streaming logic

## 5. Error Handling

- [ ] 5.1 Detect missing SSE extras on startup
- [ ] 5.2 Display clear installation instructions
- [ ] 5.3 Exit with appropriate error code
- [ ] 5.4 Add helpful error messages for SSE-specific issues

## 6. Testing

- [ ] 6.1 Unit tests for SSE argument parsing
- [ ] 6.2 Unit tests for SSE transport (if extras installed)
- [ ] 6.3 Integration tests for SSE mode
- [ ] 6.4 Test streaming behavior
- [ ] 6.5 Test error handling for missing extras

## 7. Documentation

- [ ] 7.1 Update README with SSE mode examples
- [ ] 7.2 Document SSE optional dependencies
- [ ] 7.3 Add SSE transport usage guide
- [ ] 7.4 Document uvx usage with SSE extras
