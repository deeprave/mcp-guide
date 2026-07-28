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
