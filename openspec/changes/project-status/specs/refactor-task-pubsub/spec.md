## ADDED Requirements

### Requirement: Task Event System
The TaskManager SHALL implement a pub/sub event system to replace ephemeral interest registration, enabling persistent monitoring of file events.

#### Scenario: Persistent event subscription
- **WHEN** a workflow task subscribes to file events
- **THEN** the subscription persists until the task completes
- **AND** multiple events can be received without re-registration

#### Scenario: Automatic cleanup via weak references
- **WHEN** a task is garbage collected
- **THEN** its event listeners are automatically removed during next dispatch
- **AND** no memory leaks occur from orphaned listeners

### Requirement: TaskEvent Data Structure
The system SHALL provide a TaskEvent class to encapsulate event information.

#### Scenario: Event data encapsulation
- **WHEN** an event is dispatched
- **THEN** it contains event_type and event_data fields
- **AND** event_data is a dictionary of arbitrary key-value pairs

### Requirement: EventListener with WeakRef
The system SHALL implement EventListener using weak references to prevent memory leaks.

#### Scenario: Weak reference cleanup
- **WHEN** a task is no longer referenced
- **THEN** the EventListener can detect this via weak reference
- **AND** returns None when attempting to get the task

### Requirement: Event Dispatch with Cleanup
The TaskManager SHALL automatically clean up dead listeners during event dispatch.

#### Scenario: Dead listener removal
- **WHEN** dispatching events to listeners
- **THEN** listeners with dead task references are identified
- **AND** dead listeners are removed from the subscription list

## MODIFIED Requirements

### Requirement: Task Interest Registration
The TaskManager SHALL replace register_interest() with subscribe_to_event() for persistent subscriptions.

#### Scenario: Subscription-based interest
- **WHEN** a task needs to monitor events
- **THEN** it calls subscribe_to_event() instead of register_interest()
- **AND** the subscription remains active until task completion

## REMOVED Requirements

### Requirement: Ephemeral Interest Expiration
**Reason**: Replaced by persistent pub/sub system
**Migration**: Convert register_interest() calls to subscribe_to_event()
