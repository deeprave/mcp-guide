# Docker Support for mcp-guide

This directory contains Docker configurations for running mcp-guide in containers with STDIO, HTTP and HTTPS transports.

## Architecture

### Multi-Stage Build

The base `Dockerfile` uses a three-stage build:

1. **base**: Python 3.14-alpine with OpenSSL and CA certificates
2. **build**: Installs uv, syncs dependencies, builds wheel
3. **final**: Minimal runtime (~200MB) with only necessary files

The published image uses `mcp-guide` as its entrypoint. Container commands are
CLI arguments, such as `stdio` or `http://0.0.0.0:8080`. With no arguments it
prints CLI help. Optional local transport images supply their transport default
and forward CLI options or an explicit transport URL.

### Transport-Specific Dockerfiles

- **Dockerfile.stdio**: STDIO transport for MCP clients
- **Dockerfile.http**: HTTP transport without SSL
- **Dockerfile.https**: HTTPS transport with SSL support

## Quick Start

### STDIO Mode

```bash
# Run the published image (from this directory)
docker compose --profile stdio up
```

### HTTP Mode (no SSL)

```bash
# Run the published HTTP service
docker compose --profile http up
```

Access at: http://localhost:8080/mcp

### HTTPS Mode

```bash
# Generate self-signed certificates
./generate-certs.sh --self

# Run the published HTTPS service
docker compose --profile https up
```

Access at: https://localhost/mcp

## SSL Certificate Management

### Self-Signed Certificates (Development)

Use mkcert for local development:

```bash
# Install mkcert (macOS)
brew install mkcert

# Generate certificates
cd docker
./generate-certs.sh --self
```

This creates:
- `cert.pem` - Certificate
- `key.pem` - Private key

### Let's Encrypt (Production)

For production deployments, obtain certificates on the host and mount them:

```bash
# Obtain certificates on host using certbot
sudo certbot certonly --standalone -d your-domain.com

# Update compose.yaml to mount Let's Encrypt certs
volumes:
  - /etc/letsencrypt/live/your-domain.com/fullchain.pem:/home/mcp/certs/cert.pem:ro
  - /etc/letsencrypt/live/your-domain.com/privkey.pem:/home/mcp/certs/key.pem:ro
```

Certificates are managed on the host and mounted read-only into the container.

### Certificate Locations

Certificates should be mounted from the host filesystem (recommended):

```yaml
volumes:
  - ./cert.pem:/home/mcp/certs/cert.pem:ro
  - ./key.pem:/home/mcp/certs/key.pem:ro
```

This approach allows certificate rotation without rebuilding the container.

## Logging

Logging is configurable via environment variables:

- `MG_LOG_LEVEL`: Set log level (trace, debug, info, warning, error). Default: `info`
- `MG_LOG_JSON`: Enable JSON logging (1/0 or true/false). Compose default: `1`
- `PYTHON_VERSION`: Python version for Docker builds. Default: `3.14`

**Text logging**:
```bash
MG_LOG_JSON=0 docker compose --profile stdio up
```

**JSON logging** (for log aggregation):
```bash
MG_LOG_JSON=1 docker compose --profile stdio up
```

**Custom log level**:
```bash
MG_LOG_LEVEL=debug MG_LOG_JSON=1 docker compose --profile https up
```

JSON log format:
```json
{
  "timestamp": "2026-02-08T14:16:26.386+11:00",
  "level": "INFO",
  "logger": "mcp_guide.server",
  "message": "Server started"
}
```

This includes:
- FastMCP logs
- mcp-guide application logs
- uvicorn access logs (HTTP/HTTPS mode)

## Docker Compose Profiles

Use profiles to select which service to run:

```bash
# STDIO mode
docker compose --profile stdio up

# HTTP mode (no SSL)
docker compose --profile http up

# HTTPS mode (with SSL)
docker compose --profile https up
```

## Environment Variables

### All Transports

- `MG_LOG_LEVEL`: Log level (trace, debug, info, warning, error). Default: `info`
- `MG_LOG_JSON`: Enable JSON logging (1/0 or true/false). CLI default: `false`; Compose default: `1`

### HTTPS Transport

- `MG_SSL_CERTFILE`: Path to SSL certificate. The HTTPS transport image discovers `/home/mcp/certs/cert.pem` when mounted.
- `MG_SSL_KEYFILE`: Path to SSL private key. The HTTPS transport image discovers `/home/mcp/certs/key.pem` when mounted.

Explicit CLI options override environment settings. Bind addresses and ports
are supplied in transport URLs, such as `https://0.0.0.0:8443`.
Bare HTTP and HTTPS modes default to localhost. The transport images and Compose
examples explicitly bind to all interfaces inside the container so published
ports can reach them. Restrict published ports or configure authentication
before making those endpoints accessible to untrusted callers; HTTPS alone
does not authenticate clients.

## Building Images

### Build all images

From the repository root:

```bash
# Build the image used by the publishing workflow
docker build -t mcp-guide:base -f docker/Dockerfile .

# Build STDIO image
docker build -t mcp-guide:stdio -f docker/Dockerfile.stdio docker

# Build HTTP image
docker build -t mcp-guide:http -f docker/Dockerfile.http docker

# Build HTTPS image
docker build -t mcp-guide:https -f docker/Dockerfile.https docker
```

### Using Docker Compose

```bash
# Compose runs the published image; it does not build transport images
docker compose --profile http up
docker compose --profile https up
```

## Security Considerations

1. **Never commit certificates**: `.gitignore` excludes `*.pem`, `*.key`, `*.crt`
2. **Use read-only mounts**: Mount certificates with `:ro` flag
3. **Rotate certificates**: Regularly update SSL certificates
4. **Use Let's Encrypt**: For production, use proper CA-signed certificates

## Troubleshooting

### Build Issues

**Build fails with "LICENSE.md not found"**

Ensure you're building from the project root:
```bash
ls LICENSE.md  # Should exist
docker build -t mcp-guide:base -f docker/Dockerfile .
```

**Build fails during dependency download**

Check network connectivity and try with --no-cache:
```bash
docker build --no-cache -t mcp-guide:base -f docker/Dockerfile .
```

**Platform-specific issues**

Explicitly specify platform for cross-platform builds:
```bash
docker build --platform linux/amd64 -t mcp-guide:base -f docker/Dockerfile .
```

### Runtime Issues

**Certificate errors**

```bash
# Verify certificates exist
ls -la docker/*.pem

# Check certificate validity
openssl x509 -in docker/cert.pem -text -noout
```

**Container logs**

```bash
# View logs
docker compose --profile https logs -f

# Check structured logging (requires jq)
docker compose --profile https logs | jq
```

**Port conflicts**

If port 443 or 8080 is already in use:

```yaml
# Edit compose.yaml
ports:
  - "8443:8443"  # Use different host port
```
