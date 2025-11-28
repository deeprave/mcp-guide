# Contributing to mcp-guide

## Development Setup

### Requirements

- Python 3.13+
- uv package manager

### Installation

```bash
uv sync --all-groups
```

## Development Workflow

### Running Tests

```bash
uv run pytest
```

Run with coverage:
```bash
uv run pytest --cov=src --cov-report=term-missing
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

## Architecture

mcp-guide uses a monorepo structure with two packages:

- **mcp_core** - Reusable core functionality (logging, utilities)
- **mcp_guide** - Guide-specific implementation (server, tools, prompts)

### Key Technologies

- **FastMCP** - MCP server implementation
- **Chevron** - Template-based content generation
- **Pydantic** - Data validation and settings management

## Logging

### Configuration

Logging is configured via environment variables:

- `MG_LOG_LEVEL`: Log level (TRACE, DEBUG, INFO, WARN, ERROR). Default: INFO
- `MG_LOG_FILE`: Path to log file. If not set, logs to stderr only
- `MG_LOG_JSON`: Use JSON formatting (true/1/yes). Default: false

### Examples

**Basic logging to file:**
```bash
MG_LOG_LEVEL=INFO MG_LOG_FILE=/var/log/mcp-guide.log mcp-guide
```

**TRACE level debugging:**
```bash
MG_LOG_LEVEL=TRACE MG_LOG_FILE=/tmp/debug.log mcp-guide
```

**JSON formatted logs:**
```bash
MG_LOG_LEVEL=INFO MG_LOG_FILE=/var/log/mcp-guide.log MG_LOG_JSON=true mcp-guide
```

### Log Formats

**Text format (default):**
```
2025-11-27 17:30:00 - mcp_guide.main - INFO - Starting mcp-guide server
```

**JSON format:**
```json
{"timestamp": "2025-11-27T17:30:00.123456", "level": "INFO", "logger": "mcp_guide.main", "message": "Starting mcp-guide server"}
```

See [docs/mcp_core/logging.md](docs/mcp_core/logging.md) for detailed API documentation.

## Testing

### Unit Tests

Unit tests are located in `tests/` and cover individual modules.

### Integration Tests

Integration tests use the MCP SDK client to test the server end-to-end:

```bash
uv run pytest tests/integration/
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Maximum line length: 120 characters
- Use descriptive variable names

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with tests
3. Ensure all tests pass and code is formatted
4. Update documentation as needed
5. Submit a pull request with a clear description

## License

MIT License - See LICENSE.md for details
