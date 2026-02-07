# mcp-guide

MCP server for managing project guidelines, development rules, and controlled workflows with AI agents.

## What is mcp-guide?

mcp-guide is a Model Context Protocol (MCP) server that helps AI agents understand and follow your project's guidelines, coding standards, and development workflows. It provides structured access to project documentation, rules, and context.

## Features

- **Project Guidelines Management** - Organize and serve project-specific guidelines to AI agents
- **Category-based Organization** - Structure content by categories (guidelines, language-specific rules, context, prompts)
- **Template Support** - Generate content using Mustache templates
- **Session Management** - Per-project configuration and state management

## Installation

### Using uvx (recommended)

```bash
# Run directly without installation
uvx mcp-guide

# With HTTP transport support
uvx --with uvicorn mcp-guide
```

### Using uv

```bash
# Install from source
git clone https://github.com/yourusername/mcp-guide.git
cd mcp-guide
uv sync

# With HTTP transport support
uv sync --extra http
```

## Transport Modes

mcp-guide supports multiple transport modes:

### STDIO (default)
Standard input/output for local agent communication:
```bash
mcp-guide stdio
# or simply
mcp-guide
```

### HTTP/HTTPS
Network transport for remote access or web applications:
```bash
# HTTP on localhost:8080 (default)
mcp-guide http

# HTTP on custom host:port
mcp-guide http://localhost:3000

# HTTPS on 0.0.0.0:443 (default)
mcp-guide https

# HTTPS on custom port
mcp-guide https://:8443
```

**Note**: HTTP/HTTPS transport requires uvicorn:
```bash
uv sync --extra http
# or with uvx
uvx --with uvicorn mcp-guide
```

**Troubleshooting**:
- If you get "Port already in use", specify a different port: `mcp-guide http://localhost:3000`
- Port 80/443 require root privileges - use higher ports (8080, 8443) for development

## Configuration

### Claude Desktop (STDIO)

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mcp-guide": {
      "command": "uvx",
      "args": ["mcp-guide"]
    }
  }
}
```

### Claude Desktop (HTTP)

For HTTP transport with uvicorn support:

```json
{
  "mcpServers": {
    "mcp-guide": {
      "command": "uvx",
      "args": ["--with", "uvicorn", "mcp-guide", "http://localhost:8080"]
    }
  }
}
```

### Other MCP Clients

mcp-guide works with any MCP-compatible client. Configure with the appropriate transport mode:

**STDIO (default)**:
```json
{
  "command": "uvx",
  "args": ["mcp-guide"]
}
```

**HTTP**:
```json
{
  "command": "uvx",
  "args": ["--with", "uvicorn", "mcp-guide", "http://localhost:8080"]
}
```

**HTTPS**:
```json
{
  "command": "uvx",
  "args": ["--with", "uvicorn", "mcp-guide", "https://:8443"]
}
```

## Usage

Once configured, your AI agent can access mcp-guide's tools and prompts to:

- Query project guidelines and rules
- Access language-specific coding standards
- Retrieve project context and documentation
- Follow structured development workflows

### Resource Access

mcp-guide supports MCP resources via the `guide://` URI scheme:

```
guide://collection/document
```

Example: `guide://lang/python` retrieves Python language guidelines.

For details, see `guide://docs/guide-uri-scheme.md`

*(Note: Tools and prompts are currently under development)*

## Logging

For debugging or monitoring, enable logging with environment variables:

```bash
# Basic logging
MG_LOG_LEVEL=INFO MG_LOG_FILE=/var/log/mcp-guide.log mcp-guide

# Debug mode
MG_LOG_LEVEL=DEBUG MG_LOG_FILE=/tmp/debug.log mcp-guide
```

Available log levels: TRACE, DEBUG, INFO, WARN, ERROR

## Environment Variables

**MCP_TOOL_PREFIX** - Tool name prefix (default: "guide")
```bash
export MCP_TOOL_PREFIX="guide"  # Tools named: guide_tool_name
```

**MCP_PROMPT_PREFIX** - Guide prompt prefix (default: None)
```bash
export MCP_PROMPT_PREFIX="g"  # Prompt named: g_guide
```

Using these renaming conventions avoids naming collisions in tools (common) and prompts (much less likely).
In agents that already prefix tools with the mcp names such as Claude Code, the MCP_TOOL_PREFIX should be set to an empty value (not unset).

**MCP_INCLUDE_EXAMPLE_TOOLS** - Include example tools (default: false)
```bash
export MCP_INCLUDE_EXAMPLE_TOOLS="true"  # For development
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and contribution guidelines.

## License

MIT License - See [LICENSE.md](LICENSE.md) for details

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/mcp-guide/issues)
- **Documentation**: [docs/](docs/)
- **MCP Protocol**: [Model Context Protocol](https://modelcontextprotocol.io/)
