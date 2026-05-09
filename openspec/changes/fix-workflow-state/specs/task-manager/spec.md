## ADDED Requirements

### Requirement: Managed Task Lifecycle Reconciliation
The system SHALL dynamically reconcile managed task lifecycle when feature flags
or active project context change.

#### Scenario: Workflow flag enabled at runtime
- **WHEN** the user changes the `workflow` project flag at runtime
- **AND** the resolved flag value enables workflow tracking
- **THEN** the system SHALL start or resubscribe the workflow monitoring task
- **AND** it SHALL NOT require an MCP server or agent restart

#### Scenario: Workflow flag disabled at runtime
- **WHEN** the user changes the `workflow` project flag at runtime
- **AND** the resolved flag value disables workflow tracking
- **THEN** the system SHALL stop or unsubscribe the workflow monitoring task
- **AND** it SHALL NOT continue sending workflow monitoring setup or reminder
  instructions

#### Scenario: Project switched to different task flags
- **WHEN** the active project changes
- **AND** the new project has different resolved values for task-dependent flags
- **THEN** the system SHALL stop managed tasks no longer enabled for the new
  project
- **AND** it SHALL start managed tasks newly enabled for the new project
- **AND** it SHALL avoid duplicate active subscriptions for the same managed task

#### Scenario: OpenSpec flag changed at runtime
- **WHEN** the resolved `openspec` flag changes at runtime
- **THEN** the system SHALL reconcile OpenSpec task behavior according to the new
  resolved flag value
- **AND** it SHALL NOT require an MCP server or agent restart

#### Scenario: Client-info flag changed at runtime
- **WHEN** the resolved `allow-client-info` flag changes at runtime
- **THEN** the system SHALL reconcile client-info task or subscription behavior
  according to the new resolved flag value
- **AND** it SHALL NOT require an MCP server or agent restart

#### Scenario: Concurrent lifecycle triggers
- **WHEN** project changes and flag changes trigger task reconciliation close
  together
- **THEN** the system SHALL serialize or coalesce reconciliation work
- **AND** it SHALL complete without deadlocking task manager event handling
- **AND** the final active managed task set SHALL match the latest resolved
  flags for the active project

#### Scenario: Idempotent reconciliation
- **WHEN** reconciliation runs repeatedly without a relevant flag or project
  change
- **THEN** the system SHALL leave already-correct managed tasks unchanged
- **AND** it SHALL NOT create duplicate task instances or duplicate
  subscriptions
