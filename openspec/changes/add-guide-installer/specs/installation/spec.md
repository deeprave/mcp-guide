# Installation Specification

## ADDED Requirements

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
