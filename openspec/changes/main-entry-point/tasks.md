# Tasks: Main Entry Point and Server Initialization

## 1. Transport Mode Enum (TDD)

- [x] 1.1 RED: Write test for `TransportMode` enum with STDIO value
- [x] 1.2 GREEN: Create `src/mcp_guide/main.py` with `TransportMode` enum
- [x] 1.3 REFACTOR: Add commented future transport modes (HTTP, SSE, WEBSOCKET)

## 2. Server Creation (TDD)

- [x] 2.1 RED: Write test that `create_server()` returns FastMCP instance
- [x] 2.2 RED: Write test that server has correct name and instructions
- [x] 2.3 GREEN: Create `src/mcp_guide/server.py` with `create_server()`
- [x] 2.4 GREEN: Initialize FastMCP with metadata
- [x] 2.5 REFACTOR: Add comment for future tool registration

## 3. Main Entry Point (TDD)

- [x] 3.1 RED: Write test that `main()` can be imported
- [x] 3.2 RED: Write test that `main()` has no required parameters
- [x] 3.3 GREEN: Implement `main()` function
- [x] 3.4 GREEN: Call `asyncio.run(async_main())`
- [x] 3.5 GREEN: Add `if __name__ == "__main__"` guard
- [x] 3.6 REFACTOR: Simplified async_main - no unused parameters

## 4. Console Script Configuration

- [x] 4.1 Update `[project.scripts]` section in `pyproject.toml`
- [x] 4.2 Define `mcp-guide = "mcp_guide.main:main"` entry point
- [x] 4.3 Run `uv sync` to install package
- [x] 4.4 Verify `mcp-guide` command is available

## 5. Integration Testing with MCP Inspector

- [x] 5.1 Create `tests/integration/test_server_startup.py`
- [x] 5.2 Write test fixture to start server process
- [x] 5.3 Write test that server responds to MCP handshake
- [x] 5.4 Write test that server advertises correct metadata
- [x] 5.5 All integration tests pass

## 6. Bug Fix: Event Loop Issue

- [x] 6.1 Identified RuntimeError: Already running asyncio in this thread
- [x] 6.2 Fixed by using `await mcp.run_stdio_async()` instead of `mcp.run()`
- [x] 6.3 Matches mcp-server-guide pattern: asyncio.run() + run_stdio_async()
- [x] 6.4 All tests pass (14/14 including integration)

## 7. Review Feedback Addressed

- [x] 7.1 YAGNI: Removed unused parameters (host, port, log_level) from async_main()
- [x] 7.2 Spec mismatch: Updated proposal to show run_stdio_async() instead of run()
- [x] 7.3 Metadata: Updated proposal to show instructions instead of version/description
- [x] 7.4 Test reliability: Replaced fixed delays with polling + timeout
- [x] 7.5 Updated tests to match simplified async_main()

## 8. Verification

- [x] 8.1 Run all tests: `uv run pytest` - 14/14 passed
- [x] 8.2 Run type checking: `uv run mypy src` - No errors
- [x] 8.3 Run linting: `uv run ruff check src tests` - All checks passed
- [x] 8.4 Verify 100% test pass rate - ✅

## 9. Check Phase

- [x] 9.1 Run all tests: `uv run pytest`
- [x] 9.2 Verify 100% test pass rate - 14/14 passed
- [x] 9.3 Run type checking: `uv run mypy src`
- [x] 9.4 Verify no type errors - ✅
- [x] 9.5 Run linting: `uv run ruff check src tests`
- [x] 9.6 Verify no linting warnings - ✅
- [x] 9.7 Integration tests verify server startup and MCP protocol
- [x] 9.8 Server responds to handshake - ✅
- [x] 9.9 Server metadata correct - ✅ (name: mcp-guide)
- [x] 9.10 Review all tasks marked complete
- [x] 9.11 Address review feedback - ✅
- [ ] 9.12 **READY FOR REVIEW** - Request user review
- [ ] 9.13 Address review concerns (if any)
- [ ] 9.14 **USER APPROVAL RECEIVED** - Ready for archiving
