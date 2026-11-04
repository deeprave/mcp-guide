# Spec Delta

## MODIFIED Requirements

### Requirement: Bounded machine-wide OpenSpec version checks
The OpenSpec task SHALL use the global `openspec-state` feature flag to check the installed OpenSpec CLI version at most once in each rolling 24-hour period on a computer. It SHALL use the active Project's `project_flags.openspec` as the enablement gate, read and replace state through the global feature-flag service, and not access the configuration file directly.

#### Scenario: OpenSpec is disabled for the active project
- **WHEN** the active Project does not enable OpenSpec
- **THEN** the OpenSpec task SHALL deactivate itself and SHALL NOT request a version or repository-asset check
- **AND** global CLI availability SHALL NOT enable OpenSpec for that Project

#### Scenario: Recent version check is reused
- **WHEN** the active Project enables OpenSpec
- **AND** global `openspec-state.checked` is less than 24 hours old
- **THEN** the task SHALL use the stored validation and version values
- **AND** SHALL NOT request a version check or repository-asset check

#### Scenario: First or expired version check
- **WHEN** the active Project enables OpenSpec
- **AND** global `openspec-state.checked` is absent or at least 24 hours old
- **THEN** the task SHALL request only an OpenSpec version check

#### Scenario: Enabled project initialises absent global state
- **WHEN** the active Project enables OpenSpec
- **AND** no global OpenSpec state has been stored
- **THEN** the task SHALL request only an OpenSpec version check
- **AND** SHALL set the complete global `openspec-state` feature flag after processing the response

#### Scenario: Completed version check updates global state
- **WHEN** an OpenSpec version-check response has been processed
- **THEN** the task SHALL set global `openspec-state.checked` to the current UTC Unix timestamp encoded as a decimal string
- **AND** SHALL persist the parsed version and validation result in that feature flag

#### Scenario: Invalid version-check response is bounded
- **WHEN** an OpenSpec version-check response cannot establish a valid version
- **THEN** the task SHALL persist `validated="false"` and omit `version`
- **AND** SHALL still update global `openspec-state.checked`

### Requirement: OpenSpec task follows configuration changes
The OpenSpec task SHALL use the existing configuration-change publication and project-task restart lifecycle. It SHALL not require a separate callback or polling mechanism for feature-flag changes.

#### Scenario: Current project enables OpenSpec
- **WHEN** the current Project's `project_flags.openspec` changes from a disabled to an enabled value
- **THEN** configuration publication SHALL restart that Session's project tasks
- **AND** the restarted task SHALL verify that `openspec/config.yaml` and `openspec/changes` exist
- **AND** only after both assets are verified SHALL it request an OpenSpec version check and replace the complete global `openspec-state`

#### Scenario: Enable transition has incomplete repository assets
- **WHEN** the current Project's `project_flags.openspec` changes from disabled to enabled
- **AND** either `openspec/config.yaml` or `openspec/changes` is absent
- **THEN** the task SHALL NOT request a version check
- **AND** SHALL retain the existing global `openspec-state`

#### Scenario: Current project disables OpenSpec
- **WHEN** the current Project's `project_flags.openspec` changes from an enabled to a disabled value
- **THEN** configuration publication SHALL restart that Session's project tasks
- **AND** the OpenSpec task SHALL deactivate itself for that Session

#### Scenario: Global state completion does not duplicate checks
- **WHEN** an OpenSpec check writes a current global `openspec-state.checked` value
- **AND** global feature-flag publication restarts an enabled Session's project tasks
- **THEN** the restarted OpenSpec task SHALL reuse that state
- **AND** SHALL NOT queue another version or repository-asset check

### Requirement: Passive OpenSpec project initialisation
The OpenSpec task SHALL establish CLI validation and version independently of collecting project change data. Session startup, reconnection, and ordinary project binding SHALL not verify OpenSpec repository assets. Detecting an OpenSpec project SHALL NOT itself queue an OpenSpec changes-list instruction.

#### Scenario: OpenSpec project detection
- **WHEN** a session starts or reconnects with OpenSpec enabled and current global state
- **THEN** the task SHALL not verify `openspec/config.yaml`, `openspec/changes`, or request `openspec list --json`

#### Scenario: Change data is required
- **WHEN** an OpenSpec consumer requires change data
- **THEN** the task SHALL request the changes list on demand
