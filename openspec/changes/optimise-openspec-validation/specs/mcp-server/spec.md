## MODIFIED Requirements

### Requirement: OpenSpec Project Validation
The system SHALL validate OpenSpec availability once and never repeat validation.

#### Scenario: One-time validation
- **WHEN** OpenSpec feature is enabled for the first time
- **THEN** check `openspec/project.md` exists (do not read content)
- **AND** check OpenSpec command exists
- **AND** set validation flag to true
- **AND** never validate again while flag is true

#### Scenario: Skip validated checks
- **WHEN** validation flag is true
- **THEN** skip all OpenSpec validation checks
- **AND** do not request file existence or command location
