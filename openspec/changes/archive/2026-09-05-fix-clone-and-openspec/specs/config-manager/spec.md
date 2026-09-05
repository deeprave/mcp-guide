## ADDED Requirements

### Requirement: Legacy per-project OpenSpec state removal
The configuration system SHALL accept legacy `openspec_validated` and
`openspec_version` project fields when reading configuration, but SHALL NOT
migrate their values into global `openspec-state`.

#### Scenario: Read legacy project state
- **WHEN** a project entry contains legacy OpenSpec fields
- **THEN** the configuration system SHALL load the Project without using those
  values as global state
- **AND** it SHALL leave global `openspec-state` absent unless independently set

#### Scenario: Remove deprecated per-project fields
- **WHEN** configuration containing legacy per-project OpenSpec fields is saved
- **THEN** the saved project entries SHALL omit `openspec_validated` and
  `openspec_version`
- **AND** saving SHALL NOT create or modify global `openspec-state`

### Requirement: OpenSpec feature-flag change publication
The configuration manager SHALL publish changed global `openspec-state` values
and changed active-project `project_flags.openspec` values through its existing
configuration-change delivery path.

#### Scenario: Publish a global OpenSpec state change
- **WHEN** the global `openspec-state` feature flag is written
- **THEN** the configuration manager SHALL notify registered Sessions through the
  existing global feature-flag change publication path

#### Scenario: Publish a project OpenSpec enablement change
- **WHEN** an active Project's `project_flags.openspec` value is changed
- **THEN** the configuration manager SHALL notify Sessions bound to that Project
- **AND** it SHALL not notify sessions bound to unaffected Projects solely for
  that project-level change
