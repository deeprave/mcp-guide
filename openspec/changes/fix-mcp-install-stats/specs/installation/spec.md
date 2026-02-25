## MODIFIED Requirements

### Requirement: Template Package Installation
The system SHALL copy templates from mcp_guide_templates package to docroot, tracking and reporting actual operations performed.

#### Scenario: Install from package with accurate reporting
- **WHEN** installation runs
- **THEN** templates directory from mcp_guide_templates package is located
- **AND** each file is checked against destination
- **AND** new files are installed
- **AND** changed files are updated
- **AND** unchanged files are skipped
- **AND** statistics report counts of installed, updated, and unchanged files

#### Scenario: Skip unchanged files
- **WHEN** destination file exists and matches source content
- **THEN** file copy is skipped
- **AND** file is counted as "unchanged"
- **AND** no disk I/O occurs for that file

### Requirement: Command-Line Options
The system SHALL support command-line options for docroot, config directory, and output verbosity.

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

#### Scenario: Quiet mode suppresses output
- **WHEN** -q or --quiet flag is provided
- **THEN** installation statistics are not displayed
- **AND** success/progress messages are not displayed
- **AND** error and warning messages are still displayed
- **AND** installation proceeds normally

## ADDED Requirements

### Requirement: Installation Statistics Tracking
The system SHALL track and report accurate statistics about file operations during installation.

#### Scenario: Track file operations
- **WHEN** templates are installed or updated
- **THEN** system counts files that are newly installed
- **AND** system counts files that are updated (changed)
- **AND** system counts files that are unchanged (skipped)
- **AND** binary files are excluded from all counts

#### Scenario: Report statistics in default mode
- **WHEN** installation completes without --quiet flag
- **THEN** system displays "X files installed, Y files updated, Z files unchanged"
- **AND** counts reflect actual operations performed
- **AND** message is displayed after installation completes

#### Scenario: Suppress statistics in quiet mode
- **WHEN** installation completes with --quiet flag
- **THEN** statistics are not displayed
- **AND** only errors and warnings are shown
