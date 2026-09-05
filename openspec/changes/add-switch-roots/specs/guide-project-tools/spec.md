## MODIFIED Requirements

### Requirement: Switch Current Project
The system SHALL provide `set_project(path)` for initial project-root binding and
`switch_project(name?, path?)` for selecting configuration projects during a
retained interaction.

The public `switch_project` tool description SHALL state that it can rebind the
project root when `path` is supplied, in addition to selecting the active
configuration project.

`set_project` SHALL continue to require an initial client root path and SHALL
reject a second root binding for the same interaction. `switch_project` SHALL
require at least one of `name` or `path`.

#### Scenario: Switch to existing project
- **WHEN** a root-bound interaction calls `switch_project` with the name of an
  existing configuration and no `path`
- **THEN** the system SHALL load that configuration and set it as current

#### Scenario: Create new project
- **WHEN** a root-bound interaction calls `switch_project` with a non-existent
  configuration name and no `path`
- **THEN** the system SHALL create that configuration with default categories
- **AND** it SHALL set the configuration as current at the bound root

#### Scenario: Invalid project name
- **WHEN** a project-selection request supplies an invalid configuration name
- **THEN** the system SHALL return an error with type `invalid_name`

#### Scenario: Full path provided
- **WHEN** an unbound interaction calls `set_project` with an absolute filesystem path
- **THEN** the basename of the path SHALL be used as the project name
- **AND** the session root SHALL be set to the provided path
- **AND** filesystem operations SHALL use that directory as the project root

#### Scenario: File URI provided
- **WHEN** an initial project-selection request supplies a `file://` URI
- **THEN** the system SHALL strip the URI prefix and treat the remainder as an
  absolute client filesystem path

#### Scenario: Relative path rejected
- **WHEN** an unbound interaction calls `set_project` with a relative path
- **THEN** it SHALL return an error with type `invalid_name`
- **AND** the error message SHALL indicate an absolute path is required

#### Scenario: Path traversal rejected
- **WHEN** an unbound interaction calls `set_project` with a path containing
  `..` components
- **THEN** it SHALL return an error with type `invalid_name`
- **AND** the error message SHALL indicate traversals are not permitted

#### Scenario: Name-only configuration selection
- **WHEN** a root-bound interaction calls `switch_project` with `name` and no
  `path`
- **THEN** the system SHALL select or create that configuration at the current
  bound root
- **AND** it SHALL retain the bound root unchanged

#### Scenario: Path-only root switch
- **WHEN** a root-bound interaction calls `switch_project` with `path` and no
  `name`
- **THEN** the system SHALL change the interaction root to the normalised path
- **AND** it SHALL select or create the configuration named by that path's basename

#### Scenario: Named configuration at a new root
- **WHEN** a root-bound interaction calls `switch_project` with both `name` and
  `path`
- **THEN** the system SHALL change the interaction root to the normalised path
- **AND** it SHALL select or create the supplied configuration name at that root

#### Scenario: Relative root switch
- **WHEN** a root-bound interaction supplies a relative `path`, including one
  containing `.` or `..` components
- **THEN** the system SHALL normalise it relative to the interaction's current
  bound root
- **AND** it SHALL use the resulting absolute client path as the new root

#### Scenario: User-anchored root switch
- **WHEN** a root-bound interaction supplies a `path` beginning with `~` or
  `~user`
- **THEN** the system SHALL expand that user anchor before selecting the new root

#### Scenario: Relative root switch without a current root
- **WHEN** an unbound interaction supplies a relative `path` to `switch_project`
- **THEN** the system SHALL reject the request without creating or binding a project
- **AND** it SHALL explain that a relative switch requires a current root

#### Scenario: Switch request lacks a selection
- **WHEN** an interaction calls `switch_project` without both `name` and `path`
- **THEN** the system SHALL return an invalid-selection error
- **AND** it SHALL not change the active configuration or root

#### Scenario: Tool discovery describes root rebinding
- **WHEN** an MCP client discovers the `switch_project` tool
- **THEN** its description SHALL state that `path` can rebind the project root
- **AND** it SHALL distinguish that behaviour from name-only configuration selection

#### Scenario: Result Pattern Compliance
- **WHEN** a project selection tool succeeds or fails
- **THEN** it SHALL return its result using the standard Result pattern
