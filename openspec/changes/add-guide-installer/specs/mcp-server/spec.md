# MCP Server Specification

## MODIFIED Requirements

### Requirement: First-Run Installation Check
The system SHALL check for configuration file on startup and trigger installation if missing.

#### Scenario: Configuration exists
- **WHEN** server starts and config file exists
- **THEN** server proceeds with normal startup
- **AND** no installation is triggered

#### Scenario: Configuration missing
- **WHEN** server starts and config file doesn't exist
- **THEN** automatic installation is triggered
- **AND** server stops after installation completes
- **AND** user is instructed to restart server

### Requirement: Manual Update Support
The system SHALL provide manual installer script for updating templates.

#### Scenario: Manual update via script
- **WHEN** user runs `mcp-install` command
- **THEN** installer runs in non-interactive mode by default
- **AND** existing files are updated using smart strategy
- **AND** identical files are skipped

### Requirement: Server Configuration Options
The system SHALL support command-line options for docroot and config directory.

#### Scenario: Override docroot on server startup
- **WHEN** server starts with -d or --docroot option
- **THEN** server uses specified docroot
- **AND** config file is updated if docroot differs

#### Scenario: Override config directory on server startup
- **WHEN** server starts with -c or --configdir option
- **THEN** server loads config from specified directory
- **AND** creates config there if it doesn't exist
