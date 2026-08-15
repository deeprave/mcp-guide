## ADDED Requirements

### Requirement: Accurate agent prompt capability
The system SHALL represent whether each recognised agent supports prompt invocation.

#### Scenario: Unrecognised client has no prompt syntax by default
- **WHEN** the client is not recognised or does not advertise a configured prompt capability
- **THEN** its prompt prefix SHALL be `None`

#### Scenario: Cursor Agent has no prompt syntax
- **WHEN** Cursor Agent is detected
- **THEN** its prompt prefix SHALL be `None`
- **AND** rendered guidance SHALL not instruct the agent to invoke a prompt

#### Scenario: Pi has no prompt syntax
- **WHEN** Pi or a Pi MCP Guide client is detected
- **THEN** its prompt prefix SHALL be `None`
- **AND** rendered guidance SHALL not instruct the agent to invoke a prompt

### Requirement: Pi recognition
The system SHALL recognise Pi client names.

#### Scenario: Detect Pi
- **WHEN** the client name identifies Pi, including `pi-mcp-guide`
- **THEN** the system SHALL return canonical agent name `pi`
