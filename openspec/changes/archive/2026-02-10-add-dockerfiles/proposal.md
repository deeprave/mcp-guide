# Change: Add Docker support with multi-stage builds and structured logging

## Why
Enable containerized deployment of mcp-guide for local development (STDIO), testing (HTTP), and production environments (HTTPS), providing consistent runtime environments, simplified deployment, and unified structured logging across all components.

## What Changes

### Docker Infrastructure
- Add base Dockerfile with multi-stage build (base → build → final)
- Add Dockerfile.stdio for STDIO transport
- Add Dockerfile.http for HTTP transport (no SSL)
- Add Dockerfile.https for HTTPS transport with SSL support
- Add entrypoint scripts with configurable logging via environment variables
- Add docker-compose.yaml with profiles (stdio, http, https)
- Add SSL certificate generation script (mkcert support)
- Add .dockerignore for efficient builds

### Logging Integration
- Integrate uvicorn logging with mcp-guide's structured logging system
- Pass log_level and log_json from CLI through to uvicorn configuration
- Add input validation for log levels
- Make logging configurable via environment variables (LOG_LEVEL, LOG_JSON)

### Security
- Use secure shell command construction in entrypoint scripts
- Remove unsafe certificate copying patterns
- Mount certificates at runtime via volumes (recommended approach)

### Documentation
- Create comprehensive docker/README.md covering:
  - Multi-stage build architecture
  - SSL certificate management (self-signed and Let's Encrypt)
  - Environment variable configuration
  - Build and runtime troubleshooting
- Update main README.md with Docker quick start section

### Bug Fixes
- Fix HTTP server exiting immediately after start (await server_task)

## Impact
- Affected specs: installation, deployment
- Affected code:
  - `src/mcp_guide/core/mcp_log.py` - Added uvicorn log config function
  - `src/mcp_guide/main.py` - Added server_task await for HTTP transport
  - `src/mcp_guide/transports/__init__.py` - Pass log config parameters
  - `src/mcp_guide/transports/http.py` - Integrate uvicorn logging
- Users can run mcp-guide in containers without local Python setup
- Simplified deployment to container orchestration platforms
- Consistent structured logging across all components (FastMCP, mcp-guide, uvicorn)
- Flexible SSL certificate management for production deployments
