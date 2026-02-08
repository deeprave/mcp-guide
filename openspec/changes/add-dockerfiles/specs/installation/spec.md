## ADDED Requirements

### Requirement: Docker Multi-Stage Build
The system SHALL provide a base Dockerfile with multi-stage build for all transports.

#### Scenario: Build base image
- **WHEN** base Dockerfile is built
- **THEN** image uses Python 3.14-slim as base
- **AND** build stage installs uv and builds wheel
- **AND** final stage contains only runtime dependencies
- **AND** final image size is minimized (~200MB)

### Requirement: Docker STDIO Support
The system SHALL provide a Dockerfile for running mcp-guide with STDIO transport in a container.

#### Scenario: Build STDIO container
- **WHEN** Dockerfile.stdio is built
- **THEN** container uses base final stage
- **AND** container includes STDIO entrypoint script
- **AND** logging is configurable via environment variables

#### Scenario: Run STDIO container
- **WHEN** STDIO container is started
- **THEN** mcp-guide runs with STDIO transport
- **AND** stdin/stdout are properly connected
- **AND** LOG_LEVEL and LOG_JSON environment variables control logging

### Requirement: Docker HTTP Support
The system SHALL provide a Dockerfile for running mcp-guide with HTTP transport in a container.

#### Scenario: Build HTTP container
- **WHEN** Dockerfile.http is built
- **THEN** container uses base final stage
- **AND** container includes HTTP entrypoint script without SSL dependencies
- **AND** port 8080 is exposed

#### Scenario: Run HTTP container
- **WHEN** HTTP container is started
- **THEN** mcp-guide runs with HTTP transport on port 8080
- **AND** server stays running until stopped
- **AND** logging is configurable via environment variables

### Requirement: Docker HTTPS Support
The system SHALL provide a Dockerfile for running mcp-guide with HTTPS transport in a container.

#### Scenario: Build HTTPS container
- **WHEN** Dockerfile.https is built
- **THEN** container uses base final stage
- **AND** container includes certbot for certificate management
- **AND** container includes HTTPS entrypoint script
- **AND** ports 443 and 8080 are exposed

#### Scenario: Run HTTPS container with certificates
- **WHEN** HTTPS container is started with mounted certificates
- **THEN** mcp-guide runs with HTTPS transport
- **AND** SSL certificates are loaded from /certs directory
- **AND** server accepts HTTPS connections
- **AND** logging is configurable via environment variables

#### Scenario: Custom port mapping
- **WHEN** HTTPS container is started with custom port mapping
- **THEN** container port can be mapped to host port
- **AND** mcp-guide accepts connections on mapped port

### Requirement: Structured Logging Integration
The system SHALL integrate uvicorn logging with mcp-guide's structured logging system.

#### Scenario: Configure uvicorn logging
- **WHEN** HTTP or HTTPS transport starts
- **THEN** uvicorn uses mcp-guide's log formatters
- **AND** uvicorn respects CLI log level setting
- **AND** uvicorn logs use same format as mcp-guide logs

#### Scenario: JSON logging
- **WHEN** LOG_JSON environment variable is true
- **THEN** all logs use JSON format
- **AND** uvicorn access logs use StructuredJSONFormatter
- **AND** log format is consistent across all components

#### Scenario: Invalid log level
- **WHEN** invalid log level is provided
- **THEN** system raises ValueError with clear message
- **AND** lists valid log levels

### Requirement: Configurable Logging via Environment
The system SHALL support logging configuration via environment variables.

#### Scenario: Set log level
- **WHEN** LOG_LEVEL environment variable is set
- **THEN** mcp-guide uses specified log level
- **AND** uvicorn uses same log level

#### Scenario: Enable JSON logging
- **WHEN** LOG_JSON environment variable is true
- **THEN** all logs output in JSON format
- **AND** logs include structured metadata

### Requirement: Secure Entrypoint Scripts
The system SHALL use secure command construction in entrypoint scripts.

#### Scenario: Build command safely
- **WHEN** entrypoint script constructs command
- **THEN** script uses array-based command construction
- **AND** script properly quotes all variables
- **AND** script prevents command injection

### Requirement: SSL Certificate Management
The system SHALL support flexible SSL certificate management.

#### Scenario: Mount certificates at runtime
- **WHEN** certificates are mounted via Docker volumes
- **THEN** container loads certificates from /certs directory
- **AND** certificates can be rotated without rebuilding

#### Scenario: Generate self-signed certificates
- **WHEN** generate-certs.sh is run with --self flag
- **THEN** script generates certificates using mkcert
- **AND** certificates are created in docker directory

### Requirement: Docker Compose Profiles
The system SHALL provide docker-compose.yaml with profiles for each transport mode.

#### Scenario: Run STDIO profile
- **WHEN** docker compose --profile stdio up is run
- **THEN** STDIO service starts
- **AND** HTTP and HTTPS services do not start

#### Scenario: Run HTTP profile
- **WHEN** docker compose --profile http up is run
- **THEN** HTTP service starts on port 8080
- **AND** STDIO and HTTPS services do not start

#### Scenario: Run HTTPS profile
- **WHEN** docker compose --profile https up is run
- **THEN** HTTPS service starts with mounted certificates
- **AND** STDIO and HTTP services do not start

### Requirement: Docker Build Optimization
The system SHALL provide .dockerignore to optimize Docker builds.

#### Scenario: Exclude unnecessary files
- **WHEN** Docker build runs
- **THEN** test files are excluded from build context
- **AND** documentation is excluded from build context
- **AND** development files are excluded from build context
- **AND** certificates are excluded from build context
- **AND** build is faster with smaller context

### Requirement: Comprehensive Documentation
The system SHALL provide comprehensive Docker documentation.

#### Scenario: Docker README
- **WHEN** user reads docker/README.md
- **THEN** documentation covers multi-stage build architecture
- **AND** documentation explains SSL certificate management
- **AND** documentation describes environment variables
- **AND** documentation includes troubleshooting guide

#### Scenario: Main README Docker section
- **WHEN** user reads main README.md
- **THEN** Docker section provides quick start examples
- **AND** section links to detailed docker/README.md
