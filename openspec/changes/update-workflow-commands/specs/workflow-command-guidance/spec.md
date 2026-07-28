## ADDED Requirements

### Requirement: General workflow command availability
The system SHALL make workflow phase commands available when workflow support is disabled.

#### Scenario: Invoke a phase command without workflow
- **WHEN** workflow is disabled and a user invokes a workflow phase command
- **THEN** the command SHALL render general principles for that phase
- **AND** SHALL not mention unavailable workflow state or Guide-specific workflow actions

### Requirement: Workflow add-in guidance
The system SHALL append workflow-specific guidance only when workflow is enabled and the referenced state is available.

#### Scenario: Invoke a phase command with workflow
- **WHEN** workflow is enabled and a user invokes a workflow phase command
- **THEN** the command SHALL include its general principles
- **AND** SHALL include applicable workflow state and transition guidance as an add-in section
