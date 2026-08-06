## ADDED Requirements

### Requirement: Context-Owned Instruction Delivery
The task manager SHALL associate pending instructions and acknowledgements with an
explicit interaction owner and project identity. It SHALL deliver an instruction only
when a subsequent request proves ownership of the same context or a valid descendant
state.

#### Scenario: Background instruction is queued
- **WHEN** project-scoped background work creates an instruction for a valid owner and project
- **THEN** the task manager SHALL queue it with that owner and project identity
- **AND** it SHALL not rely on an ambient active session to identify the recipient

#### Scenario: Different project request processes a result
- **WHEN** a request for a different owner or project processes a result
- **THEN** the task manager SHALL not attach the queued instruction from another context
- **AND** the original instruction SHALL remain isolated until delivered or expired

### Requirement: Request-Safe Project Task Lifecycle
The task manager SHALL manage project-scoped task lifecycle using explicit context
ownership. Lifecycle cleanup and restart SHALL not require a live MCP connection,
private SDK session object, or roots notification callback.

#### Scenario: Request context changes project
- **WHEN** a valid request context resolves a different project for the same owner
- **THEN** the task manager SHALL stop and clean up the previous project's scoped tasks
- **AND** it SHALL start only the new project's eligible tasks for that owner

#### Scenario: Expired interaction state
- **WHEN** a task manager operation encounters expired or invalid owner state
- **THEN** it SHALL safely discard or expire the associated transient delivery state
- **AND** it SHALL not attach that state to a new request context
