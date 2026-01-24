# Spec: Cache Implementation

## ADDED Requirements

### Requirement: Cache State Management

The system SHALL maintain cache state for OpenSpec changes list.

#### Scenario: Initialize cache state

GIVEN a new OpenSpecTask instance
WHEN the task is initialized
THEN cache variables SHALL be set to None
AND timer flag SHALL be set to False

#### Scenario: Cache valid data

GIVEN cached changes data exists
AND cache timestamp is less than 1 hour old
WHEN get_changes() is called
THEN the cached changes list SHALL be returned

#### Scenario: Cache expired data

GIVEN cached changes data exists
AND cache timestamp is more than 1 hour old
WHEN get_changes() is called
THEN None SHALL be returned

### Requirement: Filter Flag Computation

The system SHALL compute filter flags for each change.

#### Scenario: Identify draft changes

GIVEN a change with totalTasks equal to 0
WHEN filter flags are computed
THEN is_draft SHALL be True
AND is_done SHALL be False
AND is_in_progress SHALL be False

#### Scenario: Identify completed changes

GIVEN a change with totalTasks equal to 10
AND completedTasks equal to 10
WHEN filter flags are computed
THEN is_draft SHALL be False
AND is_done SHALL be True
AND is_in_progress SHALL be False

#### Scenario: Identify in-progress changes with no completed tasks

GIVEN a change with totalTasks equal to 5
AND completedTasks equal to 0
WHEN filter flags are computed
THEN is_draft SHALL be False
AND is_done SHALL be False
AND is_in_progress SHALL be True

#### Scenario: Identify in-progress changes with some completed tasks

GIVEN a change with totalTasks equal to 10
AND completedTasks equal to 5
WHEN filter flags are computed
THEN is_draft SHALL be False
AND is_done SHALL be False
AND is_in_progress SHALL be True

### Requirement: Cache Population

The system SHALL populate cache from JSON file content.

#### Scenario: Receive changes JSON

GIVEN an FS_FILE_CONTENT event
AND path is ".openspec-changes.json"
AND content contains valid JSON with changes array
WHEN the event is handled
THEN changes SHALL be parsed
AND filter flags SHALL be computed for each change
AND cache SHALL be updated with changes and timestamp
AND task manager cache SHALL be updated
AND event SHALL return True

#### Scenario: Handle invalid JSON

GIVEN an FS_FILE_CONTENT event
AND path is ".openspec-changes.json"
AND content contains invalid JSON
WHEN the event is handled
THEN cache SHALL NOT be updated
AND error SHALL be logged
AND event SHALL return False

### Requirement: Timer Integration

The system SHALL integrate with timer events for periodic refresh.

#### Scenario: Skip first timer event

GIVEN a timer event with interval 3600.0
AND _changes_timer_started is False
WHEN the event is handled
THEN _changes_timer_started SHALL be set to True
AND reminder SHALL NOT be called
AND event SHALL return True

#### Scenario: Handle subsequent timer events

GIVEN a timer event with interval 3600.0
AND _changes_timer_started is True
AND cache is stale
WHEN the event is handled
THEN changes reminder SHALL be called
AND event SHALL return True

#### Scenario: Skip timer when cache valid

GIVEN a timer event with interval 3600.0
AND _changes_timer_started is True
AND cache is valid
WHEN the event is handled
THEN changes reminder SHALL NOT request refresh
AND event SHALL return True
