# Getting Started with mcp-guide

This guide will help you get up and running with mcp-guide quickly.

## What is mcp-guide?

mcp-guide is an MCP (Model Context Protocol) server that provides AI agents with structured access to your project's documentation, guidelines, and context. It helps agents understand your project standards and follow development workflows.

## Installation

The quickest way to get started is with `uvx`:

```bash
uvx mcp-guide
```

This runs mcp-guide without installation. For other installation methods, see the [Installation Guide](installation.md).

## First Run

When you first run mcp-guide, it creates a configuration directory:

- **macOS/Linux**: `~/.config/mcp-guide/`
- **Windows**: `%APPDATA%\mcp-guide\`

This directory contains:
- `projects/` - Per-project configurations
- `docroot/` - Your documentation and content files

## Understanding the Docroot

The **docroot** is where mcp-guide looks for content to serve to agents. By default, it's located at:

```
~/.config/mcp-guide/docroot/
```

Content is organized by type:
- `user/information/` - Content displayed to users
- `agent/information/` - Context for AI agents
- `agent/instruction/` - Directives for agent behavior

See [Content Management](content-management.md) for details on content types.

## Basic Concepts

### Projects

mcp-guide is project-aware. Each project has its own configuration stored in:

```
~/.config/mcp-guide/projects/<project-name>/config.yaml
```

Projects define categories and collections specific to that project.

### Categories

Categories organize content by file patterns and directories. For example:

```yaml
categories:
  guidelines:
    dir: guidelines
    patterns: ["*.md"]
```

### Collections

Collections group categories together. They act as "macros" to provide targeted context:

```yaml
collections:
  python-dev:
    categories:
      - guidelines
      - lang/python
```

See [Categories and Collections](categories-and-collections.md) for details.

## Configuring with Claude Desktop

Add mcp-guide to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

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

Restart Claude Desktop to load the configuration.

## Using mcp-guide

Once configured, your AI agent can:

1. **Query content** - Access documentation and guidelines
2. **Use collections** - Get targeted context for specific tasks
3. **Follow workflows** - Track development phases
4. **Apply profiles** - Use pre-configured setups

The agent interacts with mcp-guide through MCP tools and prompts.

## Next Steps

- **[Installation Guide](installation.md)** - Detailed installation and configuration
- **[Content Management](content-management.md)** - Understanding content types
- **[Categories and Collections](categories-and-collections.md)** - Organizing your content
- **[Content Documents](content-documents.md)** - Writing content with templates
- **[Feature Flags](feature-flags.md)** - Configuring behavior
- **[Commands](commands.md)** - Using the guide prompt
- **[Profiles](profiles.md)** - Pre-configured setups

## Getting Help

- Check the [user documentation](.) for detailed guides
- Review [developer documentation](../developer/) for technical details
- Report issues on [GitHub](https://github.com/yourusername/mcp-guide/issues)

