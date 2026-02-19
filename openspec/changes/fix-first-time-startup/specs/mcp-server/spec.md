## MODIFIED Requirements

### Requirement: First-Run Installation Check
The system SHALL check for configuration file on startup and trigger installation if missing.

#### Scenario: Configuration exists
- **WHEN** server starts and config file exists
- **THEN** server proceeds with normal startup
- **AND** no installation is triggered

#### Scenario: Configuration missing - successful initialization
- **WHEN** first tool is called and config file doesn't exist
- **THEN** lock_update detects missing parent directory
- **AND** creates parent directory
- **AND** creates lock file successfully
- **AND** automatic installation is triggered via get_or_create_config
- **AND** config directory is created
- **AND** initial config.yaml is created with no projects
- **AND** all templates from mcp_guide/templates are installed to docroot
- **AND** tool execution continues normally

#### Scenario: Configuration missing - parent creation fails
- **WHEN** lock_update cannot create parent directory
- **THEN** error is logged with full stack trace using logger.exception
- **AND** ConfigDirectoryError is raised
- **AND** exception propagates to main entry point
- **AND** main catches exception and exits with code 2
- **AND** no further processing occurs

#### Scenario: Configuration missing - lock creation fails after parent created
- **WHEN** lock_update creates parent but still cannot create lock file
- **THEN** error is logged with full stack trace using logger.exception
- **AND** ConfigDirectoryError is raised
- **AND** exception propagates to main entry point
- **AND** main catches exception and exits with code 2
- **AND** no further processing occurs
