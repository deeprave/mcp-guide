## MODIFIED Requirements

### Requirement: Cache State Management

The system SHALL maintain cache state for an OpenSpec changes list, including
the acquisition time and the client-observed `openspec/changes` directory
modification time.

#### Scenario: Initialize cache state

GIVEN a new OpenSpecTask instance
WHEN the task is initialised
THEN changes data, timestamp, and directory modification time SHALL be unset

#### Scenario: Cache valid data

GIVEN cached changes data exists
AND its timestamp is less than one hour old
AND its cached directory modification time matches the client-observed value
WHEN get_changes() is called
THEN the cached changes list SHALL be returned

#### Scenario: Cache expired data

GIVEN cached changes data exists
AND its timestamp is at least one hour old
WHEN get_changes() is called
THEN the cached changes list SHALL become unavailable
AND a later OpenSpec-list render SHALL request a refreshed list

#### Scenario: Missing or changed directory metadata

GIVEN cached changes data exists
AND its directory modification time is missing or differs from the
client-observed value
WHEN get_changes() is called
THEN the cached changes list SHALL NOT be returned
AND a later OpenSpec-list render SHALL request a refreshed list

#### Scenario: Superseded refresh response

GIVEN a changes refresh has been superseded by a newer refresh
WHEN a directory listing or OpenSpec-list response for the older refresh arrives
THEN the system SHALL ignore that response
AND SHALL NOT associate its changes data with the newer directory modification
time

## REMOVED Requirements

### Requirement: Timer Integration

**Reason**: OpenSpec changes data is evaluated lazily by consumers using its
TTL and client-observed directory modification time. A recurring task timer
is not required.

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
