## ADDED Requirements

### Requirement: Direct workflow-state source
The workflow monitoring system SHALL use a confirmed direct filesystem source when available without changing its semantic change-detection behavior.

#### Scenario: Confirmed workflow file read
- **WHEN** workflow monitoring is enabled and direct filesystem access is confirmed
- **THEN** the monitor SHALL read and parse the configured workflow file directly
- **AND** SHALL compare it with the cached workflow state
- **AND** SHALL emit the same semantic change guidance as for relayed content

#### Scenario: Unconfirmed or failed direct source
- **WHEN** workflow monitoring lacks confirmed direct access or its direct read fails
- **THEN** the monitor SHALL preserve its existing relay-based workflow-file behavior

### Requirement: Workflow relay suppression
The workflow monitoring system SHALL not queue workflow-file relay setup or reminder instructions after it has successfully obtained workflow state through confirmed direct access.

#### Scenario: Confirmed initial workflow state
- **WHEN** a confirmed session has loaded current workflow state directly
- **THEN** workflow monitoring SHALL not instruct the agent to send the workflow file content
