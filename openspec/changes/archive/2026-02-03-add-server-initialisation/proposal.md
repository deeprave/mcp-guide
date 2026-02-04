# Change: Add Server Initialisation Hook

## Why

The MCP Guide server needs a reliable way to execute initialisation code when the server starts, before any tool calls are made. Currently, initialisation relies on `TIMER_ONCE` events triggered by the first tool call, which means:

1. Initialisation doesn't happen until a tool is called
2. No guaranteed execution order
3. Tightly coupled to task manager implementation

A proper server initialisation mechanism allows:
- Guaranteed execution on server startup
- Decoupled from specific implementations (task manager, tools)
- Extensible for multiple initialisation handlers
- Works universally across all MCP clients

## What Changes

- Add `@mcp.on_startup()` decorator for registering initialisation handlers
- Implement FastMCP lifespan hook to execute registered handlers
- Decouple initialisation from task manager and tool execution
- Allow multiple initialisation handlers to be registered

## Impact

**Affected code:**
- `src/mcp_guide/guide.py` - Add startup handler registration
- `src/mcp_guide/server.py` - Implement lifespan hook
- `src/mcp_guide/client_context/tasks.py` - Use startup decorator
- `src/mcp_guide/workflow/tasks.py` - Use startup decorator

**Breaking changes:** None - additive only

**Benefits:**
- Reliable initialisation independent of tool calls
- Clean separation of concerns
- Extensible architecture for future initialisation needs
- Works with all MCP clients without configuration
