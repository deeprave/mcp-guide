# Change: Add Docker support for STDIO and HTTPS transports

## Why
Enable containerized deployment of mcp-guide for both local development (STDIO) and production environments (HTTPS), providing consistent runtime environments and simplified deployment.

## What Changes
- Add Dockerfile for STDIO transport (local development, testing)
- Add Dockerfile for HTTPS transport (production deployment)
- Add .dockerignore for efficient builds
- Document Docker usage in README

## Impact
- Affected specs: installation
- Affected code: None (infrastructure only)
- Users can run mcp-guide in containers without local Python setup
- Simplified deployment to container orchestration platforms
