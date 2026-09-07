# guide-project-tools

## Purpose

Define project selection and project-management tool contracts.

## Requirements

### Requirement: Switch Current Project
The system SHALL provide `set_project(path)` for initial project-root binding and
`switch_project(name? | path?)` for selecting configuration projects during a
retained interaction.

The public `switch_project` tool description SHALL state that it can rebind the
project root when `path` is supplied, in addition to selecting the active
configuration project.

`set_project` SHALL continue to require an initial client root path and SHALL
reject a second root binding for the same interaction. `switch_project` SHALL
require exactly one of `name` or `path`.

A different selection SHALL create a fresh bound Session and make it current
under the unchanged public session ID. The outgoing Session SHALL expire without
changing its original binding. The tool SHALL reject a switch while that ID
already has an expiring Session; it SHALL NOT queue the switch or create another
expiring instance.

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
- **THEN** the system SHALL percent-decode its local URI path and treat it as
  an absolute client filesystem path

#### Scenario: Relative path rejected
- **WHEN** an unbound interaction calls `set_project` with a relative path
- **THEN** it SHALL return an error with type `invalid_name`
- **AND** the error message SHALL indicate an absolute path is required

#### Scenario: Absolute path normalised
- **WHEN** an unbound interaction calls `set_project` with an absolute path containing
  `..` components
- **THEN** it SHALL normalise the path before binding the resulting root
- **AND** normalisation SHALL NOT turn relative input into an accepted absolute path

#### Scenario: Name-only configuration selection
- **GIVEN** no Session for the interaction's ID is expiring
- **WHEN** a root-bound interaction calls `switch_project` with `name` and no
  `path`
- **THEN** the system SHALL select or create that configuration at the current
  bound root
- **AND** it SHALL retain the bound root unchanged
- **AND** a different configuration selection SHALL use a fresh Session under the same public ID

#### Scenario: Path-only root switch
- **GIVEN** no Session for the interaction's ID is expiring
- **WHEN** a root-bound interaction calls `switch_project` with `path` and no
  `name`
- **THEN** the system SHALL change the interaction root to the normalised path
- **AND** it SHALL select or create the configuration named by that path's basename
- **AND** a different selection SHALL replace the bound Session without changing the public ID

#### Scenario: Combined selection rejected
- **WHEN** an interaction calls `switch_project` with both `name` and `path`
- **THEN** the system SHALL return an invalid-selection error
- **AND** it SHALL not change the active configuration or root

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

#### Scenario: Switch without a current root
- **WHEN** an unbound interaction calls `switch_project`, including with a relative `path`
- **THEN** the system SHALL reject the request without creating or binding a project
- **AND** it SHALL direct the agent to establish a project root with `set_project`

#### Scenario: Switch request lacks a selection
- **WHEN** an interaction calls `switch_project` without either `name` or `path`
- **THEN** the system SHALL return an invalid-selection error
- **AND** it SHALL not change the active configuration or root

#### Scenario: Tool discovery describes root rebinding
- **WHEN** an MCP client discovers the `switch_project` tool
- **THEN** its description SHALL state that `path` can rebind the project root
- **AND** it SHALL distinguish that behaviour from name-only configuration selection

#### Scenario: Same selection is a no-op
- **GIVEN** no Session for the public ID is expiring
- **WHEN** a valid switch selects the already current configuration and root
- **THEN** it SHALL succeed without replacing the Session or restarting its tasks

#### Scenario: Switch rejected while prior Session is expiring
- **GIVEN** the interaction's ID already has an expiring Session
- **WHEN** another switch is requested, including an unchanged selection
- **THEN** the request SHALL fail with an explicit pending-expiry error
- **AND** it SHALL leave the current and expiring Sessions unchanged
- **AND** it SHALL NOT queue or automatically retry the switch

#### Scenario: Replacement preparation fails
- **GIVEN** the interaction has a current bound Session
- **WHEN** target validation or replacement preparation fails
- **THEN** the tool SHALL return an error without changing the current binding
- **AND** an unpublished candidate SHALL NOT become available to follow-up requests

#### Scenario: Successful switch returns replacement context
- **WHEN** a project switch succeeds
- **THEN** the result SHALL describe the replacement's project and preserve the public session ID
- **AND** any startup instructions attached to that result SHALL belong to the replacement
- **AND** a subsequent client request SHALL resolve the replacement

#### Scenario: Result Pattern Compliance
- **WHEN** a project selection tool succeeds or fails
- **THEN** it SHALL return its result using the standard Result pattern

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
