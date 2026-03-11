# Developer Setup

This guide covers setting up mcp-guide for development.

## Prerequisites

- **Python 3.11+** - Required for modern Python features (3.13+ recommended)
- **uv** - Fast Python package installer and runner

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/deeprave/mcp-guide.git
cd mcp-guide
```

### 2. Install Dependencies

```bash
uv sync
```

This installs all dependencies including dev tools (pytest, mypy, ruff, etc.).

### 3. Configure MCP Client

Add the development server to your MCP client configuration (e.g., `~/.kiro/settings/mcp.json` for Kiro CLI):

```json
{
  "mcpServers": {
 ...
    "guide": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-guide",
        "run",
        "mcp-guide",
        "--log-file",
        "/tmp/mcp-guide.log",
        "--log-level",
        "TRACE"
      ],
      "type": "stdio",
      "timeout": 120000,
      "trusted": true
    },
  ...
  }
}
```

Replace `/path/to/mcp-guide` with your actual project path.

### 4. Symlink Templates for Live Editing

Create a symlink to work on templates without reinstalling:

```bash
mkdir -p ~/.config/mcp-guide
ln -s /path/to/mcp-guide/src/mcp_guide/templates ~/.config/mcp-guide/docs
```

After this, template changes are immediately available without restart.
You may need to clear `~/.config/mcp-guide/docs` before you do this.

## Development Workflow

### Code Changes

Any code changes require restarting the MCP server (or restart your agent/client if it cannot be done directly).

### Template Changes

Template changes are live - no restart needed (symlink makes them immediately available).

### Running Tests

```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/unit/test_session.py

# With coverage
uv run pytest --cov=mcp_guide --cov-report=html
```

### Code Quality

```bash
# Type checking
uv run mypy

# Linting
uv run ruff check

# Formatting
uv run ruff format

# All checks
uv run pytest && uv run mypy && uv run ruff check && uv run ruff format
```

**HIGHLY RECOMMENDED**: Use [pre-commit](https://pre-commit.com) as git hooks, all of these checks are within `.pre-commit-config.yaml`.

### Logging

Development logs can be written to `/tmp/mcp-guide.log` or wherever desired (configurable via `--log-file`).

Use `TRACE` level for detailed debugging:
```bash
tail -f /tmp/mcp-guide.log
```
This can be very noisy, and DEBUG level may be sufficient for many cases.

## Project Structure

```
mcp-guide/
├── src/mcp_guide/          # Source code
│   ├── agents/             # Agent configurations
│   ├── templates/          # Mustache templates and markdown docs
│   ├── tools/              # MCP tools
│   ├── prompts/            # MCP prompts
│   └── resources.py        # MCP resources
├── tests/                  # Test suite
├── docs/                   # Documentation
└── openspec/               # OpenSpec proposals
```

## Tips

- Enable `guide-development` flag for faster template reloading
- Use `@guide :status` to check server state
- Check logs for detailed error messages
