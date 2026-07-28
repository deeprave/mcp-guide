## MODIFIED Requirements

### Requirement: Workflow Status Display
The system SHALL update status command to show workflow information when enabled.

#### Scenario: Status with workflow tracking enabled
- **WHEN** user runs `:status` command and `workflow` flag is configured
- **THEN** display current phase, active issue, and queued issues from workflow state file

#### Scenario: Status with workflow tracking disabled
- **WHEN** user runs `:status` command and `workflow` flag is false
- **THEN** display basic project information without workflow details
- **AND** it SHALL NOT instruct the agent to send workflow file content
- **AND** it SHALL NOT imply that workflow monitoring is currently active

#### Scenario: Status with workflow enabled but state unavailable
- **WHEN** user runs `:status` command and workflow tracking is enabled
- **AND** no workflow state has yet been received
- **THEN** status output SHALL state that workflow state is not yet available
- **AND** it SHALL include setup guidance for providing workflow state
- **AND** that guidance SHALL appear only in the workflow-enabled case
