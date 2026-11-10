# workflow-monitoring Specification

## Purpose
Define monitoring and semantic change detection for project workflow files.

## Requirements

### Requirement: Project-scoped workflow task activation
The workflow monitoring task SHALL activate from the current project context rather than import-time initialization.

#### Scenario: Workflow disabled for current project
- **WHEN** the workflow task starts for a project where workflow tracking is disabled
- **THEN** it SHALL remain inactive and create no workflow subscription

#### Scenario: Workflow enabled after project switch
- **WHEN** a project switch activates workflow tracking for the new project
- **THEN** the task SHALL subscribe using the new project's workflow configuration without an MCP restart

### Requirement: Workflow state-file validation

The monitor SHALL parse a configured workflow state file as a YAML mapping and accept state whose phase is a recognised workflow phase. The effective, normalised workflow flag controls the configured guidance sequence but SHALL NOT make another recognised phase invalid.

#### Scenario: Valid workflow state

- **WHEN** the configured workflow file supplies a mapping with a phase in the effective workflow configuration
- **THEN** the monitor accepts its phase, issue, queue, and description values

#### Scenario: Recognised phase outside configured sequence

- **GIVEN** `planning` is a recognised workflow phase but is absent from the effective workflow configuration
- **WHEN** the configured workflow file supplies `phase: planning`
- **THEN** the monitor accepts the workflow state

### Requirement: Semantic Workflow Change Detection
The workflow monitoring system SHALL detect and report semantic changes in workflow state rather than echoing redundant content.

#### Scenario: Phase transition detected
- **WHEN** workflow file content changes the phase from "discussion" to "planning"
- **THEN** system SHALL generate a phase transition event with from/to information
- **AND** system SHALL include the planning phase rules in the response

#### Scenario: Issue change detected
- **WHEN** workflow file content changes the issue field
- **THEN** system SHALL generate an issue change event with previous and new values
- **AND** system SHALL handle cleared issues (changed to empty/null)

#### Scenario: Multiple changes in single update
- **WHEN** workflow file content changes multiple fields (phase, issue, description)
- **THEN** system SHALL detect and report all changes in a single response
- **AND** system SHALL prioritize phase transition rules if phase changed

### Requirement: Workflow State Comparison
The system SHALL compare new workflow state against cached previous state to identify specific changes.

#### Scenario: First startup with no cached state
- **WHEN** workflow monitoring starts with no previous cached state
- **THEN** system SHALL process the current state without "from" values
- **AND** system SHALL cache the initial state for future comparisons

#### Scenario: State comparison with cached data
- **WHEN** new workflow content is received and previous state exists
- **THEN** system SHALL compare new state against cached state
- **AND** system SHALL update cache only after generating change events

### Requirement: Change Event Types
The system SHALL support detection of the following change types with from/to context.

#### Scenario: Queue change detection
- **WHEN** items are added or removed from the workflow queue
- **THEN** system SHALL generate queue change events with added/removed items
- **AND** system SHALL preserve queue order information

#### Scenario: Tracking field changes
- **WHEN** the tracking field is modified or cleared
- **THEN** system SHALL generate tracking change events with previous and new values
- **AND** system SHALL handle both additions and removals of tracking data

#### Scenario: Description changes
- **WHEN** the description field is added, modified, or removed
- **THEN** system SHALL generate description change events
- **AND** system SHALL indicate whether description was added, changed, or cleared

### Requirement: Workflow Content Processing
The workflow monitoring task SHALL compare valid workflow state against cached
previous state and generate semantic change responses.

#### Scenario: Valid workflow state is compared
- **WHEN** submitted workflow content parses to valid state
- **THEN** the task compares it with cached state before generating a response

### Requirement: Workflow state cache update boundary

The task SHALL update cached workflow state only after processing valid changes.

#### Scenario: Valid workflow state is cached after processing
- **WHEN** a valid workflow change has been processed
- **THEN** the task updates its cached workflow state

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
