## ADDED Requirements

### Requirement: Docker STDIO Support
The system SHALL provide a Dockerfile for running mcp-guide with STDIO transport in a container.

#### Scenario: Build STDIO container
- **WHEN** Dockerfile.stdio is built
- **THEN** container includes Python runtime and mcp-guide
- **AND** container is configured for STDIO transport
- **AND** build uses multi-stage for minimal image size

#### Scenario: Run STDIO container
- **WHEN** STDIO container is started
- **THEN** mcp-guide runs with STDIO transport
- **AND** stdin/stdout are properly connected
- **AND** container can communicate with host processes

### Requirement: Docker HTTPS Support
The system SHALL provide a Dockerfile for running mcp-guide with HTTPS transport in a container.

#### Scenario: Build HTTPS container
- **WHEN** Dockerfile.https is built
- **THEN** container includes Python runtime, mcp-guide, and uvicorn
- **AND** container is configured for HTTPS transport
- **AND** build uses multi-stage for minimal image size

#### Scenario: Run HTTPS container
- **WHEN** HTTPS container is started
- **THEN** mcp-guide runs with HTTPS transport on port 443
- **AND** port 443 is exposed
- **AND** container binds to 0.0.0.0 for external access

#### Scenario: Custom port mapping
- **WHEN** HTTPS container is started with custom port mapping
- **THEN** container port can be mapped to host port
- **AND** mcp-guide accepts connections on mapped port

### Requirement: Docker Build Optimization
The system SHALL provide .dockerignore to optimize Docker builds.

#### Scenario: Exclude unnecessary files
- **WHEN** Docker build runs
- **THEN** test files are excluded from build context
- **AND** documentation is excluded from build context
- **AND** development files are excluded from build context
- **AND** build is faster with smaller context
