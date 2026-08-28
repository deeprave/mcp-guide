## ADDED Requirements

### Requirement: Machine-wide OpenSpec state
The configuration system SHALL persist OpenSpec CLI state as a top-level
`openspec` mapping, independent of individual projects.

The mapping SHALL contain `validated` as a boolean, `version` as a string or
null, and `checked` as a UTC Unix timestamp float or null.

#### Scenario: Default OpenSpec state
- **WHEN** configuration without an `openspec` mapping is loaded
- **THEN** the system SHALL expose OpenSpec state with `validated` set to false
- **AND** `version` and `checked` set to null

#### Scenario: Persist global OpenSpec state
- **WHEN** OpenSpec validation or version-check state changes
- **THEN** the updated `openspec` mapping SHALL be written at the global
  configuration level
- **AND** it SHALL NOT be written within a project entry

### Requirement: Legacy per-project OpenSpec state migration
The configuration system SHALL migrate deprecated `openspec_validated` and
`openspec_version` project fields into the global OpenSpec state without using
ambiguous legacy version data as authoritative.

#### Scenario: Migrate an unambiguous legacy version
- **WHEN** legacy project entries contain exactly one distinct non-null
  `openspec_version`
- **THEN** that value SHALL initialise global `openspec.version`
- **AND** global `openspec.checked` SHALL be null so the installed version is
  checked on the next eligible task run

#### Scenario: Migrate conflicting legacy versions
- **WHEN** legacy project entries contain more than one distinct non-null
  `openspec_version`
- **THEN** global `openspec.version` SHALL be null
- **AND** global `openspec.checked` SHALL be null
- **AND** a later version check SHALL establish the authoritative value

#### Scenario: Remove deprecated per-project fields
- **WHEN** configuration containing legacy per-project OpenSpec fields is saved
- **THEN** the saved project entries SHALL omit `openspec_validated` and
  `openspec_version`
