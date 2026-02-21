# mcp-guide Documentation

**Structured content delivery for AI agents via Model Context Protocol**

mcp-guide is an MCP server that provides AI agents with organised access to project guidelines, documentation, and context.

## Key Features

| Feature | Description |
|---------|-------------|
| **Content Management** | Organise documents, instructions and prompts by categories and collections |
| **Template Support** | Dynamic content with Mustache/Chevron templates |
| **Multiple Transports** | STDIO, HTTP, and HTTPS modes |
| **Feature Flags** | Project-specific and global configuration |
| **Workflow Management** | Structured development phase tracking |
| **Profile System** | Pre-configured setups for common scenarios |
| **Docker Support** | Containerised deployment with SSL |
| **OpenSpec Integration** | Spec-driven development workflow |

## Basics

- [Getting Started](user/getting-started.md) - Quick introduction and first steps
- [Installation](user/installation.md) - Installation and setup instructions
- [Prompt Commands](user/commands.md) - Prompt command reference

## User Guide

### Core Concepts
- [Categories and Collections](user/categories-and-collections.md) - Organising your project documentation
- [Documents](user/documents.md) - Understanding document types and references

### Features
- [Workflows](user/workflows.md) - Structured development phase tracking
- [OpenSpec Integration](user/openspec.md) - Spec-driven development workflow

### Configuration
- [Content Management](user/content-management.md) - Working with content in your project
- [Feature Flags](user/feature-flags.md) - Configuring project and global features
- [Profiles](user/profiles.md) - Using pre-configured project templates

### Developer Notes
- [Developer Setup](develop/SETUP.md) - Setting up mcp-guide for development
- [Command Authoring](developer/command-authoring.md) - Creating custom commands
- [Filesystem Access](developer/filesystem-access.md) - Security and access patterns
- [Debugging](developer/DEBUGGING.md) - Debugging and troubleshooting

## Resources

- [GitHub Repository](https://github.com/deeprave/mcp-guide)
- [PyPI Package](https://pypi.org/project/mcp-guide/)
- [MCP Protocol](https://modelcontextprotocol.io/)
