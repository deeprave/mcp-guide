# cache-management Specification

## Purpose
Define cached OpenSpec change discovery and its invalidation behaviour.
## Requirements
### Requirement: Cache State Management

The system SHALL maintain cache state for an OpenSpec changes list, including its acquisition time and refresh generation. Cache validity SHALL be determined by its TTL or an explicit refresh, not client-observed filesystem metadata.

#### Scenario: Initialize cache state

- **GIVEN** a new OpenSpecTask instance
- **WHEN** the task is initialised
- **THEN** changes data, timestamp, and refresh generation SHALL be unset

#### Scenario: Cache valid data

- **GIVEN** cached changes data exists
- **AND** its timestamp is less than one hour old
- **WHEN** get_changes() is called
- **THEN** the cached changes list SHALL be returned

#### Scenario: Cache expired data

- **GIVEN** cached changes data exists
- **AND** its timestamp is at least one hour old
- **WHEN** get_changes() is called
- **THEN** the cached changes list SHALL become unavailable
- **AND** a later OpenSpec-list render SHALL request a refreshed list

#### Scenario: Missing or changed directory metadata

- **GIVEN** cached changes data exists and client directory metadata is absent or changes
- **WHEN** a consumer requests a forced refresh
- **THEN** the OpenSpec-list render SHALL request a new OpenSpec-list result
- **AND** SHALL not inspect or request a changes-directory modification time

#### Scenario: Dispatch a mutation-capable OpenSpec command

- **GIVEN** cached OpenSpec command results exist
- **WHEN** Guide dispatches a command or skill that may mutate OpenSpec state
- **THEN** Guide SHALL invalidate the relevant cached OpenSpec results
- **AND** SHALL NOT automatically request replacement CLI data

#### Scenario: Superseded refresh response

- **GIVEN** a changes refresh has been superseded by a newer refresh
- **WHEN** an OpenSpec-list response for the older refresh arrives
- **THEN** the system SHALL ignore that response
- **AND** SHALL NOT associate its changes data with the newer refresh generation

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
