## ADDED Requirements

### Requirement: Workflow Phase Permission Markers
The workflow system SHALL support explicit permission markers in phase definitions to control when user consent is required for phase transitions.

#### Scenario: Preceding asterisk requires entry permission
- **WHEN** a workflow phase is defined with a preceding asterisk (e.g., "*implementation")
- **THEN** explicit user consent, request, or confirmation SHALL be required to enter that phase

#### Scenario: Trailing asterisk requires exit permission
- **WHEN** a workflow phase is defined with a trailing asterisk (e.g., "review*")
- **THEN** explicit user consent, request, or confirmation SHALL be required to leave that phase

#### Scenario: Both asterisks require entry and exit permission
- **WHEN** a workflow phase is defined with both preceding and trailing asterisks (e.g., "*implementation*")
- **THEN** explicit user consent SHALL be required for both entering and leaving that phase

#### Scenario: No asterisk allows automatic transition
- **WHEN** a workflow phase is defined without asterisks (e.g., "planning")
- **THEN** agents MAY transition to and from that phase automatically based on workflow logic

### Requirement: Workflow Transitions Template Variable
The template system SHALL provide a workflow.transitions variable containing permission metadata for all workflow phases.

#### Scenario: Template access to transition metadata
- **WHEN** rendering workflow templates
- **THEN** the workflow.transitions variable SHALL be available containing phase permission settings

#### Scenario: Transition metadata structure
- **WHEN** accessing workflow.transitions[phase_name]
- **THEN** it SHALL contain:
  - `default`: boolean indicating if this is the starting phase
  - `pre`: boolean indicating if explicit consent required to enter
  - `post`: boolean indicating if explicit consent required to leave

#### Scenario: Permission inheritance rules
- **WHEN** transitioning from a phase ending with "*" to a phase starting with "*"
- **THEN** explicit consent for the second phase SHALL be assumed satisfied by the first

### Requirement: Default Workflow Permission Configuration
The system SHALL provide a default workflow configuration with appropriate permission controls for standard development phases.

#### Scenario: Default workflow phases and permissions
- **WHEN** no custom workflow is configured
- **THEN** the default workflow SHALL be: [discussion, planning, *implementation, check, review*]
- **AND** implementation SHALL require explicit consent to enter
- **AND** review SHALL require explicit consent to leave

#### Scenario: Minimal workflow support
- **WHEN** a minimal workflow is configured
- **THEN** it SHALL support [discussion, implementation] as the simplest valid workflow
- **AND** discussion SHALL be the required starting phase
- **AND** implementation SHALL be a required phase

### Requirement: Custom Workflow Permission Configuration
The system SHALL support custom workflow configurations with user-defined permission markers while maintaining required phases.

#### Scenario: Custom workflow with permission markers
- **WHEN** a custom workflow is defined with permission markers
- **THEN** the permission markers SHALL be parsed and applied to transition logic
- **AND** the workflow.transitions variable SHALL reflect the custom configuration

#### Scenario: Required phase validation
- **WHEN** validating a custom workflow configuration
- **THEN** it MUST include a discussion phase (starting phase)
- **AND** it MUST include an implementation phase
- **AND** other phases (planning, check, review) SHALL be optional
