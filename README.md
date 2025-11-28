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

### Using uv (recommended)

```bash
# Install from source
git clone https://github.com/yourusername/mcp-guide.git
cd mcp-guide
uv sync
```

### Using pip

```bash
pip install mcp-guide
```

## Configuration

### Claude Desktop

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mcp-guide": {
      "command": "uv",
      "args": ["run", "mcp-guide"]
    }
  }
}
```

### Other MCP Clients

mcp-guide works with any MCP-compatible client. Configure it to run:

```bash
mcp-guide
```

The server communicates via STDIO transport.

## Usage

Once configured, your AI agent can access mcp-guide's tools and prompts to:

- Query project guidelines and rules
- Access language-specific coding standards
- Retrieve project context and documentation
- Follow structured development workflows

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

## Tool Development

mcp-guide follows standardized conventions for tool implementation. See [Tool Implementation Guide](docs/tool-implementation.md) for details.

### Tool Conventions

- **Result Pattern**: All tools return `Result[T]` for rich error handling
- **ToolArguments**: Pydantic-based argument validation with automatic schema generation
- **Tool Decorator**: Automatic registration with logging and prefixing
- **Instruction Field**: Guide agent behavior through result instructions

### Environment Variables

**MCP_TOOL_PREFIX** - Tool name prefix (default: "guide")
```bash
export MCP_TOOL_PREFIX="guide"  # Tools named: guide_tool_name
```

**MCP_INCLUDE_EXAMPLE_TOOLS** - Include example tools (default: false)
```bash
export MCP_INCLUDE_EXAMPLE_TOOLS="true"  # For development
```

### References

- [ADR-008: Tool Definition Conventions](docs/adr/008-tool-definition-conventions.md)
- [ADR-003: Result Pattern](docs/adr/003-result-pattern.md)
- [Tool Implementation Guide](docs/tool-implementation.md)

## Project Structure

```
mcp-guide/
├── guide/          # Project guidelines
├── lang/           # Language-specific rules
├── context/        # Project context
└── prompt/         # Prompt templates
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and contribution guidelines.

## License

MIT License - See [LICENSE.md](LICENSE.md) for details

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/mcp-guide/issues)
- **Documentation**: [docs/](docs/)
- **MCP Protocol**: [Model Context Protocol](https://modelcontextprotocol.io/)
