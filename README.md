# mcp-guide

**Structured content delivery for AI agents via Model Context Protocol**

mcp-guide is an MCP server that provides AI agents with organised access to project guidelines, documentation, and context. It helps agents understand your project's standards, follow development workflows, and access relevant information through a flexible content management system.

## Key Features

- **Content Management** - Organise documents, instructions and prompts by category and collection
- **Template Support** - Dynamic content with Mustache/Chevron templates
- **Multiple Transports** - STDIO, HTTP, and HTTPS modes
- **Feature Flags** - Project-specific and global configuration
- **Workflow Management** - Structured development phase tracking
- **Profile System** - Pre-configured setups for common scenarios
- **Docker Support** - Containerised deployment with SSL
- **OpenSpec Integration** - Spec-driven development workflow

## Quick Start

mcp-guide is run using your AI Agent's MCP configuration, and not usually run directly, at least in stdio transport mode.
In stdio mode, standard input and output are used to communicate with the MCP so the agent needs to control both in order
to operate.
In http mode, however, the server provides web server (http) transport, and this may be started in standalone mode, not
necessarily by the agent directly (although typically it does).

The configurations below detail configuration with some cli agents, but almost all of them will be similar.

### Configure with AI Agents

#### JSON configuration

These block can be used as is, and inserted into the agent's configuration.
The stdio mode is a straight-forward configuration, although it requires to uv tool to be installed.

##### Stdio
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

If the "mcpServers" block already exists, add the "mcp-guide" block at the end, ensuring that the previously last item, if any, has a terminating comma.

#### Kiro-CLI

Add the above JSON block to `~/.config/kiro/mcp.json`:

#### Claude Code

Add the above JSON block to `~/.claude/settings.json`:

#### GitHub Copilot CLI

Add to `~/.config/.copilot/mcp.json`:

## Content Organisation

mcp-guide organises content using **frontmatter** (optional YAML metadata at the start of documents) to define document properties and behaviour.

Content is classified into three types via the `type:` field in frontmatter:

  - **user/information** - Content displayed to users
  - **agent/information** - Context for AI agents
  - **agent/instruction** - Directives for agent behaviour

Content is organised using **categories** (file patterns and directories) and **collections** (groups of categories). Collections act as "macros" to provide targeted context for specific tasks or purposes.

See [Content Management](docs/user/content-management.md) for details.

## Feature Flags

Feature flags control behaviour, capabilities and special features and may be set globally or per project:

- **workflow** - Enable workflow phase tracking
- **openspec** - Enable OpenSpec integration
- **content-style** - Output format (None, plain, mime)

See [Feature Flags](docs/user/feature-flags.md) for more information.

## Documentation

- **[Documentation Index](docs/index.md)** - Documentation overview
- **[Getting Started](docs/user/getting-started.md)** - First-time setup and basic concepts
- **[Installation Guide](docs/user/installation.md)** - Detailed installation and configuration
- **[Changelog](CHANGELOG.md)** - Release notes and version history

## Links

- **Documentation**: [docs/user/](docs/user/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/mcp-guide/issues)
- **MCP Protocol**: [modelcontextprotocol.io](https://modelcontextprotocol.io/)

## License

MIT License - See [LICENSE.md](LICENSE.md) for details.
