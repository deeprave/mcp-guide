## ADDED Requirements

### Requirement: Global OpenSpec state context
The template context system SHALL obtain OpenSpec CLI validation and version
state from the global `openspec-state` feature flag rather than the active
project entry.
Whether OpenSpec context is available for an active Project SHALL remain
controlled by that Project's `project_flags.openspec` setting.

#### Scenario: OpenSpec is disabled for the active project
- **WHEN** global OpenSpec CLI state is available but the active Project does not enable OpenSpec
- **THEN** the template context SHALL treat OpenSpec as disabled for that Project

#### Scenario: Render global OpenSpec state
- **WHEN** a template renders OpenSpec validation or CLI version information
- **THEN** it SHALL use the global `openspec-state.validated` and
  `openspec-state.version` values

#### Scenario: Project switch retains OpenSpec CLI state
- **WHEN** the active project changes on the same computer
- **THEN** OpenSpec CLI validation and version context SHALL remain derived from
  the same global state
- **AND** the project switch SHALL NOT trigger a version check solely because
  the project changed
