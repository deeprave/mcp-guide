## ADDED Requirements

### Requirement: Global OpenSpec state model
The system SHALL model machine-wide OpenSpec state separately from `Project`.

The global state SHALL provide a boolean `validated`, an optional string
`version`, and an optional float `checked` UTC Unix timestamp.

#### Scenario: Construct default global OpenSpec state
- **WHEN** global configuration is constructed without OpenSpec values
- **THEN** `validated` SHALL default to false
- **AND** `version` and `checked` SHALL default to null

#### Scenario: Project excludes global OpenSpec state
- **WHEN** a Project is serialised after the migration
- **THEN** it SHALL NOT contain `openspec_validated` or `openspec_version`
- **AND** global OpenSpec state SHALL be serialised only in the top-level
  configuration mapping
