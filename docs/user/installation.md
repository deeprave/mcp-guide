# Installation Guide

Complete installation and setup instructions for mcp-guide with AI agents.

## Installation with AI Agents

mcp-guide is designed to work with AI agents via the Model Context Protocol (MCP). Configure your AI agent to run mcp-guide as an MCP server.

### Common JSON configuration

This JSON block can be used with most AI CLI agents to add the MCP server.
It requires uv, Python 3.11+ to be installed, and the "uvx" command to be available on the PATH.

mcp-guide supports three transport modes:

- **STDIO** - Standard input/output for local agent communication (most common)
- **HTTP** - Non-secure network transport using Server-Sent Events (SSE)
- **HTTPS** - Secure network transport using Server-Sent Events (SSE) with SSL certificates

MCP client configuration (STDIO):

```json
{
  "mcpServers": {
    "mcp-guide": {
      "command": "uvx",
      "args": ["mcp-guide"],
      "env": {
        "MCP_TOOL_PREFIX": ""
      }
    }
  }
}
```

**Note:** The `env` section is optional but recommended for Claude Code to avoid double-prefixing of tool names.

The following configuration requires only docker. The host volume mapping is optional but recommended to persist any changes you make to documents.

MCP client configuration (STDIO with Docker):

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

Configuration locations:
- Kiro-CLI: `~/.kiro/settings/mcp.json`
- Claude Code: `~/.claude/settings.json`
- GitHub Copilot CLI: `~/.config/.copilot/mcp.json`

### Streaming Mode (SSE)

#### HTTP transport

MCP client configuration (HTTP):

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
HTTPS transport requires SSL certificates, HTTP transport does not.
Both configurations require uvicorn for serving HTTP requests.

MCP client configuration (HTTPS):

```json
{
  "mcpServers": {
    "mcp-guide": {
      "command": "uvx",
      "args": [
        "--with",
        "uvicorn",
        "mcp-guide",
        "https://localhost:8443",
        "--ssl-certfile",
        "/path/to/cert.pem",
        "--ssl-keyfile",
        "/path/to/key.pem"
      ]
    }
  }
}
```

**Note:** Port 443 (default HTTPS) requires root/admin privileges. Use port 8443 or another non-privileged port (>1024) for development.

Generating SSL certificates (development):

```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365
```

For production, use certificates obtained from a trusted CA (Let's Encrypt, DigiCert, etc.).
Alternatively, use a reverse proxy like nginx or Apache to handle SSL termination and forward requests to mcp-guide over HTTP.
Note that no confidential information is transferred between mcp and agent - there are no login credentials or other secrets.
HTTPS transport is recommended when accessing the server from another host, however.


## Docker Compose

mcp-guide provides docker compose support for containerised deployments. Use the `--profile` flag to select which service to run (e.g., `docker compose --profile http up`).

Docker compose configuration:

```yaml
services:
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

**Note:** STDIO mode cannot be used in a compose configuration because it requires the MCP client to start the MCP server to attach stdin/stdout used for message exchange. In HTTP/HTTPS mode, the MCP server runs independently from the AI client and communicates over the network using the HTTP protocol.

Pull the pre-built image:

```bash
docker pull dlnugent/mcp-guide:latest
```

Note that the volume mappings (-v) for configuration files are optional, but ensure that configuration changes and any changes to documents in the docroot store are persisted across restarts.

### Docker STDIO Mode

Run with docker:

```bash
docker run -it --rm \
  -v ~/.config/mcp-guide:/home/mcp/.config/mcp-guide \
  dlnugent/mcp-guide:latest
```

### Docker HTTP Mode

Run with docker:

```bash
docker run -it --rm \
  -v ~/.config/mcp-guide:/home/mcp/.config/mcp-guide \
  -p 8080:8080 \
  dlnugent/mcp-guide:latest \
  http://0.0.0.0:8080
```

Access at: `http://localhost:8080/mcp`

### Docker HTTPS Mode

Generate certificates:

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

## Other Commands

### mcp-install

Install or update the template and document store. Run this after installation or to update to the latest templates.

From repository or installed package:
```bash
mcp-install
```

Via uvx:
```bash
uvx --from mcp-guide mcp-install
```

Use `--help` to display usage information:
```bash
mcp-install --help
```

### guide-agent-install

Install mcp-guide configuration for specific AI agents. Automates the setup process by creating the appropriate configuration files.

From repository or installed package:
```bash
guide-agent-install <agent> <dir>
```

Via uvx:
```bash
uvx --from mcp-guide guide-agent-install <agent> <dir>
```

**Usage:**
- No arguments: Display README with general information
- Agent only: Display agent-specific README
- Agent and directory: Install configuration for the specified agent

Use `--help` to display usage information:
```bash
guide-agent-install --help
```

## Configuration

### Configuration Directory

mcp-guide stores configuration in:

- **macOS/Linux**: `~/.config/mcp-guide/`
- **Windows**: `%APPDATA%\mcp-guide\`

Directory structure:

```
~/.config/mcp-guide/
├── config.yaml        # Single configuration file
└── docs/             # Content files (docroot)
```

### Logging

Environment variables:

```bash
# Log level (TRACE, DEBUG, INFO, WARN, ERROR)
export MG_LOG_LEVEL=INFO

# Log file path
export MG_LOG_FILE=/var/log/mcp-guide.log

# Enable JSON structured logging (set to 1 or any non-empty value)
export MG_LOG_JSON=1
```

### Tool Naming

Environment variable:

```bash
# Tool name prefix (default: "guide")
export MCP_TOOL_PREFIX="guide"
```

This can also be configured in the MCP client configuration using the `env` section (see the stdio configuration example above).

**Note**: Some clients (like Claude Code) already prefix tool names with the MCP server name.
In these cases, set `MCP_TOOL_PREFIX=""` or start with `--no-tool-prefix` to avoid double prefixing.

## Next Steps

- **[Getting Started](getting-started.md)** - Basic concepts and first steps
- **[Content Management](content-management.md)** - Understanding content types
- **[Categories and Collections](categories-and-collections.md)** - Organising content

