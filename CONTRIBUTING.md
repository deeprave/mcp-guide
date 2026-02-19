# Contributing to mcp-guide

## Development Setup

### Requirements

- Python 3.11+
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

### Key Technologies

- **FastMCP** - MCP server implementation
- **Chevron** - Template-based content generation
- **Pydantic** - Data validation and settings management

### Development Workflow

This project uses **OpenSpec** for spec-driven development:

- Specifications are in `openspec/specs/`
- Changes are proposed in `openspec/changes/`
- See `openspec/AGENTS.md` for the full workflow

Use OpenSpec commands to manage changes:
```bash
openspec list              # View active changes
openspec validate --strict # Validate specifications
```

## Docker Development

Docker support includes both STDIO and HTTP transports:

**STDIO mode (for local development):**
```bash
docker compose --profile stdio up
```

**HTTP mode (for remote access):**
```bash
docker compose --profile http up
```

See `docker/README.md` for SSL certificate setup and detailed configuration.

## Agent Configurations

Pre-configured agent setups are available for common AI coding assistants. Install using the `guide-agent-install` command:

```bash
# List available agents
guide-agent-install --list

# Show agent-specific README
guide-agent-install <agent>

# Install configuration
guide-agent-install <agent> <directory>
```

Available agents: `kiro`, `claude`, `copilot`

Each agent has specific configuration files that are installed to the appropriate directory for that agent.

## Feature Flags

### Development Flag

The `guide-development` flag enables less aggressive caching during development, making template and content changes immediately visible.

**To enable this flag, ask your AI agent to set it:**
- "Enable the guide-development flag for this project"
- "Set guide-development to true"

The agent will use the appropriate MCP tools (`guide_set_feature_flag` or `guide_set_project_flag`) to configure this.

## Profiles

Profiles provide pre-configured category and collection setups for common scenarios. Profiles are composable - multiple profiles can be applied to build complex configurations.

**To use profiles, ask your AI agent:**
- "What profiles are available?"
- "Apply the [profile-name] profile to this project"

The agent will use MCP tools (`guide_list_profiles`, `guide_use_project_profile`) to manage profiles.

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
