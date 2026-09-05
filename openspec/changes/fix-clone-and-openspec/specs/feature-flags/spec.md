## ADDED Requirements

### Requirement: Global structured OpenSpec state flag
The system SHALL store machine-wide OpenSpec CLI state in the global-only
`openspec-state` feature flag. Its mapping SHALL contain `validated` as
`"true"` or `"false"`, optional `version` as a version string, and optional
`checked` as a decimal UTC Unix timestamp string.

#### Scenario: Read absent OpenSpec state
- **WHEN** the global `openspec-state` flag is absent
- **THEN** OpenSpec consumers SHALL treat CLI validation and version as unknown
- **AND** reading it SHALL NOT persist a flag

#### Scenario: Set a completed OpenSpec check
- **WHEN** OpenSpec availability and version have been checked
- **THEN** the system SHALL replace the complete global `openspec-state` flag
  through the existing global feature-flag set API
- **AND** a valid result SHALL include `validated`, `version`, and `checked`
- **AND** an invalid result SHALL set `validated` to `"false"`, omit `version`,
  and include `checked`

### Requirement: OpenSpec feature-flag scopes
The `openspec` flag SHALL be project-only and is the exclusive OpenSpec
enablement gate. The `openspec-state` flag SHALL be global-only.

#### Scenario: Global state does not enable a project
- **WHEN** global `openspec-state` is present and a Project does not set
  `project_flags.openspec` to an enabled value
- **THEN** OpenSpec SHALL remain disabled for that Project
- **AND** flag resolution SHALL not use a global `openspec` fallback
