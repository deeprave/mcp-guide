# mcp-guide

MCP server for handling guidelines, project rules and controlled development workflow.

## Overview

mcp-guide is a clean reimplementation of mcp-server-guide with improved architectural patterns, featuring:

- **Monorepo structure** with two packages:
  - `mcp_core` - Reusable core functionality
  - `mcp_guide` - Guide-specific implementation
- **Modern Python** (3.13+) with strict typing
- **FastMCP** for MCP server implementation
- **Template-based** content generation with Chevron

## Requirements

- Python 3.13+
- uv package manager

## Installation

```bash
uv sync --all-groups
```

## Development

### Running Tests

```bash
uv run pytest
```

### Type Checking

```bash
uv run mypy src
```

### Linting

```bash
uv run ruff check src tests
```

### Formatting

```bash
uv run ruff format src tests
```

### Building

```bash
uv build
```

## License

MIT License - See LICENSE.md for details
