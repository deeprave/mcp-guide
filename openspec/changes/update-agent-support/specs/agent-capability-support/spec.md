## ADDED Requirements

### Requirement: Accurate agent prompt capability
The system SHALL represent whether each recognised agent supports prompt invocation.

#### Scenario: Cursor Agent has no prompt syntax
- **WHEN** Cursor Agent is detected
- **THEN** its prompt prefix SHALL be `None`
- **AND** rendered guidance SHALL not instruct the agent to invoke a prompt

### Requirement: Aider recognition
The system SHALL recognise Aider client names and apply its configured project integration behavior.

#### Scenario: Detect Aider
- **WHEN** the client name identifies Aider
- **THEN** the system SHALL return canonical agent name `aider`
- **AND** SHALL select Aider-specific supported conventions when configured
