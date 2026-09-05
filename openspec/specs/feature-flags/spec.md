# feature-flags Specification

## Purpose
TBD - created by archiving completed changes. Update Purpose after archive.

## Requirements

### Requirement: Feature Flags Use A Dedicated Runtime Value Abstraction

The feature flag system SHALL use a dedicated runtime feature-value abstraction
instead of treating flag values purely as raw nested Python data throughout the
system.

#### Scenario: Construct feature value from supported raw shapes
- **GIVEN** a raw flag value represented as a supported scalar, list, or dict
- **WHEN** the system accepts or loads that flag value
- **THEN** it constructs a dedicated runtime feature-value object
- **AND** it rejects unsupported raw shapes

#### Scenario: Raw serialization remains compatible
- **GIVEN** a valid runtime feature-value object
- **WHEN** the system persists or exports that value
- **THEN** it serializes to the same externally supported raw flag shape
- **AND** existing user-facing configuration syntax remains valid

#### Scenario: Feature value provides display-safe rendering
- **GIVEN** a valid runtime feature-value object
- **WHEN** display-oriented code needs a user-facing representation
- **THEN** the feature-value abstraction provides a stable display form
- **AND** callers do not need to inspect raw nested structures directly

#### Scenario: Flag resolution preserves abstraction
- **GIVEN** project and global flags are available
- **WHEN** the system resolves the effective value for a flag
- **THEN** the resolved result is returned through the dedicated runtime
  feature-value abstraction
- **AND** callers do not need to reconstruct the abstraction manually

### Requirement: Global Feature Flags Are Process-Owned
Global feature-flag list, get, set, and remove operations SHALL be owned by the
process runtime, which SHALL persist them through the configuration service.
The global feature-flag handler SHALL NOT depend on a Session or on a direct
configuration-service reference.

Project feature flags remain part of the bound project's configuration and are
outside this requirement.

#### Scenario: Global flag is read or written
- **WHEN** an operation lists, gets, sets, or removes a global feature flag
- **THEN** it SHALL go through the process runtime
- **AND** the runtime SHALL persist the change in the shared configuration
- **AND** the handler SHALL NOT require a Session or a configuration-service
  object

#### Scenario: Project flag is unchanged in ownership
- **WHEN** an operation lists, gets, sets, or removes a project feature flag
- **THEN** it SHALL continue to use the bound project's configuration
- **AND** it SHALL NOT treat that flag as process-global state

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
