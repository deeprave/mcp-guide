## ADDED Requirements

### Requirement: Project-Scoped Task Lifecycle
The system SHALL manage project-scoped task lifecycle after project context is
available, while each task class decides whether and how to activate for that
context.

#### Scenario: Project-scoped task class registration
- **WHEN** a project-scoped task module is imported
- **AND** the task class is decorated for task registration
- **THEN** the system SHALL register the task class for later lifecycle
  management
- **AND** it SHALL NOT instantiate the task class during registration
- **AND** it SHALL NOT require the registration decorator to specify feature
  flags, activation predicates, cache keys, or factories

#### Scenario: Initial project bind starts project-scoped tasks
- **WHEN** a project is bound for the first time
- **THEN** the task manager SHALL instantiate registered project-scoped task
  classes for the current project context
- **AND** it SHALL invoke task-owned async startup behavior
- **AND** each task SHALL decide whether to subscribe or remain inactive for
  that context
- **AND** it SHALL NOT require an MCP server or agent restart

#### Scenario: Project switch restarts project-scoped tasks
- **WHEN** the active project changes
- **THEN** the task manager SHALL stop all active project-scoped task instances
  from the previous project
- **AND** it SHALL unsubscribe stopped instances from task-manager event delivery
- **AND** it SHALL clear project-scoped task state needed to avoid stale context
- **AND** it SHALL clear queued and tracked instructions that may reference the
  previous project
- **AND** it SHALL instantiate fresh registered task classes for the new project
  context
- **AND** it SHALL avoid duplicate active subscriptions for the same registered
  task class

#### Scenario: Runtime project config changes restart project-scoped tasks
- **WHEN** project or global config changes affect the active project
- **THEN** the task manager SHALL restart registered project-scoped tasks for the
  current project context
- **AND** each task SHALL re-evaluate its own activation policy during startup
- **AND** it SHALL NOT require an MCP server or agent restart

#### Scenario: Task-owned activation policy
- **WHEN** a registered project-scoped task starts
- **THEN** the task class SHALL be able to inspect project flags, project config,
  client context, command availability, or other task-specific inputs
- **AND** the task manager SHALL NOT assume a one-to-one relationship between a
  feature flag and a task class

#### Scenario: Concurrent lifecycle triggers
- **WHEN** project changes and config changes trigger task lifecycle restart
  close together
- **THEN** the system SHALL serialize or coalesce lifecycle mutation work
- **AND** it SHALL complete without deadlocking task manager event handling
- **AND** the final active project-scoped task set SHALL belong to the latest
  active project context

#### Scenario: Idempotent lifecycle restart
- **WHEN** lifecycle restart runs repeatedly for the same active project context
- **THEN** the system SHALL avoid duplicate task instances and duplicate
  subscriptions
- **AND** it SHALL leave task-manager event delivery in a consistent state
