# workflow-monitoring Specification

## Purpose
TBD - created by archiving change semantic-workflow-change-detection. Update Purpose after archive.
## Requirements
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

### Requirement: Phase Rule Inclusion
The system SHALL include relevant phase rules when phase transitions are detected.

#### Scenario: Phase rule discovery
- **WHEN** a phase transition is detected to "review" phase
- **THEN** system SHALL discover the review phase template using glob pattern "*review"
- **AND** system SHALL render and include the phase rules in the response

#### Scenario: Phase rule content
- **WHEN** phase rules are included in response
- **THEN** rules SHALL provide clear guidance on what actions are allowed in the new phase
- **AND** rules SHALL address common misconceptions about phase restrictions

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
The workflow monitoring task SHALL process workflow file content by comparing against previous state and generating semantic change responses.

#### Scenario: Content processing workflow
- **WHEN** workflow file content is received
- **THEN** system SHALL parse the new content into workflow state
- **AND** system SHALL compare against cached previous state (if available)
- **AND** system SHALL generate appropriate change events based on differences
- **AND** system SHALL queue contextual instructions based on change types
- **AND** system SHALL update cached state only after processing changes

#### Scenario: Error handling during comparison
- **WHEN** workflow content parsing or comparison fails
- **THEN** system SHALL log appropriate warnings
- **AND** system SHALL not update cached state
- **AND** system SHALL not queue potentially incorrect change instructions

