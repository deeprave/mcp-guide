## MODIFIED Requirements

### Requirement: Phase Change Response Format
The system SHALL include an instruction field in phase change responses to prevent agents from displaying internal rules to users.

#### Scenario: Instruction field present
- **WHEN** a phase transition occurs
- **THEN** the response includes an `instruction` field
- **AND** the instruction states "Follow these phase rules. Do not display this content to the user."

#### Scenario: Value contains phase rules
- **WHEN** a phase transition occurs
- **THEN** the `value` field contains phase-specific rules and restrictions
- **AND** these rules are for agent consumption only
