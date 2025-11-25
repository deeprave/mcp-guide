# Tasks: Main Entry Point and Server Initialization

## 1. Transport Mode Enum (TDD)

- [ ] 1.1 RED: Write test for `TransportMode` enum with STDIO value
- [ ] 1.2 GREEN: Create `src/mcp_guide/main.py` with `TransportMode` enum
- [ ] 1.3 REFACTOR: Add commented future transport modes (HTTP, SSE, WEBSOCKET)

## 2. Server Creation (TDD)

- [ ] 2.1 RED: Write test that `create_server()` returns FastMCP instance
- [ ] 2.2 RED: Write test that server has correct name, version, description
- [ ] 2.3 GREEN: Create `src/mcp_guide/server.py` with `create_server()`
- [ ] 2.4 GREEN: Initialize FastMCP with metadata
- [ ] 2.5 REFACTOR: Add docstrings and comments for future tool registration

## 3. Async Main Function (TDD)

- [ ] 3.1 RED: Write test that `async_main()` can be called with parameters
- [ ] 3.2 RED: Write test that `async_main()` calls `create_server()`
- [ ] 3.3 GREEN: Implement `async_main()` function in `main.py`
- [ ] 3.4 GREEN: Import and call `create_server()`
- [ ] 3.5 GREEN: Handle STDIO transport with `await mcp.run()`
- [ ] 3.6 REFACTOR: Add docstring documenting parameters and future transports

## 4. Main Entry Point (TDD)

- [ ] 4.1 RED: Write test that `main()` can be imported
- [ ] 4.2 RED: Write test that `main()` calls `asyncio.run()`
- [ ] 4.3 GREEN: Implement `main()` function
- [ ] 4.4 GREEN: Call `asyncio.run(async_main(...))` with defaults
- [ ] 4.5 GREEN: Add `if __name__ == "__main__"` guard
- [ ] 4.6 REFACTOR: Add module docstring with usage example

## 5. Console Script Configuration

- [ ] 5.1 Add `[project.scripts]` section to `pyproject.toml`
- [ ] 5.2 Define `mcp-guide = "mcp_guide.main:main"` entry point
- [ ] 5.3 Run `uv sync` to install package
- [ ] 5.4 Verify `mcp-guide` command is available

## 6. Integration Testing with MCP Inspector

- [ ] 6.1 Create `tests/integration/test_server_startup.py`
- [ ] 6.2 Write test fixture to start server process
- [ ] 6.3 Write test that server responds to MCP handshake
- [ ] 6.4 Write test that server advertises correct metadata
- [ ] 6.5 Manual test: `mcp-inspector --cli uv run mcp-guide`

## 7. Verification

- [ ] 7.1 Run all tests: `uv run pytest`
- [ ] 7.2 Run type checking: `uv run mypy src`
- [ ] 7.3 Run linting: `uv run ruff check src tests`
- [ ] 7.4 Verify 100% test pass rate

## 8. Check Phase

- [ ] 8.1 Run all tests: `uv run pytest`
- [ ] 8.2 Verify 100% test pass rate
- [ ] 8.3 Run type checking: `uv run mypy src`
- [ ] 8.4 Verify no type errors
- [ ] 8.5 Run linting: `uv run ruff check src tests`
- [ ] 8.6 Verify no linting warnings
- [ ] 8.7 Test with MCP Inspector: `mcp-inspector --cli uv run mcp-guide`
- [ ] 8.8 Verify server responds to handshake
- [ ] 8.9 Verify server metadata correct
- [ ] 8.10 Review all tasks marked complete
- [ ] 8.11 **READY FOR REVIEW** - Request user review
- [ ] 8.12 Address review concerns (if any)
- [ ] 8.13 **USER APPROVAL RECEIVED** - Ready for archiving
