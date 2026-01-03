## ADDED Requirements

### Requirement: Workflow Template Context
The system SHALL provide workflow-related variables in template context when workflow tracking is enabled.

#### Scenario: Current workflow phase
- **WHEN** rendering templates with workflow tracking enabled
- **THEN** include `workflow_phase` variable with current phase name

#### Scenario: Next workflow phase
- **WHEN** rendering templates with workflow tracking enabled
- **THEN** include `workflow_next` variable with next phase based on list order

#### Scenario: Workflow file path
- **WHEN** rendering templates with workflow tracking enabled
- **THEN** include `workflow_file` variable with workflow state file name/path

#### Scenario: Current workflow task
- **WHEN** rendering templates with workflow tracking enabled
- **THEN** include `workflow_task` variable with current issue name

#### Scenario: Workflow task description
- **WHEN** rendering templates with workflow tracking enabled
- **THEN** include `workflow_description` variable with task description (may be blank)

### Requirement: Workflow Status Display
The system SHALL update status command to show workflow information when enabled.

#### Scenario: Status with workflow tracking enabled
- **WHEN** user runs `:status` command and `workflow` flag is configured
- **THEN** display current phase, active issue, and queued issues from workflow state file

#### Scenario: Status with workflow tracking disabled
- **WHEN** user runs `:status` command and `workflow` flag is false
- **THEN** display basic project information without workflow details
