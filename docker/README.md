# Docker Support for mcp-guide

This directory contains Docker configurations for running mcp-guide in containers with support for STDIO and HTTPS transports.

## Architecture

### Multi-Stage Build

The base `Dockerfile` uses a three-stage build:

1. **base**: Python 3.14-slim with OpenSSL and CA certificates
2. **build**: Installs uv, syncs dependencies, builds wheel
3. **final**: Minimal runtime (~200MB) with only necessary files

The final stage is shared by both STDIO and HTTPS transports.

### Transport-Specific Dockerfiles

- **Dockerfile.stdio**: STDIO transport for MCP clients
- **Dockerfile.http**: HTTP transport without SSL
- **Dockerfile.https**: HTTPS transport with SSL support

## Quick Start

### STDIO Mode

```bash
# Build base image first
docker build -t mcp-guide:base -f Dockerfile ..

# Build and run STDIO container
docker compose --profile stdio up
```

### HTTP Mode (no SSL)

```bash
# Build and run HTTP container
docker compose --profile http up
```

Access at: http://localhost:8080/mcp

### HTTPS Mode

```bash
# Generate self-signed certificates
./generate-certs.sh --self

# Build and run HTTPS container
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
  - /etc/letsencrypt/live/your-domain.com/fullchain.pem:/certs/cert.pem:ro
  - /etc/letsencrypt/live/your-domain.com/privkey.pem:/certs/key.pem:ro
```

**Note**: The HTTPS container includes certbot for convenience, but it's recommended to manage certificates on the host for better control and automation.

### Certificate Locations

Certificates should be mounted from the host filesystem (recommended):

```yaml
volumes:
  - ./cert.pem:/certs/cert.pem:ro
  - ./key.pem:/certs/key.pem:ro
```

This approach allows certificate rotation without rebuilding the container.

## Logging

Logging is configurable via environment variables:

- `LOG_LEVEL`: Set log level (trace, debug, info, warning, error, critical). Default: `info`
- `LOG_JSON`: Enable JSON logging (true/false). Default: `false`
- `PYTHON_VERSION`: Python version for Docker builds. Default: `3.14`

**Text logging** (default):
```bash
docker compose --profile stdio up
```

**JSON logging** (for log aggregation):
```bash
LOG_JSON=true docker compose --profile stdio up
```

**Custom log level**:
```bash
LOG_LEVEL=debug LOG_JSON=true docker compose --profile https up
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

- `LOG_LEVEL`: Log level (trace, debug, info, warning, error, critical). Default: `info`
- `LOG_JSON`: Enable JSON logging (true/false). Default: `false`

### HTTPS Transport

- `SSL_CERTFILE`: Path to SSL certificate (default: `/certs/cert.pem`)
- `SSL_KEYFILE`: Path to SSL private key (default: `/certs/key.pem`)

## Building Images

### Build all images

```bash
# Build base image
docker build -t mcp-guide:base -f Dockerfile ..

# Build STDIO image
docker build -t mcp-guide:stdio -f Dockerfile.stdio ..

# Build HTTPS image
docker build -t mcp-guide:https -f Dockerfile.https ..
```

### Using Docker Compose

```bash
# Build specific profile
docker compose --profile stdio build
docker compose --profile https build
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
  - "8443:443"  # Use different host port
```
