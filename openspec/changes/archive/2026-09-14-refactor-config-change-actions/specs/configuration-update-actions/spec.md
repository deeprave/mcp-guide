## Purpose

Defines the per-session change contract that safely applies shared
configuration updates without restarting or invalidating unrelated features.

## ADDED Requirements

### Requirement: Effective configuration update contract
The system SHALL represent a configuration publication to a bound session as an
update containing the session's previous and new effective configuration and
the computed differences for active-project content, global flags, active-project categories,
collections, project flags, and task-relevant feature flags.

The effective configuration exposed to consumers SHALL be an immutable
projection. The Session SHALL reconstruct and own a separate mutable project
model when it applies the update to its active binding.

The system SHALL represent a changed validated configuration image as a
configuration snapshot delta containing old/new snapshots, changed global flag
information, and changed strict project identities. The process runtime SHALL
derive effective updates from that delta only for active, live, bound sessions.

#### Scenario: Project configuration changes for an active session
- **WHEN** a publication changes the configuration selected by a bound session
- **THEN** that session receives an update containing the previous and new
  effective active-project configuration
- **AND** the update identifies changed active-project content, categories, collections, project
  flags, and resolved feature flags

#### Scenario: Global flags change
- **WHEN** a publication changes global feature flags
- **THEN** every active live bound session becomes a candidate for an effective
  update with its prior and new resolved global flag values
- **AND** a candidate receives a consumer update only when its effective values
  differ
- **AND** no project-specific difference is reported unless that session's
  active project also changed

#### Scenario: Global flag is masked by project configuration
- **WHEN** a changed global flag is overridden to the same effective value by a
  bound session's project configuration
- **THEN** that session receives no consumer update for the global change

#### Scenario: Unbound or expiring session
- **WHEN** a configuration snapshot delta is published
- **AND** a session is unbound, expiring, disposed, or otherwise not live
- **THEN** the process runtime SHALL NOT select it for effective update
  delivery

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
The system SHALL serialize configuration-update application per session through
a single-consumer queue and coalesce overlapping publications so each consumer
converges on the latest effective configuration revision.

#### Scenario: Concurrent shared publications
- **WHEN** a file watcher publication and an in-process write overlap
- **THEN** a session applies updates in a consistent order
- **AND** it does not retain caches, tasks, or project data from a superseded
  configuration snapshot
