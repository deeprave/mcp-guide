## ADDED Requirements

### Requirement: Clone transferable project configuration
The `clone_project` tool SHALL copy all transferable configuration from the
specified source project into the currently bound destination project, while
retaining the destination project's identity (`name`, `key`, and `hash`).

#### Scenario: Clone retains project flags and settings
- **WHEN** the source project has project flags, allowed write paths,
  additional read paths, or exports
- **THEN** the destination project SHALL receive those settings
- **AND** the destination project's identity fields SHALL remain unchanged

#### Scenario: Clone retains per-project OpenSpec enablement
- **WHEN** the source project enables or disables OpenSpec through `project_flags.openspec`
- **THEN** the destination project SHALL receive the source's OpenSpec enablement value
- **AND** global OpenSpec CLI state SHALL NOT determine the destination's enablement

#### Scenario: Merge clone combines mapping configuration
- **WHEN** `clone_project` is called with `merge=true`
- **THEN** categories, collections, project flags, and exports from the source
  SHALL be merged into the destination
- **AND** a source value SHALL replace a destination value with the same key
- **AND** source allowed write paths and additional read paths SHALL replace the
  corresponding destination path lists

#### Scenario: Replacement clone copies the complete transferable configuration
- **WHEN** `clone_project` is called with `merge=false`
- **THEN** the destination project's categories, collections, project flags,
  allowed write paths, additional read paths, and exports SHALL be replaced by
  the source values
- **AND** the destination project's identity fields SHALL remain unchanged
