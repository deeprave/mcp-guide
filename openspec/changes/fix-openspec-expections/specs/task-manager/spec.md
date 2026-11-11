# Spec Delta

## MODIFIED Requirements

### Requirement: OpenSpec task follows configuration changes
The OpenSpec task SHALL use the existing configuration-change publication and project-task restart lifecycle. It SHALL not require a separate callback or polling mechanism for feature-flag changes. An explicit enable transition SHALL validate the OpenSpec CLI and its store resolution from the bound project, without inspecting or requesting repository assets.

#### Scenario: Current project enables OpenSpec
- **WHEN** the current Project's `project_flags.openspec` changes from a disabled to an enabled value
- **THEN** configuration publication SHALL restart that Session's project tasks
- **AND** the restarted task SHALL request a CLI version check when the global version state is absent or expired
- **AND** SHALL request an OpenSpec CLI command that resolves the active project's store
- **AND** SHALL NOT inspect or request `openspec/config.yaml`, `openspec/changes`, or another worktree-relative OpenSpec path

#### Scenario: Enable transition resolves an inherited or named store
- **WHEN** the current Project's `project_flags.openspec` changes from disabled to enabled
- **AND** the OpenSpec CLI successfully resolves a store from an ancestor directory or named-store configuration
- **THEN** the task SHALL treat OpenSpec as available for that Project
- **AND** SHALL retain the Project's enabled setting without requiring a worktree-local OpenSpec installation

#### Scenario: Enable transition has no OpenSpec project configuration
- **WHEN** the current Project's `project_flags.openspec` changes from disabled to enabled
- **AND** an OpenSpec CLI command reports that no usable store is available from the bound project
- **THEN** the task SHALL direct the user to `guide://_openspec/init`
- **AND** SHALL NOT infer store availability from client filesystem listings

#### Scenario: Current project disables OpenSpec
- **WHEN** the current Project's `project_flags.openspec` changes to a disabled value
- **THEN** configuration publication SHALL restart that Session's project tasks
- **AND** the OpenSpec task SHALL stop and unsubscribe for that Session

#### Scenario: Global state completion does not duplicate checks
- **WHEN** an OpenSpec check writes a current global `openspec-state.checked` value
- **AND** global feature-flag publication restarts an enabled Session's project tasks
- **THEN** the restarted OpenSpec task SHALL reuse that state
- **AND** it SHALL NOT queue another availability or version-check instruction

### Requirement: Passive OpenSpec project initialisation
The OpenSpec task SHALL establish CLI validation and version independently of collecting project change data. Session startup, reconnection, and ordinary project binding SHALL not inspect repository assets or request a project-store check. Detecting an OpenSpec project SHALL NOT itself queue an OpenSpec changes-list instruction.

#### Scenario: OpenSpec project detection
- **WHEN** a session starts or reconnects with OpenSpec enabled and current global state
- **THEN** the task SHALL not inspect `openspec/config.yaml`, `openspec/changes`, or another presumed OpenSpec location
- **AND** SHALL not request `openspec list --json`

#### Scenario: Change data is required
- **WHEN** an OpenSpec consumer requires change data
- **THEN** the task SHALL request the changes list on demand
