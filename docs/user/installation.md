# Installation Guide

Complete installation and setup instructions for mcp-guide with AI agents.

## Installation with AI Agents

mcp-guide is designed to work with AI agents via the Model Context Protocol (MCP). Configure your AI agent to run mcp-guide as an MCP server.

### Common JSON configuration

This JSON block can be used with most AI CLI agents to add the MCP server.
It requires uv., python 3.11+ to be installed, and the "uvx" command to be available on the PATH.

**MCP client configuration (stdio):**

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

The following configuration requires only docker.
The volume mapping is optional

**MCP client configuration (STDIO with Docker):**

```json
{
  "mcpServers": {
    "mcp-guide": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "${HOME}/.config/mcp-guide:/home/mcp/.config/mcp-guide",
        "dlnugent/mcp-guide:latest",
        "stdio"
      ]
    }
  }
}
```

### STDIO Mode (Default)

Standard input/output for local agent communication. This is the most common configuration.

**Kiro-CLI** (`~/.config/kiro/mcp.json`):
**Claude Code** (`~/.claude/settings.json`):
**GitHub Copilot CLI** (`~/.config/.copilot/mcp.json`):

### Streaming Mode (SSE)

#### HTTP transport

Unsecured network transport:

```json
{
  "mcpServers": {
    "mcp-guide": {
      "command": "uvx",
      "args": [
        "--with",
        "uvicorn",
        "mcp-guide",
        "http://localhost:8080"
      ]
    }
  }
}
```

#### HTTPS transport

Network transport with Server-Sent Events for remote access.
Https transport requires SSL certificates, http transport does not.
Both configurations require uvicorn for serving http requests.

```json
{
  "mcpServers": {
    "mcp-guide": {
      "command": "uvx",
      "args": [
        "--with",
        "uvicorn",
        "mcp-guide",
        "https",
        "--ssl-certfile",
        "/path/to/cert.pem",
        "--ssl-keyfile",
        "/path/to/key.pem"
      ]
    }
  }
}
```

**Generating SSL Certificates** (development):

```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365
```

For production, use certificates obtained from a trusted CA (Let's Encrypt, DigiCert, etc.).
Note that no confidential information is transferred between mcp and agent - there are no login credentials or other secrets.
Https transport is recommdned when accessing the server from another host, however.


## Docker Compose

mcp-guide provides docker compose support for containerised deployments.

### `compose.yaml` supporting all three modes selected uising profiles

```yaml
services:
  mcp-guide-stdio:
    image: dlnugent/mcp-guide:latest
    profiles: [stdio]
    stdin_open: true
    tty: true
    command: ["stdio"]
    environment:
      - MG_LOG_LEVEL=${MG_LOG_LEVEL:-info}
      - MG_LOG_JSON=${MG_LOG_JSON:-1}

  mcp-guide-http:
    image: dlnugent/mcp-guide:latest
    profiles: [http]
    ports:
      - "8080:8080"
    command: ["http", "--host", "0.0.0.0", "--port", "8080"]
    environment:
      - MG_LOG_LEVEL=${MG_LOG_LEVEL:-info}
      - MG_LOG_JSON=${MG_LOG_JSON:-1}

  mcp-guide-https:
    image: dlnugent/mcp-guide:latest
    profiles: [https]
    ports:
      - "443:443"
    volumes:
      - ./cert.pem:/home/mcp/certs/cert.pem:ro
      - ./key.pem:/home/mcp/certs/key.pem:ro
    command: ["https", "--host", "0.0.0.0", "--port", "443", "--ssl-certfile", "/home/mcp/certs/cert.pem", "--ssl-keyfile", "/home/mcp/certs/key.pem"]
    environment:
      - MG_LOG_LEVEL=${MG_LOG_LEVEL:-info}
      - MG_LOG_JSON=${MG_LOG_JSON:-1}
```

### Using The Pre-built Image

```bash
docker pull dlnugent/mcp-guide:latest
```

Note that the mappings (-v) for the configuration files are optional, but ensure that configuration changes and any changes to documents in the docroot store are persisted across restarts.

### STDIO Mode

**Using docker run:**

```bash
docker run -it --rm \
  -v ~/.config/mcp-guide:/home/mcp/.config/mcp-guide \
  dlnugent/mcp-guide:latest
```

### HTTP Mode

```bash
docker run -it --rm \
  -v ~/.config/mcp-guide:/home/mcp/.config/mcp-guide \
  -p 8080:8080 \
  dlnugent/mcp-guide:latest \
  http://0.0.0.0:8080
```

Access at: `http://localhost:8080/mcp`

### HTTPS Mode

Generate certificates first:

```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365
```

Run with HTTPS:

```bash
docker run -it --rm \
  -v ~/.config/mcp-guide:/home/mcp/.config/mcp-guide \
  -v $(pwd)/cert.pem:/home/mcp/certs/cert.pem \
  -v $(pwd)/key.pem:/home/mcp/certs/key.pem \
  -p 443:443 \
  dlnugent/mcp-guide:latest \
  https://0.0.0.0:443 --ssl-certfile /home/mcp/certs/cert.pem --ssl-keyfile /home/mcp/certs/key.pem
```

Access at: `https://localhost/mcp`

## Configuration

### Configuration Directory

mcp-guide stores configuration in:

- **macOS/Linux**: `~/.config/mcp-guide/`
- **Windows**: `%APPDATA%\mcp-guide\`

Configuration & Document Structure:
```
~/.config/mcp-guide/
├── config.yaml        # Single configuration file
└── docs/             # Content files (docroot)
```

### Logging

```bash
# Log level (TRACE, DEBUG, INFO, WARN, ERROR)
export MG_LOG_LEVEL=INFO

# Log file path
export MG_LOG_FILE=/var/log/mcp-guide.log

# Enable JSON structured logging (set to 1 or any non-empty value)
export MG_LOG_JSON=1
```

### Tool Naming

```bash
# Tool name prefix (default: "guide")
export MCP_TOOL_PREFIX="guide"
```

**Note**: Some clients (like Claude Code) already prefix tool names with the MCP server name.
In these cases, set `MCP_TOOL_PREFIX=""` or start with `--no-tool-prefix` to avoid double prefixing.

### Development

```bash
# Include example tools (default: false)
export MCP_INCLUDE_EXAMPLE_TOOLS="true"
```

## Configuration

### Configuration Directory

mcp-guide stores configuration in:

- **macOS/Linux**: `~/.config/mcp-guide/`
- **Windows**: `%APPDATA%\mcp-guide\`

Structure:

```
~/.config/mcp-guide/
├── config.yaml        # Single configuration file
└── docs/             # Content files (docroot)
```

## Environment Variables

### Logging

```bash
# Log level (TRACE, DEBUG, INFO, WARN, ERROR)
export MG_LOG_LEVEL=INFO

# Log file path
export MG_LOG_FILE=/var/log/mcp-guide.log

# Enable JSON structured logging (set to 1 or any non-empty value)
export MG_LOG_JSON=1
```

### Tool and Prompt Naming

```bash
# Tool name prefix (default: "guide")
export MCP_TOOL_PREFIX="guide"

# Prompt name prefix (default: none)
export MCP_PROMPT_PREFIX="g"
```

**Note**: Some clients (like Claude Code) already prefix tool names with the MCP server name. In these cases, set `MCP_TOOL_PREFIX=""` to avoid double prefixing.

## Next Steps

- **[Getting Started](getting-started.md)** - Basic concepts and first steps
- **[Content Management](content-management.md)** - Understanding content types
- **[Categories and Collections](categories-and-collections.md)** - Organising content

