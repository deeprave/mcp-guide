# workflow-templates Specification Delta

## MODIFIED Requirements

### Requirement: Workflow Update Messages
Workflow update messages SHALL be expressed as critical instructions that must not be ignored.

#### Scenario: Phase transition message
- WHEN a workflow phase transition occurs
- THEN the update message SHALL be prefixed with "IMPORTANT: This instruction MUST NEVER BE IGNORED."
- AND the message SHALL clearly indicate the phase change
- AND the message SHALL include any required actions

#### Scenario: Workflow state change message
- WHEN workflow state changes (e.g., issue assignment, task completion)
- THEN the update message SHALL be prefixed with "IMPORTANT: This instruction MUST NEVER BE IGNORED."
- AND the message SHALL clearly describe the state change
- AND the message SHALL guide the agent's next actions
