# Getting Started with mcp-guide

This guide will help you get up and running with mcp-guide quickly.

## What is mcp-guide?

mcp-guide is an MCP (Model Context Protocol) server that provides AI agents with structured access to your project's documentation, guidelines, and context. It helps agents understand your project standards and follow development workflows.

## Installation

See the [Installation Guide](installation.md) for detailed setup instructions.

## First Run

When you first run mcp-guide, it creates a configuration directory:

- **macOS/Linux**: `~/.config/mcp-guide/`
- **Windows**: `%APPDATA%\mcp-guide\`

This directory contains:
- `config.yaml` - Single configuration file shared by all projects
- `docs/` - Your documentation and content files (docroot)

Note: The docroot is on the MCP server's filesystem, not the AI agent's filesystem.

## Understanding the Docroot

The **docroot** is where mcp-guide looks for content to serve to agents. By default, it's located at `{configDir}/docs/`.

Content is classified by the `type:` field in document frontmatter:
- `user/information` - Content displayed to users
- `agent/information` - Context for AI agents
- `agent/instruction` - Directives for agent behaviour

See [Content Management](content-management.md) for details on content types.

## Basic Concepts

### Categories

Categories organise content by file patterns and directories. For example:

```yaml
categories:
  guidelines:
    dir: guidelines
    patterns: ["readthis", "guidelines"]
```

Patterns are globs matching document basenames (not extensions).

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

## Configuring with AI Agents

See the [README](../../README.md#configure-with-ai-agents) for configuration instructions for Kiro-CLI, Claude Code, GitHub Copilot CLI, and HTTPS streaming modes.

## Using mcp-guide

Once configured, your AI agent can:

1. **Query content** - Access documentation and guidelines
2. **Use collections** - Get targeted context for specific tasks
3. **Follow workflows** - Track development phases
4. **Apply profiles** - Use pre-configured setups

### What You Can Do

As a user, you can interact with mcp-guide through your AI agent using:

- **Query content** - Ask the agent to reference specific documentation
- **Execute commands** - Use template commands for dynamic content
- **Apply profiles** - Request pre-configured setups for common scenarios
- **Use prompts** - Leverage the `@guide` or `/guide` prompt for direct access

### Using the @guide Prompt

The `@guide` prompt provides direct access to content:

```
@guide <category>[/pattern]    # Reference specific documents (no .md extension needed)
@guide :<command>               # Execute template commands
@guide :help                    # View available commands
```

Examples:
```
@guide guidelines               # Access guidelines category
@guide guidelines/python        # Access python-specific guidelines
@guide :help                    # Show available commands
```

The agent interacts with mcp-guide through MCP tools and prompts.

## Next Steps

- **[Installation Guide](installation.md)** - Detailed installation and configuration
- **[Content Management](content-management.md)** - Understanding content types
- **[Categories and Collections](categories-and-collections.md)** - Organising your content
- **[Content Documents](content-documents.md)** - Writing content with templates
- **[Feature Flags](feature-flags.md)** - Configuring behaviour
- **[Commands](commands.md)** - Using the guide prompt
- **[Profiles](profiles.md)** - Pre-configured setups

## Getting Help

- Check the [user documentation](.) for detailed guides
- Review [developer documentation](../developer/) for technical details
- Report issues on [GitHub](https://github.com/yourusername/mcp-guide/issues)

