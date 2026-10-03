## MODIFIED Requirements

### Requirement: Docker HTTPS Support
The system SHALL provide a Dockerfile for running mcp-guide with HTTPS transport
in a container. Certificates SHALL be managed outside the container and mounted
at runtime; the HTTPS image SHALL NOT bundle certbot.

#### Scenario: Build HTTPS container
- **GIVEN** the base final stage is available
- **WHEN** Dockerfile.https is built
- **THEN** container uses base final stage
- **AND** container includes HTTPS entrypoint script without certbot
- **AND** port 8443 is exposed

#### Scenario: Run HTTPS container with certificates
- **GIVEN** certificates have been obtained outside the container
- **WHEN** HTTPS container is started with mounted certificates
- **THEN** mcp-guide runs with HTTPS transport
- **AND** SSL certificates are loaded from /home/mcp/certs directory
- **AND** server accepts HTTPS connections
- **AND** logging is configurable via environment variables

#### Scenario: Custom port mapping
- **GIVEN** the HTTPS container listens on port 8443
- **WHEN** HTTPS container is started with custom port mapping
- **THEN** container port can be mapped to host port
- **AND** mcp-guide accepts connections on mapped port

### Requirement: SSL Certificate Management
The system SHALL support flexible SSL certificate management using externally
managed certificates. Certificate acquisition, renewal, ownership and private-key
permissions SHALL remain deployment responsibilities.

#### Scenario: Mount certificates at runtime
- **GIVEN** certificate and private-key files are readable by the container user
- **WHEN** certificates are mounted read-only via Docker volumes
- **THEN** container loads certificates from /home/mcp/certs directory
- **AND** certificates can be rotated without rebuilding

#### Scenario: Generate self-signed certificates
- **GIVEN** mkcert is installed on the host
- **WHEN** generate-certs.sh is run with --self flag
- **THEN** script generates certificates using mkcert
- **AND** certificates are created in docker directory
