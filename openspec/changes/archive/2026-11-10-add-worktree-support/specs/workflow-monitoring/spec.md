## MODIFIED Requirements

### Requirement: Workflow state-file validation

The monitor SHALL parse a configured workflow state file as a YAML mapping and accept state whose phase is a recognised workflow phase. The effective, normalised workflow flag controls the configured guidance sequence but SHALL NOT make another recognised phase invalid.

#### Scenario: Valid workflow state

- **WHEN** the configured workflow file supplies a mapping with a phase in the effective workflow configuration
- **THEN** the monitor accepts its phase, issue, queue, and description values

#### Scenario: Recognised phase outside configured sequence

- **GIVEN** `planning` is a recognised workflow phase but is absent from the effective workflow configuration
- **WHEN** the configured workflow file supplies `phase: planning`
- **THEN** the monitor accepts the workflow state

### Requirement: Invalid workflow submission handling

Invalid workflow content SHALL return a clear failure and SHALL neither replace cached state nor be acknowledged as successfully received. Invalid content includes malformed YAML, a non-mapping, an omitted phase, an unknown phase, or an invalid field type; it does not include a recognised phase that is absent from the configured sequence.

#### Scenario: Invalid workflow-file submission

- **WHEN** submitted workflow content is invalid
- **THEN** the task returns a failure without replacing cached state

#### Scenario: Content processing workflow

- **WHEN** workflow file content is received
- **THEN** system SHALL parse the new content into workflow state
- **AND** system SHALL compare against cached previous state (if available)
- **AND** system SHALL generate appropriate change events based on differences
- **AND** system SHALL update cached state only after processing changes

#### Scenario: Invalid workflow-file submission

- **WHEN** submitted workflow file content is invalid YAML, is not a mapping, omits `phase`, names an unknown phase, or has a field with an invalid schema type
- **THEN** the file-content operation SHALL return a failure identifying the invalid workflow file
- **AND** the system SHALL NOT cache submitted state
- **AND** the system SHALL NOT acknowledge the submission as successfully received
- **AND** an unknown phase error SHALL identify the recognised phase choices

#### Scenario: Error handling during comparison

- **WHEN** workflow content parsing or comparison fails
- **THEN** system SHALL log appropriate warnings
- **AND** system SHALL not update cached state
- **AND** system SHALL not queue potentially incorrect change instructions
