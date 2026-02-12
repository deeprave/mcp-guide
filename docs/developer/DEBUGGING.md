# Debugging Guide

This guide explains how to debug mcp-guide using remote debugging with debuggers that support the Debug Adapter Protocol (DAP).

## Overview

mcp-guide supports remote debugging through the `debugpy` package. This allows you to:
- Set breakpoints in the mcp-guide source code
- Step through code execution
- Inspect variables and call stacks
- Debug MCP tool calls and server behaviour

## Prerequisites

Install `debugpy`:
```bash
uv sync --extra debug
```

Or run with uvx:
```bash
uvx --with debugpy mcp-guide
```

## Environment Variables

Configure debugging using these environment variables:

- `MG_DEBUG`: Enable debugging (set to `true`, `1`, or `yes`)
- `MG_DEBUG_PORT`: Debug server port (default: `5678`)
- `MG_DEBUG_WAIT`: Wait for debugger to attach before starting (set to `true`, `1`, or `yes`)

## Usage Examples

### Quick Start (Non-Blocking)

Start the server with debugging enabled:
```bash
MG_DEBUG=true mcp-guide
```

The server will start immediately and listen for debugger connections on port 5678.

### Wait for Debugger (Blocking)

Start the server and wait for debugger to attach:
```bash
MG_DEBUG=true MG_DEBUG_WAIT=true mcp-guide
```

The server will pause at startup until you attach your debugger.

### Custom Port

Use a different debug port:
```bash
MG_DEBUG=true MG_DEBUG_PORT=9999 mcp-guide
```

## Debugging Workflow

1. **Set breakpoints** in the mcp-guide source code

2. **Start the server** with debugging enabled:
   ```bash
   MG_DEBUG=true MG_DEBUG_WAIT=true mcp-guide --docroot /path/to/docs
   ```

3. **Attach your debugger** (VS Code: Run > Start Debugging, or F5)

4. **Trigger MCP calls** from your MCP client (Claude Desktop, etc.)

5. **Debug!** Step through code, inspect variables, etc.

## MCP Client Configuration

When using with Claude Desktop or another MCP client, configure the environment variables in your client's settings.

### Claude Desktop Example

Edit your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "guide": {
      "command": "uvx",
      "args": ["--with", "debugpy", "mcp-guide", "--docroot", "/path/to/docs"],
      "env": {
        "MG_DEBUG": "true",
        "MG_DEBUG_PORT": "5678",
        "MG_DEBUG_WAIT": "true"
      }
    }
  }
}
```

**Note**: With `MG_DEBUG_WAIT=true`, Claude Desktop will wait for you to attach the debugger before the server becomes available.

## Tips

- **Use `MG_DEBUG_WAIT=false`** (or omit it) during normal operation to avoid blocking
- **Use `MG_DEBUG_WAIT=true`** when debugging server startup or initialisation
- **Set breakpoints** in tool implementations (`src/mcp_guide/tools/`) to debug specific tools
- **Check stderr output** for debug server status messages
- **Multiple instances**: Use different `MG_DEBUG_PORT` values if running multiple debug sessions

## Troubleshooting

### "debugpy not installed" warning
Install debugpy: `pip install debugpy` or use `uvx --with debugpy mcp-guide`

### Cannot connect to debug server
- Verify the port is correct (`MG_DEBUG_PORT`)
- Check if another process is using the port
- Ensure the server has started and printed "Debug server listening on port..."

### Debugger not stopping at breakpoints
- Verify path mappings in your debugger configuration
- Ensure you're debugging the correct Python process
- Check that breakpoints are in code that's actually executed

## Implementation Details

The debugging setup is implemented in `src/mcp_guide/main.py` in the `_setup_remote_debugging()` function. It:

1. Checks for `MG_DEBUG` environment variable
2. Imports `debugpy` (with graceful fallback if not installed)
3. Starts a debug server on the specified port
4. Optionally waits for debugger attachment
5. Continues normal server startup

This happens **before** any other initialisation, allowing you to debug the entire server lifecycle.
