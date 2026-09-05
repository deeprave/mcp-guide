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
