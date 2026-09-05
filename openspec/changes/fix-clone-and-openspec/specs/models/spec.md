## ADDED Requirements

### Requirement: Project excludes legacy OpenSpec state
The `Project` model SHALL retain only project-level OpenSpec enablement and SHALL
not model machine-wide CLI state.

#### Scenario: Project serialisation after migration
- **WHEN** a Project is serialised after the migration
- **THEN** it SHALL NOT contain `openspec_validated` or `openspec_version`
- **AND** the Project's `project_flags.openspec` value SHALL remain serialised as
  the exclusive project-level enablement setting
