# Installation Guide

Complete installation and setup instructions for mcp-guide with AI agents.

## Installation with AI Agents

mcp-guide is designed to work with AI agents via the Model Context Protocol (MCP). Configure your AI agent to run mcp-guide as an MCP server.

### Common JSON configuration

This JSON block can be used with most AI CLI agents to add the MCP server.
It requires uv, Python 3.13+ to be installed, and the "uvx" command to be available on the PATH.

mcp-guide supports three transport modes:

- **STDIO** - Standard input/output for local agent communication (most common)
- **HTTP** - Streamable HTTP transport for network clients
- **HTTPS** - Streamable HTTP over TLS with SSL certificates

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
- Codex: `~/.codex/config.json` (see [Codex Setup](#codex-setup) below)

### Project Detection

By default mcp-guide does not infer a project from inherited `PWD` or from the
server process working directory. HTTP, container, and desktop hosts must not treat
server `getcwd()` as the client filesystem. A CLI agent that starts a local stdio
server from the project directory may opt in with `--use-pwd` or
`MG_USE_PWD=1`, but this shortcut additionally requires already verified filesystem
sharing. It cannot replace the first absolute-root binding after server startup.
Guide still does not use MCP roots for binding.

When the interaction is not already bound, the agent must call `set_project` with the
absolute client filesystem path of the project root:

```
set_project({"path": "/path/to/your/project"})
```

`set_project` binds the initial root once. A retained interaction can then use
`switch_project({"name": "..."})` to select a different Guide configuration at
that root, or `switch_project({"path": "/absolute/client/other-project"})` to rebind its root
and select the configuration named by that path's basename. Supply exactly one of
`name` or `path`; use an absolute client path until stdio filesystem sharing is
verified. After verification, `~`, `~user`, `$VAR` and paths relative to the current
bound root are also accepted. HTTP/HTTPS always requires absolute client paths and
never probes. Docker stdio requires successful verification of the project mount
at the same absolute path; stdio alone is not sufficient. The one-shot probe times
out 60 seconds after its instruction is attached to an outgoing response, excluding
time waiting in the queue. See [Client filesystem
verification](protocol-and-sessions.md#client-filesystem-verification).

Once the project is set, all of mcp-guide's project-related functionality — categories, collections, feature flags, workflows — becomes available. Without it, tools will return an error asking the agent to set a project first. See [Protocol and Sessions](protocol-and-sessions.md) for the state rules used by modern and retained clients.

If you're using an agent that doesn't automatically detect the project, you can include a brief instruction in your agent's system prompt or project configuration to call `set_project` at the start of each session.

### Codex Setup

[Codex](https://github.com/openai/codex) communicates with MCP servers over STDIO. If the server is not started from the project directory, the agent needs to call `set_project` with the working directory path to get started.

Add to `~/.codex/config.json`:

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

Once connected, the agent should call `set_project` with the absolute client project path. The optional stdio `PWD` shortcut requires both `MG_USE_PWD` and already verified filesystem sharing. After binding, `guide://` URIs become the primary way to access content and commands — see [Guide URIs](guide-uris.md) for details.

### Streamable HTTP

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

Network transport with Streamable HTTP for remote access.
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
For remote access, use direct HTTPS or HTTP behind a TLS-terminating reverse
proxy. HTTPS encrypts traffic; it does not authenticate callers.

Bare `http` and `https`, and transport URLs without a host, bind to `localhost`.
To listen on another interface, supply its address explicitly in the transport
URL. For example, `https://0.0.0.0:8443` listens on all IPv4 interfaces and
requires the usual certificate options. No separate bind flag is needed.

#### IPv4 and IPv6 binding

| Bind host | Listening addresses |
| --- | --- |
| Omitted, or `localhost` | Loopback addresses returned by local hostname resolution, normally IPv4 and IPv6 |
| `0.0.0.0` | All IPv4 interfaces only |
| `[::]` | All IPv4 and IPv6 interfaces through one dual-stack listener |
| `[::1]` | IPv6 loopback only |
| A hostname | Its locally resolved bind addresses; not an all-interface wildcard |

Request dual-stack access explicitly, quoting bracketed URLs in shell commands:

```bash
mcp-guide 'http://[::]:8080'
mcp-guide 'https://[::]:8443' --ssl-certfile cert.pem --ssl-keyfile key.pem
```

The MCP endpoint remains `/mcp` (or the configured path prefix). HTTPS uses the
same certificate settings for both families. Dual-stack support must be available
on the host; an unsupported or unsuccessful bind fails startup instead of
falling back to IPv6-only or IPv4-only listening.

**Breaking exposure change:** `[::]` now accepts IPv4 as well as IPv6. Existing
deployments relying on IPv6-only wildcard exposure must review their bind and
network controls before upgrading. Use a specific IPv6 address for an
address-specific listener. Localhost and explicit IPv4 defaults are unchanged.

#### Optional remote authentication

Remote HTTP(S) deployments can protect selected operations with an installed
provider:

```text
mcp-guide https --auth-provider <provider-name> ...
```

`<provider-name>` is an entry point supplied by the provider package. Guide does
not implement login, issue tokens, or interpret credentials. The provider
receives request evidence and returns `UserAuthorisation` with opaque access
scopes. Guide uses `user` for ordinary protected operations and `admin` for
administrative operations. An unauthenticated result may include an opaque HTTPS
handoff that a capable client can complete before retrying.
Guide represents missing or invalid authentication with `not_authorised` (HTTP
401 semantics), and insufficient authenticated access with `forbidden` (HTTP
403 semantics). These are Result codes within MCP responses, not HTTP transport
status codes or authentication challenges. These authentication failure results
do not expose tokens, principals, claims, or credential data.
Authentication identifies access to operations, not a tenant or project owner:
remote project paths and checksums are not tenancy controls.

Authentication is available for either HTTP or HTTPS when a provider is
selected. The transport does not prescribe TLS or reverse-proxy policy: that is
the deployment administrator's responsibility. Direct HTTPS, or HTTP behind a
TLS-terminating reverse proxy, are the recommended remote deployments. Stdio
does not support `--auth-provider`; Guide rejects that configuration.

Without a provider, operations remain available without authentication,
including tools that mutate project configuration, flags, permission settings
and documents. Before exposing Guide to untrusted callers, configure a provider
or restrict access through network or reverse-proxy controls. TLS alone is not
an access-control boundary.


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
    command: ["http://0.0.0.0:8080"]
    environment:
      - MG_LOG_LEVEL=${MG_LOG_LEVEL:-info}
      - MG_LOG_JSON=${MG_LOG_JSON:-1}

  mcp-guide-https:
    image: dlnugent/mcp-guide:latest
    profiles: [https]
    ports:
      - "443:8443"
    volumes:
      - ./cert.pem:/home/mcp/certs/cert.pem:ro
      - ./key.pem:/home/mcp/certs/key.pem:ro
    command: ["https://0.0.0.0:8443", "--ssl-certfile", "/home/mcp/certs/cert.pem", "--ssl-keyfile", "/home/mcp/certs/key.pem"]
    environment:
      - MG_LOG_LEVEL=${MG_LOG_LEVEL:-info}
      - MG_LOG_JSON=${MG_LOG_JSON:-1}
```

**Note:** STDIO mode cannot be used in a compose configuration because it requires the MCP client to start the MCP server to attach stdin/stdout used for message exchange. In HTTP/HTTPS mode, the MCP server runs independently from the AI client and communicates over the network using the HTTP protocol.

The examples bind IPv4 inside the container. To request both address families,
use `command: ["http://[::]:8080"]` (or the HTTPS equivalent with certificate
options). This controls Guide's listener, not Docker's host-side port publishing:
IPv6 availability also depends on the host and Docker network configuration.

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
  dlnugent/mcp-guide:latest stdio
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
  -v "$(pwd)/cert.pem:/home/mcp/certs/cert.pem:ro" \
  -v "$(pwd)/key.pem:/home/mcp/certs/key.pem:ro" \
  -p 443:8443 \
  dlnugent/mcp-guide:latest \
  https://0.0.0.0:8443 --ssl-certfile /home/mcp/certs/cert.pem --ssl-keyfile /home/mcp/certs/key.pem
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

**Updating from within your agent:**

You can also update documentation directly through your AI agent using the `update_documents` tool. Just ask:

```
Please update the documentation
```

The agent will run the `update_documents` tool, which performs the same smart update as `mcp-install update`. To enable automatic update prompting when new versions are available, set the `autoupdate` feature flag globally.

**See:** [Feature Flags](feature-flags.md) for details on the `autoupdate` flag.

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

### Server capacity limits

The following optional settings belong at the top level of the server's
`config.yaml`. They are global, server-owned values: clients and projects cannot
change them, and a configuration edit takes effect only after restart.

```yaml
# Defaults shown; omit either setting to use its default.
max-content-limit: 500mb
max-document-limit: 100

# HTTP/HTTPS only, measured across a rolling 15-second window.
http-session-rate-limit: 5
http-service-rate-limit: 100
```

`max-content-limit` accepts positive decimal byte values such as `500mb`,
`2GB`, or `1000kb`. It bounds source documents, templates and partials, rendered
content, and the final document response. `max-document-limit` bounds the number
of documents selected by one request. Omitted values are not written back into
the configuration file.

The HTTP limits are requests per second, with capacities of 75 requests per
established MCP session and 1,500 per server process at the defaults. A session
that is at capacity receives HTTP 429; a process at capacity receives HTTP 503.
Both include `Retry-After`, which falls naturally as admitted requests leave the
window. Stdio does not use HTTP request-rate limiting.

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
