## ADDED Requirements

### Requirement: Bounded machine-wide OpenSpec version checks
The OpenSpec task SHALL use the global `openspec-state` feature flag to check the
installed OpenSpec CLI version at most once in each rolling 24-hour period on a
computer.
It SHALL continue to use the current Project's `project_flags.openspec` value as
the enablement gate.
It SHALL read and replace this state through the existing global feature-flag
service and SHALL NOT access the configuration file directly.

#### Scenario: OpenSpec is disabled for the active project
- **WHEN** the active Project does not enable OpenSpec
- **THEN** the OpenSpec task SHALL NOT start or request a version check for that Project
- **AND** global CLI availability SHALL NOT enable OpenSpec for that Project

#### Scenario: First or expired version check
- **WHEN** the active Project's `project_flags.openspec` is enabled
- **AND** global `openspec-state.checked` is absent or at least 24 hours old
- **THEN** the task SHALL request an OpenSpec version check

#### Scenario: Enabled project initialises absent global state
- **WHEN** the active Project's `project_flags.openspec` is enabled
- **AND** no global OpenSpec state has been stored
- **THEN** the task SHALL check OpenSpec availability and version
- **AND** it SHALL set the complete global `openspec-state` feature flag after
  processing the response

#### Scenario: Recent version check is reused
- **WHEN** global `openspec-state.checked` is less than 24 hours old
- **THEN** the task SHALL NOT request another OpenSpec version check
- **AND** it SHALL use the stored global validation and version values

#### Scenario: Completed version check updates global state
- **WHEN** an OpenSpec version-check response has been processed
- **THEN** the task SHALL set global `openspec-state.checked` to the current UTC
  Unix timestamp encoded as a decimal string
- **AND** it SHALL persist the parsed version and validation result in that
  feature flag

#### Scenario: Invalid version-check response is bounded
- **WHEN** an OpenSpec version-check response cannot establish a valid version
- **THEN** the task SHALL persist `validated="false"` and omit `version`
- **AND** it SHALL still update global `openspec-state.checked`

### Requirement: OpenSpec task follows configuration changes
The OpenSpec task SHALL use the existing configuration-change publication and
project-task restart lifecycle. It SHALL not require a separate callback or
polling mechanism for feature-flag changes.

#### Scenario: Current project enables OpenSpec
- **WHEN** the current Project's `project_flags.openspec` changes to an enabled value
- **THEN** configuration publication SHALL restart that Session's project tasks
- **AND** the restarted OpenSpec task SHALL read global `openspec-state`
- **AND** it SHALL queue an availability instruction when state is absent or expired
- **AND** it SHALL queue a version-check instruction only after a successful
  availability response

#### Scenario: Current project disables OpenSpec
- **WHEN** the current Project's `project_flags.openspec` changes to a disabled value
- **THEN** configuration publication SHALL restart that Session's project tasks
- **AND** the OpenSpec task SHALL stop and unsubscribe for that Session

#### Scenario: Global state completion does not duplicate checks
- **WHEN** an OpenSpec check writes a current global `openspec-state.checked` value
- **AND** global feature-flag publication restarts an enabled Session's project tasks
- **THEN** the restarted OpenSpec task SHALL reuse that state
- **AND** it SHALL NOT queue another availability or version-check instruction
