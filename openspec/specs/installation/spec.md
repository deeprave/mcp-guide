# installation Specification

## Purpose
TBD - created by archiving change add-guide-installer. Update Purpose after archive.
## Requirements
### Requirement: Async File Comparison
The system SHALL compare files asynchronously using SHA256 hashes to determine if updates are needed.

#### Scenario: Identical files skipped
- **WHEN** source and destination files have identical SHA256 hashes
- **THEN** file copy is skipped
- **AND** no backup is created

### Requirement: Original Installation Tracking
The system SHALL store original installed files in `_installed.zip` in docroot for update comparison.

#### Scenario: First installation
- **WHEN** templates are installed for the first time
- **THEN** all installed files are stored in `_installed.zip`
- **AND** zip file is created in docroot

#### Scenario: Update with tracking
- **WHEN** templates are updated
- **THEN** original files from `_installed.zip` are used for comparison
- **AND** new versions are stored in updated `_installed.zip`

### Requirement: Smart Update Strategy
The system SHALL use intelligent update strategy based on file modification status.

#### Scenario: File unchanged from original
- **WHEN** current file matches original in `_installed.zip`
- **THEN** file is updated to new version without backup
- **AND** no user changes are lost

#### Scenario: File modified by user
- **WHEN** current file differs from original in `_installed.zip`
- **THEN** diff is computed between original and current
- **AND** diff is applied to new version
- **AND** result is kept if patch succeeds

#### Scenario: Patch application fails
- **WHEN** diff cannot be applied to new version
- **THEN** current file is backed up to `orig.<filename>`
- **AND** new version is installed
- **AND** warning is raised about overwritten changes

#### Scenario: File identical to new version
- **WHEN** current file matches new version (SHA256)
- **THEN** file is skipped
- **AND** no backup or update occurs

### Requirement: Template Package Installation
The system SHALL copy templates from mcp_guide_templates package to docroot.

#### Scenario: Install from package
- **WHEN** installation runs
- **THEN** templates directory from mcp_guide_templates package is located
- **AND** all template files are copied to docroot
- **AND** directory structure is preserved

### Requirement: Configuration Creation
The system SHALL create configuration file with docroot path if it doesn't exist.

#### Scenario: New installation
- **WHEN** config file doesn't exist
- **THEN** config file is created with docroot path
- **AND** docroot directory is created if needed

#### Scenario: Update existing config
- **WHEN** config file exists and user provides new docroot
- **THEN** docroot path is updated in config
- **AND** existing config values are preserved

### Requirement: Interactive Installation
The system SHALL provide optional interactive prompts for installation path with default values.

#### Scenario: Accept default path interactively
- **WHEN** user runs with --interactive flag
- **AND** accepts default docroot
- **THEN** templates are installed to default location
- **AND** config is created with default path

#### Scenario: Custom path with validation
- **WHEN** user provides custom docroot path via -d/--docroot or interactively
- **THEN** path is validated for security
- **AND** installation proceeds if valid
- **AND** error is shown if invalid
- **AND** docroot is saved to config file

### Requirement: Command-Line Options
The system SHALL support command-line options for docroot and config directory.

#### Scenario: Override docroot via CLI
- **WHEN** -d or --docroot option is provided
- **THEN** templates are installed to specified docroot
- **AND** docroot path is saved to config file

#### Scenario: Override config directory via CLI
- **WHEN** -c or --configdir option is provided
- **THEN** config file is created in specified directory
- **AND** existing config values are preserved if file exists

#### Scenario: Use defaults
- **WHEN** no options are provided
- **THEN** default docroot is used
- **AND** default config directory is used
- **AND** existing config docroot is preserved if config exists

### Requirement: Non-Interactive Mode Default
The system SHALL run in non-interactive mode by default, with optional interactive prompts.

#### Scenario: Default non-interactive installation
- **WHEN** installer runs without flags
- **THEN** no prompts are shown
- **AND** default values are used
- **AND** installation proceeds automatically

#### Scenario: Interactive mode enabled
- **WHEN** -i or --interactive flag is provided
- **THEN** user is prompted for installation path
- **AND** user is prompted for confirmation
- **AND** custom paths can be provided interactively

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

