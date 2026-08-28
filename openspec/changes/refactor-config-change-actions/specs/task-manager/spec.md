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
- **AND** SHALL retain unaffected task handlers and their valid state without
  requiring an MCP restart

#### Scenario: Configuration change has no task-relevant difference
- **WHEN** a configuration update changes only categories or collections and
  no task-relevant feature value changes
- **THEN** the task manager SHALL NOT restart task handlers
- **AND** SHALL retain valid task caches and queued instructions

#### Scenario: Concurrent lifecycle triggers remain consistent
- **WHEN** project and configuration changes trigger lifecycle restarts close together
- **THEN** the task manager SHALL serialize or coalesce the mutations without deadlock
- **AND** the final active task set SHALL belong to the latest project context
