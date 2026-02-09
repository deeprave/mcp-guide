# Installation Guide

Complete installation and setup instructions for mcp-guide.

## Installation Methods

### Using uvx (Recommended)

Run mcp-guide without installation:

```bash
uvx mcp-guide
```

With HTTP/HTTPS support:

```bash
uvx --with uvicorn mcp-guide
```

### Using uv tool

Install as a tool:

```bash
uv tool install mcp-guide
```

With HTTP/HTTPS support:

```bash
uv tool install mcp-guide[http]
```

### Using pip

```bash
pip install mcp-guide
```

With HTTP/HTTPS support:

```bash
pip install mcp-guide[http]
```

### From Source

```bash
git clone https://github.com/yourusername/mcp-guide.git
cd mcp-guide
uv sync

# With HTTP/HTTPS support
uv sync --extra http
```

## Transport Modes

mcp-guide supports three transport modes for different use cases.

### STDIO (Default)

Standard input/output for local agent communication:

```bash
mcp-guide
# or explicitly
mcp-guide stdio
```

**Use when**: Running locally with desktop AI clients (Claude Desktop, etc.)

### HTTP

Network transport for remote access:

```bash
# Default: http://localhost:8080
mcp-guide http

# Custom host and port
mcp-guide http://localhost:3000

# With path prefix
mcp-guide http://localhost:8080/v1
```

**Endpoint**: The `/mcp` path is automatically appended (e.g., `http://localhost:8080/mcp`)

**Use when**: Accessing from web applications or remote clients

**Requirements**: Requires uvicorn (`uvx --with uvicorn` or `uv sync --extra http`)

### HTTPS

Secure network transport with SSL:

```bash
# With separate certificate and key files
mcp-guide https --ssl-certfile cert.pem --ssl-keyfile key.pem

# With combined certificate bundle
mcp-guide https --ssl-certfile bundle.pem

# Custom port
mcp-guide https://:8443 --ssl-certfile cert.pem --ssl-keyfile key.pem
```

**Use when**: Production deployments requiring secure communication

**Requirements**: SSL certificates and uvicorn

#### Generating SSL Certificates

**Development (self-signed)**:

```bash
# Separate files
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365

# Combined bundle
openssl req -x509 -newkey rsa:4096 -nodes \
  -out bundle.pem -keyout bundle.pem -days 365
```

**Production**: Use certificates from a trusted CA (Let's Encrypt, DigiCert, etc.)

**Alternative**: Use a reverse proxy (nginx, Caddy) for TLS termination with HTTP mode

## Docker Deployment

mcp-guide provides Docker support for containerized deployments.

### Building the Base Image

```bash
cd docker
docker build -t mcp-guide:base -f Dockerfile ..
```

### STDIO Mode

```bash
docker compose --profile stdio up
```

### HTTPS Mode

Generate certificates first:

```bash
./generate-certs.sh --self
```

Then start the container:

```bash
docker compose --profile https up
```

Access at: `https://localhost/mcp`

See [docker/README.md](../../docker/README.md) for detailed Docker documentation.

## Configuration

### Configuration Directory

mcp-guide stores configuration in:

- **macOS/Linux**: `~/.config/mcp-guide/`
- **Windows**: `%APPDATA%\mcp-guide\`

Structure:

```
~/.config/mcp-guide/
├── projects/           # Per-project configurations
│   └── <project>/
│       └── config.yaml
└── docroot/           # Content files
    ├── user/
    │   └── information/
    ├── agent/
    │   ├── information/
    │   └── instruction/
    └── commands/
```

### Claude Desktop Configuration

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**STDIO**:

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

**HTTP**:

```json
{
  "mcpServers": {
    "mcp-guide": {
      "command": "uvx",
      "args": ["--with", "uvicorn", "mcp-guide", "http://localhost:8080"]
    }
  }
}
```

### Other MCP Clients

mcp-guide works with any MCP-compatible client. Use the appropriate transport configuration for your client.

## Environment Variables

### Logging

```bash
# Log level (TRACE, DEBUG, INFO, WARN, ERROR)
export MG_LOG_LEVEL=INFO

# Log file path
export MG_LOG_FILE=/var/log/mcp-guide.log
```

### Tool and Prompt Naming

```bash
# Tool name prefix (default: "guide")
export MCP_TOOL_PREFIX="guide"

# Prompt name prefix (default: none)
export MCP_PROMPT_PREFIX="g"
```

**Note**: Some clients (like Claude Code) already prefix tool names with the MCP server name. In these cases, set `MCP_TOOL_PREFIX=""` to avoid double prefixing.

### Development

```bash
# Include example tools (default: false)
export MCP_INCLUDE_EXAMPLE_TOOLS="true"
```

## Troubleshooting

### Port Already in Use

If you get "Port already in use" with HTTP/HTTPS mode:

```bash
# Use a different port
mcp-guide http://localhost:3000
```

### Permission Denied (Ports 80/443)

Ports 80 and 443 require root privileges. Use higher ports for development:

```bash
mcp-guide http://localhost:8080
mcp-guide https://:8443 --ssl-certfile cert.pem --ssl-keyfile key.pem
```

### SSL Certificate Errors

For self-signed certificates, clients may reject the connection. Options:

1. Use a reverse proxy with valid certificates
2. Configure client to trust self-signed certificates
3. Use HTTP mode for development

### Configuration Not Loading

Ensure the configuration directory exists and has proper permissions:

```bash
# macOS/Linux
ls -la ~/.config/mcp-guide/

# Windows
dir %APPDATA%\mcp-guide\
```

## Next Steps

- **[Getting Started](getting-started.md)** - Basic concepts and first steps
- **[Content Management](content-management.md)** - Understanding content types
- **[Categories and Collections](categories-and-collections.md)** - Organizing content

