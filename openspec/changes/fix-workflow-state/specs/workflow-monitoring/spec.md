## ADDED Requirements

### Requirement: Workflow Bootstrap Guidance
The workflow monitoring system SHALL provide bootstrap guidance when workflow
tracking is enabled but no workflow state file has yet been received.

#### Scenario: Missing workflow file bootstrap
- **WHEN** workflow tracking is enabled
- **AND** the agent is instructed to provide workflow state for the first time
- **AND** the configured workflow file does not exist at the project root
- **THEN** the guidance SHALL instruct the agent to create the workflow file
- **AND** the initial content SHALL include `phase: discussion`
- **AND** the initial content SHALL include an explicit blank `issue:` line

#### Scenario: Existing workflow file bootstrap
- **WHEN** workflow tracking is enabled
- **AND** the configured workflow file already exists
- **THEN** the guidance SHALL instruct the agent to send the complete contents
  of that file
- **AND** it SHALL NOT instruct the agent to create a replacement file
