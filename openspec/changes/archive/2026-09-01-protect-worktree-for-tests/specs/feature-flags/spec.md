## ADDED Requirements

### Requirement: Global Feature Flags Are Process-Owned
Global feature-flag list, get, set, and remove operations SHALL be owned by the
process runtime, which SHALL persist them through the configuration service.
The global feature-flag handler SHALL NOT depend on a Session or on a direct
configuration-service reference.

Project feature flags remain part of the bound project's configuration and are
outside this requirement.

#### Scenario: Global flag is read or written
- **WHEN** an operation lists, gets, sets, or removes a global feature flag
- **THEN** it SHALL go through the process runtime
- **AND** the runtime SHALL persist the change in the shared configuration
- **AND** the handler SHALL NOT require a Session or a configuration-service
  object

#### Scenario: Project flag is unchanged in ownership
- **WHEN** an operation lists, gets, sets, or removes a project feature flag
- **THEN** it SHALL continue to use the bound project's configuration
- **AND** it SHALL NOT treat that flag as process-global state
