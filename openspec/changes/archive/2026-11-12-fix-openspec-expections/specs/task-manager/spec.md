# Spec Delta

## MODIFIED Requirements

### Requirement: OpenSpec task follows configuration changes
The OpenSpec task SHALL use the existing configuration-change publication and project-task restart lifecycle. It SHALL not require a separate callback or polling mechanism for feature-flag changes. An explicit enable transition SHALL not validate or inspect the bound project's OpenSpec store.

#### Scenario: Current project enables OpenSpec
- **WHEN** the current Project's `project_flags.openspec` changes from a disabled to an enabled value
- **THEN** configuration publication SHALL restart that Session's project tasks
- **AND** the restarted task SHALL request a CLI version check when the global version state is absent or expired
- **AND** SHALL NOT request a project-scoped OpenSpec CLI command
- **AND** SHALL NOT inspect or request `openspec/config.yaml`, `openspec/changes`, or another worktree-relative OpenSpec path

#### Scenario: Enable transition has no OpenSpec project configuration
- **WHEN** the current Project's `project_flags.openspec` changes from disabled to enabled
- **THEN** the task SHALL not determine whether that Project resolves an OpenSpec store
- **AND** SHALL not infer a result from local configuration or filesystem listings

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
The OpenSpec task SHALL establish global CLI-version state independently of collecting project change data. Session startup, reconnection, ordinary project binding, and an enable transition SHALL not inspect repository assets or request project-store information. Detecting an OpenSpec project SHALL NOT itself queue an OpenSpec changes-list instruction.

#### Scenario: OpenSpec project detection
- **WHEN** a session starts, reconnects, binds, or enables OpenSpec with current global state
- **THEN** the task SHALL not inspect `openspec/config.yaml`, `openspec/changes`, or another presumed OpenSpec location
- **AND** SHALL not request `openspec list --json`

#### Scenario: Change data is required
- **WHEN** an OpenSpec consumer requires change data
- **THEN** the task SHALL request the changes list on demand
