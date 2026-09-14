## MODIFIED Requirements

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
- **WHEN** a configuration update changes global or project flags relevant to
  the active project
- **THEN** the task manager SHALL invalidate only caches derived from changed
  configuration values
- **AND** SHALL start, stop, or reconfigure only task handlers whose activation
  or configuration is affected
- **AND** SHALL retire cache entries, queued instructions, and tracked
  acknowledgement retries owned by a handler it stops or replaces
- **AND** SHALL retain unaffected task handlers and their valid state without
  requiring an MCP restart

#### Scenario: Disabled task has pending state
- **WHEN** a configuration update disables or replaces a task that has produced
  cache entries or queued acknowledgement instructions
- **THEN** the task manager SHALL remove that task's pending state before a
  later result can deliver it
- **AND** SHALL retain pending state owned by unaffected handlers and unowned
  Session-level producers

#### Scenario: Project task uses an explicit activation
- **WHEN** the task manager creates a project-scoped task instance
- **THEN** it SHALL create and provide one task-owned activation capability
- **AND** the activation SHALL be the only project-task authority for its
  subscriptions, task-owned cache entries, queued instructions, tracked
  acknowledgement instructions, and deferred delivery callbacks
- **AND** the project task SHALL NOT receive the general task manager for
  mutable operations

#### Scenario: Retired activation cannot restore task state
- **WHEN** the task manager stops or replaces a project-scoped task
- **THEN** it SHALL retire that task's activation before invoking task cleanup
- **AND** SHALL remove only the subscriptions, cache entries, queued
  instructions, and tracked acknowledgement state owned by that activation
- **AND** any startup, event, timer, tool, or deferred delivery callback that
  resumes after retirement SHALL NOT create or restore task-owned state
- **AND** retirement and cleanup SHALL be idempotent

#### Scenario: Configuration change has no task-relevant difference
- **WHEN** a configuration update changes only categories or collections and
  no task-relevant feature value changes
- **THEN** the task manager SHALL NOT restart task handlers
- **AND** SHALL retain valid task caches and queued instructions

#### Scenario: Concurrent lifecycle triggers remain consistent
- **WHEN** project and configuration changes trigger lifecycle restarts close together
- **THEN** the task manager SHALL serialize or coalesce the mutations without deadlock
- **AND** the final active task set SHALL belong to the latest project context
