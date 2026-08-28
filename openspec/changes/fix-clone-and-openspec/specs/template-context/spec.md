## ADDED Requirements

### Requirement: Global OpenSpec state context
The template context system SHALL obtain OpenSpec CLI validation and version
state from global configuration rather than the active project entry.

#### Scenario: Render global OpenSpec state
- **WHEN** a template renders OpenSpec validation or CLI version information
- **THEN** it SHALL use the global `openspec.validated` and `openspec.version`
  values

#### Scenario: Project switch retains OpenSpec CLI state
- **WHEN** the active project changes on the same computer
- **THEN** OpenSpec CLI validation and version context SHALL remain derived from
  the same global state
- **AND** the project switch SHALL NOT trigger a version check solely because
  the project changed
