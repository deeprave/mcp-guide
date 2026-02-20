## MODIFIED Requirements

### Requirement: Cache Invalidation via Timer

The system SHALL integrate with timer events for periodic cache invalidation.

#### Scenario: Invalidate cache on timer

GIVEN a timer event with interval 3600.0
WHEN the event is handled
THEN cache timestamp SHALL be set to None to invalidate cache
AND changes SHALL NOT be requested
AND event SHALL return True

#### Scenario: Cache remains invalid until requested

GIVEN cache has been invalidated by timer
AND no `:openspec/list` command has been issued
WHEN get_changes() is called
THEN None SHALL be returned
AND no data request SHALL be triggered

## REMOVED Requirements

### Requirement: Timer Integration

**Reason**: Replacing with simpler cache invalidation behavior
**Migration**: Timer now only invalidates cache instead of requesting data

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
