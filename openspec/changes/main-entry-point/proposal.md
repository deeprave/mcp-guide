# Proposal: Main Entry Point and Server Initialization

## Metadata
- **Epic**: MG-18 - MCP Guide Architectural Reboot
- **Issue**: MG-19 - Minimal MCP server in stdio mode
- **Assignee**: David Nugent

## Overview

Implement the minimal main entry point that starts the MCP server with STDIO transport.

## Motivation

Establish the foundational server initialization code that:
- Provides a clean entry point for the MCP server
- Starts FastMCP with STDIO transport (MVP)
- Sets up async runtime properly
- Allows for future transport modes without refactoring

## Context

This is the absolute minimum needed for a working MCP server:
- Entry point that can be called from command line
- Async runtime initialization
- FastMCP server creation and startup
- Basic server metadata (name, version)

Future enhancements (documented in `openspec/ideas/transport-modes.md`):
- HTTP/HTTPS transport
- SSE transport
- OAuth authentication
- CLI options for configuration

## Objectives

1. Create main entry point in `src/mcp_guide/main.py`
2. Implement `create_server()` function in `src/mcp_guide/server.py`
3. Start FastMCP with STDIO transport
4. Configure as console script in `pyproject.toml`

## Requirements

### Main Entry Point

```python
# src/mcp_guide/main.py

import asyncio
from enum import Enum

class TransportMode(str, Enum):
    STDIO = "stdio"
    # Future transport modes:
    # HTTP = "http"
    # SSE = "sse"
    # WEBSOCKET = "websocket"

async def async_main():
    """Async entry point - starts MCP server with STDIO transport"""
    from mcp_guide.server import create_server

    mcp = create_server()
    await mcp.run_stdio_async()

def main():
    """MCP Guide Server - Main entry point"""
    asyncio.run(async_main())
        log_level: Logging level
    """
    from mcp_guide.server import create_server

    mcp = create_server()

    if transport == TransportMode.STDIO:
        await mcp.run()  # Default STDIO transport
    # Future transport implementations will go here

if __name__ == "__main__":
    main()
```

### Server Creation

```python
# src/mcp_guide/server.py

from mcp.server import FastMCP

def create_server() -> FastMCP:
    """Create and configure the MCP Guide server

    Returns:
        Configured FastMCP instance
    """
    mcp = FastMCP(
        name="mcp-guide",
        instructions="MCP server for project documentation and development guidance"
    )

    # Future: Register tools, prompts, resources here

    return mcp
```

### Console Script Configuration

```toml
# pyproject.toml

[project.scripts]
mcp-guide = "mcp_guide.main:main"
```

## Assumptions

- FastMCP is installed and available
- Python 3.13+ async runtime works correctly
- STDIO transport is sufficient for MVP

## Out of Scope

- CLI argument parsing (future)
- HTTP/HTTPS transport (future)
- OAuth authentication (future)
- Configuration file support (future)
- Tool/prompt registration (separate change)

## Success Criteria

- [ ] `mcp-guide` command starts the server
- [ ] Server responds to MCP protocol handshake
- [ ] Server runs in STDIO mode
- [ ] No errors on startup
- [ ] Can be tested with MCP inspector or Claude Desktop
