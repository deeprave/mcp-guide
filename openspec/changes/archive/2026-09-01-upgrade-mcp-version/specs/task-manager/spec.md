## ADDED Requirements

### Requirement: Session-Owned Instruction Delivery
A context-owned Guide `Session`, selected through the request context, SHALL contain a
non-global TaskManager instance. The Session and its TaskManager SHALL share a
lifecycle. That TaskManager SHALL own pending instructions, acknowledgements, caches,
timers, and project-scoped task state; it SHALL associate pending instructions and
acknowledgements with an explicit Session owner and project identity, and deliver an
instruction only when a subsequent request proves ownership of the same context or a
valid descendant state.

#### Scenario: Background instruction is queued
- **WHEN** project-scoped background work creates an instruction for a valid owner and project
- **THEN** the task manager SHALL queue it with that owner and project identity
- **AND** it SHALL not rely on an ambient active session to identify the recipient

#### Scenario: Stdio single-agent compatibility
- **WHEN** Guide runs over stdio for one agent process
- **THEN** its `GuideRuntime` SHALL use one context-owned Guide Session for that agent
- **AND** that Session SHALL contain a Session-owned TaskManager rather than use a global instance
- **AND** instruction delivery, timers, and project lifecycle SHALL retain the current single-agent behaviour

#### Scenario: Different project request processes a result
- **WHEN** a request for a different owner or project processes a result
- **THEN** the task manager SHALL not attach the queued instruction from another context
- **AND** the original instruction SHALL remain isolated until delivered or expired

### Requirement: Request-Safe Project Task Lifecycle
The context-owned Guide Session and its contained TaskManager SHALL manage
project-scoped task lifecycle using explicit context ownership. Lifecycle cleanup and
startup SHALL not require a live MCP connection, private SDK session object, or roots
notification callback.

#### Scenario: Interaction begins with a selected project
- **WHEN** an unbound interaction explicitly selects a project
- **THEN** its task manager/state object SHALL start only that project's eligible tasks
- **AND** it SHALL not create or alter another interaction's project-scoped tasks

#### Scenario: Expired interaction state
- **WHEN** a task manager operation encounters expired or invalid owner state
- **THEN** it SHALL safely discard or expire the associated transient delivery state
- **AND** it SHALL not attach that state to a new request context

### Requirement: Session-Local Configuration Change Handling
When the shared ConfigManager publishes a change to an affected Guide Session,
that Session SHALL dispatch its Session-listener lifecycle locally. Its contained
TaskManager SHALL invalidate configuration-derived flags and apply any required task
startup, shutdown, or event-interception refresh. A publication SHALL never mutate
another Session's TaskManager directly or merge their queues, timers, caches, or task
instances.

#### Scenario: Global configuration publication reaches separate task managers
- **WHEN** a global feature-flag change is published to multiple active Sessions
- **THEN** each Session SHALL refresh its own contained TaskManager through its local
  listener lifecycle
- **AND** each TaskManager's queues, timers, and cache SHALL remain isolated

#### Scenario: Project configuration publication is scoped
- **WHEN** a project-configuration update is published to Sessions with a matching
  active `(name, root_hash)` identity
- **THEN** only those Sessions SHALL run task lifecycle refreshes for that project
- **AND** a Session with a different configuration identity SHALL retain its own
  task-manager state unchanged
