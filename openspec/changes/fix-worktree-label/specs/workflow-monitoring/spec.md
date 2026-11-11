# Spec Delta

## MODIFIED Requirements

### Requirement: Project-scoped workflow task activation

The workflow monitoring task SHALL activate from the current project context rather than import-time initialization. For a linked-worktree session, it SHALL also activate a session-local minimum workflow capability when the shared project's workflow setting is disabled, so the session can receive its local workflow file and establish its worktree label. This SHALL NOT persist or publish a project flag change.

#### Scenario: Workflow disabled for current project
- **GIVEN** a session is bound to the repository root for a project where workflow tracking is disabled
- **WHEN** the workflow task starts
- **THEN** it SHALL remain inactive and create no workflow subscription

#### Scenario: Workflow enabled after project switch
- **WHEN** a project switch activates workflow tracking for the new project
- **THEN** the task SHALL subscribe using the new project's workflow configuration without an MCP restart

#### Scenario: Linked worktree receives minimum local workflow capability
- **GIVEN** a session is bound to a linked worktree for a project where workflow tracking is disabled
- **WHEN** the workflow task starts
- **THEN** it SHALL activate for that session with `discussion` and `implementation` as the minimum workflow phases
- **AND** SHALL not persist or publish workflow as enabled for the project
