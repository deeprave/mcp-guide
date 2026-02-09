# mcp-guide

**Structured content delivery for AI agents via Model Context Protocol**

mcp-guide is an MCP server that provides AI agents with organized access to project guidelines, documentation, and context. It helps agents understand your project's standards, follow development workflows, and access relevant information through a flexible content management system.

## Key Features

- **Content Management** - Organize documentation by categories and collections
- **Template Support** - Dynamic content with Mustache/Chevron templates
- **Multiple Transports** - STDIO, HTTP, and HTTPS modes
- **Feature Flags** - Project-specific and global configuration
- **Workflow Management** - Structured development phase tracking
- **Profile System** - Pre-configured setups for common scenarios
- **Docker Support** - Containerized deployment with SSL
- **OpenSpec Integration** - Spec-driven development workflow

## Quick Start

```bash
# Run with uvx (recommended)
uvx mcp-guide

# Or install with uv
uv tool install mcp-guide
```

### Configure with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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

## Documentation

- **[Getting Started](docs/user/getting-started.md)** - First-time setup and basic concepts
- **[Installation Guide](docs/user/installation.md)** - Detailed installation and configuration
- **[User Documentation](docs/user/)** - Complete user guides
- **[Developer Documentation](docs/developer/)** - Technical reference
- **[Changelog](CHANGELOG.md)** - Release notes and version history

## Transport Modes

### STDIO (Default)
Standard input/output for local agent communication:
```bash
mcp-guide
```

### HTTP/HTTPS
Network transport for remote access:
```bash
# HTTP (requires uvicorn)
uvx --with uvicorn mcp-guide http://localhost:8080

# HTTPS with SSL certificates
uvx --with uvicorn mcp-guide https --ssl-certfile cert.pem --ssl-keyfile key.pem
```

### Docker
Containerized deployment:
```bash
cd docker
docker compose --profile stdio up
```

See [Installation Guide](docs/user/installation.md) for detailed setup instructions.

## Content Organization

mcp-guide organizes content into three types:

- **user/information** - Content displayed to users
- **agent/information** - Context for AI agents
- **agent/instruction** - Directives for agent behavior

Content is organized using **categories** (file patterns and directories) and **collections** (groups of categories). Collections act as "macros" to provide targeted context for specific tasks.

See [Content Management](docs/user/content-management.md) for details.

## Feature Flags

Control behavior with project-specific or global flags:

- **workflow** - Enable workflow phase tracking
- **openspec** - Enable OpenSpec integration
- **content-style** - Output format (plain, mime)

See [Feature Flags](docs/user/feature-flags.md) for complete reference.

## Development

```bash
# Clone and install
git clone https://github.com/yourusername/mcp-guide.git
cd mcp-guide
uv sync

# Run tests
uv run pytest

# Format and lint
uv run ruff format src tests
uv run ruff check src tests
uv run mypy src
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

MIT License - See [LICENSE.md](LICENSE.md) for details.

## Links

- **Documentation**: [docs/user/](docs/user/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/mcp-guide/issues)
- **MCP Protocol**: [modelcontextprotocol.io](https://modelcontextprotocol.io/)

