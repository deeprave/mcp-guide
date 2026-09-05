# guide-project-tools

## Purpose

Define project selection and project-management tool contracts.

## Requirements

### Requirement: Switch Current Project
The system SHALL provide a tool to switch to a different project by name or full path.

#### Scenario: Switch to existing project
- **WHEN** user calls `set_current_project` with an existing project name
- **THEN** load that project's configuration and set it as current

#### Scenario: Create new project
- **WHEN** user calls `set_current_project` with a non-existent project name
- **THEN** create new project with default categories and set it as current

#### Scenario: Invalid project name
- **WHEN** user calls `set_current_project` with invalid characters or empty name
- **THEN** return error with type `invalid_name`

#### Scenario: Full path provided
- **WHEN** user calls `set_current_project` with an absolute filesystem path
- **THEN** the basename of the path SHALL be used as the project name
- **AND** the session roots SHALL be updated with the provided path
- **AND** `resolve_project_path()` SHALL return the provided directory

#### Scenario: File URI provided
- **WHEN** user calls `set_current_project` with a `file://` URI
- **THEN** the URI prefix SHALL be stripped and treated as an absolute path

#### Scenario: Relative path rejected
- **WHEN** user calls `set_current_project` with a relative path containing separators
- **THEN** return error with type `invalid_name`
- **AND** the error message SHALL indicate an absolute path is required

#### Scenario: Path traversal rejected
- **WHEN** user calls `set_current_project` with a path containing `..` components
- **THEN** return error with type `invalid_name`
- **AND** the error message SHALL indicate traversals are not permitted

### Requirement: Result Pattern Compliance
All project management tools SHALL return responses using the Result pattern.

#### Scenario: Unbound project error
- **WHEN** any tool requires a bound project and the session is unbound
- **THEN** return a consistent static `RESULT_NO_PROJECT` error
- **AND** the error SHALL include an instruction telling the agent to call `set_project` with the project path or name

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
