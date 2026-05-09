## ADDED Requirements

### Requirement: Startup Update Prompts Require Updateable Installed Docs
The system SHALL queue acknowledged documentation update prompts only for
updateable installed documentation roots.

Startup prompting SHALL first validate that the resolved documentation root is a
safe update target and that the installed documentation version file exists
before comparing versions or queuing an update instruction.

#### Scenario: Missing installed version file suppresses prompt
- **WHEN** the resolved documentation root does not contain a `.version` file
- **THEN** the system SHALL not queue an acknowledged `update_documents` prompt

#### Scenario: Unsafe docroot suppresses prompt
- **WHEN** the resolved documentation root is not safe for updates
- **THEN** the system SHALL not queue an acknowledged `update_documents` prompt

#### Scenario: Valid outdated docs still prompt
- **WHEN** the resolved documentation root is safe for updates
- **AND** the `.version` file exists
- **AND** the installed documentation version differs from the package version
- **THEN** the system SHALL queue the acknowledged `update_documents` prompt

