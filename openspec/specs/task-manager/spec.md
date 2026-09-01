# task-manager Specification

## Purpose
TBD - created by archiving completed changes. Update Purpose after archive.

## Requirements

### Requirement: Deferred Project-Bound Initialization
The task manager SHALL support startup before a real project is available.

Project-independent startup work MAY run during server initialization, but
project-sensitive initialization SHALL be deferred until the session is bound to a
real project.

#### Scenario: Server startup without MCP context
- **WHEN** the server runs startup hooks before any client request context exists
- **THEN** task manager initialization SHALL complete without requiring immediate project resolution
- **AND** no failure SHALL occur solely because client roots are not yet available

#### Scenario: First project-bound initialization
- **WHEN** the session later binds to a real project
- **THEN** the task manager SHALL initialize resolved flags and other project-sensitive state at that time
- **AND** deferred initialization SHALL run at most once per project bind event

### Requirement: Project-Scoped Task Lifecycle
The system SHALL manage project-scoped tasks after project context is available, while each task decides whether and how to activate for that context.

#### Scenario: Registered project task does not instantiate on import
- **WHEN** a project-scoped task class is registered
- **THEN** the system SHALL record it for lifecycle management
- **AND** SHALL NOT instantiate it during registration

#### Scenario: Project switch replaces project tasks
- **WHEN** the active project changes
- **THEN** the task manager SHALL stop and unsubscribe active project-scoped task instances
- **AND** SHALL clear project-scoped cache, queued instructions, and tracked instructions
- **AND** SHALL create fresh task instances for the new project without duplicate subscriptions

#### Scenario: Configuration change re-evaluates project tasks
- **WHEN** project or global configuration changes affect the active project
- **THEN** the task manager SHALL restart project-scoped tasks
- **AND** each task SHALL re-evaluate its activation policy without requiring an MCP restart

#### Scenario: Concurrent lifecycle triggers remain consistent
- **WHEN** project and configuration changes trigger lifecycle restarts close together
- **THEN** the task manager SHALL serialize or coalesce the mutations without deadlock
- **AND** the final active task set SHALL belong to the latest project context

### Requirement: MCP Update Task
The system SHALL provide `McpUpdateTask` that checks the `autoupdate` feature
flag once at startup and queues an update instruction when enabled.

#### Scenario: Autoupdate enabled by default
- **WHEN** task initializes via startup timer
- **AND** `autoupdate` is not set
- **THEN** the update instruction is queued
- **AND** task unsubscribes after handling the startup check

#### Scenario: Autoupdate explicitly enabled
- **WHEN** task initializes via startup timer
- **AND** `autoupdate` feature flag is true
- **THEN** the update instruction is queued
- **AND** task unsubscribes after handling the startup check

#### Scenario: Autoupdate explicitly disabled
- **WHEN** task initializes via startup timer
- **AND** `autoupdate` feature flag is false
- **THEN** no instruction is queued
- **AND** task unsubscribes after handling the startup check

#### Scenario: Prompt is tracked for acknowledgement
- **WHEN** task queues the update instruction
- **THEN** it is queued as an acknowledged instruction
- **AND** the task manager may re-send reminders until it is acknowledged

#### Scenario: Update acknowledgement stops reminders
- **WHEN** the agent runs `update_documents`
- **AND** `McpUpdateTask` has a tracked instruction id
- **THEN** that instruction is acknowledged
- **AND** further reminders are not sent for the same queued prompt

### Requirement: Startup Update Prompts Require Updateable Installed Docs
The system SHALL queue acknowledged documentation update prompts only for
updateable installed documentation roots.

Startup prompting SHALL first validate that the resolved documentation root is a
safe update target and that the installed documentation version file exists
before comparing versions or queuing an update instruction.

#### Scenario: Missing installed version file suppresses prompt
- **WHEN** the resolved documentation root does not contain a `.version` file
- **THEN** the system SHALL not queue an acknowledged `update_documents` prompt

#### Scenario: Unsafe docroot suppresses prompt
- **WHEN** the resolved documentation root is not safe for updates
- **THEN** the system SHALL not queue an acknowledged `update_documents` prompt

#### Scenario: Valid outdated docs still prompt
- **WHEN** the resolved documentation root is safe for updates
- **AND** the `.version` file exists
- **AND** the installed documentation version differs from the package version
- **THEN** the system SHALL queue the acknowledged `update_documents` prompt

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
