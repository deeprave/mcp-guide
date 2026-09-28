# Spec Delta

## MODIFIED Requirements

### Requirement: Workflow Status Display
The system SHALL update status command to show workflow information when enabled.
The template context SHALL expose the established session protocol classification
as `client.protocol` alongside other client-information fields.

#### Scenario: Status with workflow tracking enabled
- **WHEN** user runs `:status` command and `workflow` flag is configured
- **THEN** display current phase, active issue, and queued issues from workflow state file
- **AND** display the connected session's MCP `2026-07-28` or `legacy` protocol
  classification

#### Scenario: Status with workflow tracking disabled
- **WHEN** user runs `:status` command and `workflow` flag is false
- **THEN** display basic project information without workflow details
- **AND** display the connected session's MCP `2026-07-28` or `legacy` protocol
  classification
- **AND** it SHALL NOT instruct the agent to send workflow file content
- **AND** it SHALL NOT imply that workflow monitoring is active

#### Scenario: Status with workflow enabled but state unavailable
- **WHEN** user runs `:status` command and workflow tracking is enabled
- **AND** no workflow state has yet been received
- **THEN** status output SHALL state that workflow state is not yet available
- **AND** SHALL include setup guidance only for the workflow-enabled case
- **AND** SHALL display the connected session's protocol classification
