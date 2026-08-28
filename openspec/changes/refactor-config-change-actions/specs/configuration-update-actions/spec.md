## Purpose

Defines the per-session change contract that safely applies shared
configuration updates without restarting or invalidating unrelated features.

## ADDED Requirements

### Requirement: Effective configuration update contract
The system SHALL represent a configuration publication to a bound session as an
update containing the session's previous and new effective configuration and
the computed differences for global flags, active-project categories,
collections, project flags, and task-relevant feature flags.

#### Scenario: Project configuration changes for an active session
- **WHEN** a publication changes the configuration selected by a bound session
- **THEN** that session receives an update containing the previous and new
  effective active-project configuration
- **AND** the update identifies the changed categories, collections, project
  flags, and resolved feature flags

#### Scenario: Global flags change
- **WHEN** a publication changes global feature flags
- **THEN** every active bound session receives an update with its prior and new
  effective global flag values
- **AND** no project-specific difference is reported unless that session's
  active project also changed

### Requirement: Session-scoped update consumer registration
The system SHALL allow a bound session to register configuration-update
consumers and SHALL dispatch each applicable update through a common
configuration-update protocol.

#### Scenario: Components register when a session binds
- **WHEN** a session becomes bound to a project root
- **THEN** its Session-owned configuration consumers are registered for update
  dispatch
- **AND** consumers are isolated to that session

#### Scenario: Consumer failure isolation
- **WHEN** one registered consumer fails while applying an update
- **THEN** the session continues dispatching the update to its remaining
  consumers
- **AND** the failure is recorded for diagnosis

### Requirement: Ordered and coalesced configuration application
The system SHALL serialize configuration-update application per session and
coalesce overlapping publications so each consumer converges on the latest
effective configuration.

#### Scenario: Concurrent shared publications
- **WHEN** a file watcher publication and an in-process write overlap
- **THEN** a session applies updates in a consistent order
- **AND** it does not retain caches, tasks, or project data from a superseded
  configuration snapshot
