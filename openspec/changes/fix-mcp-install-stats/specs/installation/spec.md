## MODIFIED Requirements

### Requirement: Smart Update Strategy
The system SHALL use intelligent update strategy based on file modification status.

#### Scenario: File unchanged from original and differs from new version
- **WHEN** current file matches original in `_installed.zip`
- **AND** current file differs from new version
- **THEN** file is updated to new version without backup
- **AND** no user changes are lost

#### Scenario: File unchanged from original and identical to new version
- **WHEN** current file matches original in `_installed.zip`
- **AND** current file matches new version (SHA256)
- **THEN** file is skipped
- **AND** no update occurs

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

## ADDED Requirements

### Requirement: Installation Logging
The system SHALL use structured logging for installation operations with configurable verbosity.

#### Scenario: Verbose logging
- **WHEN** `--verbose` flag is provided
- **THEN** log level is set to DEBUG
- **AND** per-file operations are logged
- **AND** summary statistics are logged

#### Scenario: Normal logging
- **WHEN** no verbosity flags are provided
- **THEN** log level is set to INFO
- **AND** summary statistics are logged
- **AND** conflict warnings are logged

#### Scenario: Quiet logging
- **WHEN** `--quiet` flag is provided
- **THEN** log level is set to WARNING
- **AND** only conflict warnings are logged
- **AND** summary statistics are suppressed

#### Scenario: Per-file operation logging
- **WHEN** file operations occur
- **THEN** each operation is logged at DEBUG level
- **AND** message includes file path and operation type

#### Scenario: Summary statistics logging
- **WHEN** installation or update completes
- **THEN** summary statistics are logged at INFO level
- **AND** statistics include counts for installed, updated, patched, unchanged files

#### Scenario: Conflict warning logging
- **WHEN** patch fails and backup is created
- **THEN** individual conflict is logged at WARNING level with file path and backup location
- **AND** summary conflict warning is logged at WARNING level after all operations
