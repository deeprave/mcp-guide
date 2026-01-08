## ADDED Requirements

### Requirement: EventType Bitflag System
The TaskManager SHALL use EventType as a bitflag enumeration for event categorization and filtering.

#### Scenario: EventType bitflag operations
- **WHEN** subscribing to multiple event types
- **THEN** combine EventTypes using bitwise OR operations
- **AND** filtering matches using bitwise AND operations

#### Scenario: Timer event bit identification
- **WHEN** creating timer events
- **THEN** ensure all timer events have a common timer bit set
- **AND** allow additional bits for specific timer event types

### Requirement: Subscribe and Unsubscribe Interface
The TaskManager SHALL provide subscribe() and unsubscribe() methods for event registration.

#### Scenario: Event subscription with filtering
- **WHEN** a subscriber calls subscribe(callback, event_types)
- **THEN** register callback for specified EventType bitflags
- **AND** store subscription with weak reference to subscriber

#### Scenario: Timer event subscription
- **WHEN** subscribing with optional timer parameter
- **THEN** create recurring timer events at specified interval
- **AND** assign EventType with timer bit set plus optional specific bits

#### Scenario: Single unsubscribe operation
- **WHEN** calling unsubscribe(subscriber)
- **THEN** remove subscriber from both timed and non-timed events
- **AND** clean up any associated timer schedules

### Requirement: Event Dispatch with Fan-out
The TaskManager SHALL dispatch events to all matching subscribers using bitflag filtering.

#### Scenario: Event fan-out to subscribers
- **WHEN** dispatching an event with EventType
- **THEN** notify all subscribers whose registered EventTypes match using bitwise AND
- **AND** provide event_type and payload dict to each callback

#### Scenario: Multi-EventType subscriber handling
- **WHEN** a subscriber is registered for multiple EventTypes
- **THEN** receive events for any matching EventType
- **AND** callback receives the specific EventType that triggered the event

### Requirement: Timer Event Scheduling
The TaskManager SHALL provide automated timer event generation with asyncio scheduling.

#### Scenario: Timer subscription with interval
- **WHEN** subscribing with timer interval in seconds
- **THEN** create recurring timer that fires at specified intervals
- **AND** generate events with timer bit set in EventType

#### Scenario: Timer event loop management
- **WHEN** timer events are scheduled
- **THEN** maintain table of subscriber, expiry timestamp, and EventType
- **AND** use asyncio.sleep() to wait until next scheduled event

#### Scenario: Timer event recalculation
- **WHEN** timer events fire
- **THEN** recalculate next expiry time for recurring events
- **AND** update timer table with new timestamps

### Requirement: Weak Reference Subscriber Management
The TaskManager SHALL use weak references for automatic subscriber cleanup.

#### Scenario: Weak reference subscriber storage
- **WHEN** storing subscriber references
- **THEN** use weakref to prevent memory leaks
- **AND** automatically detect when subscribers are garbage collected

#### Scenario: Dead subscriber cleanup during dispatch
- **WHEN** dispatching events to subscribers
- **THEN** detect dead weak references and remove from subscription lists
- **AND** clean up associated timer schedules for dead subscribers

### Requirement: Generic Event Payload System
The TaskManager SHALL support arbitrary event payloads as dictionaries.

#### Scenario: Event payload structure
- **WHEN** dispatching events
- **THEN** provide payload as dictionary with event-specific data
- **AND** payload content is determined by EventType requirements

#### Scenario: Subscriber callback interface
- **WHEN** calling subscriber callbacks
- **THEN** provide (event_type, payload) parameters
- **AND** allow subscribers to handle multiple EventTypes in single callback

## MODIFIED Requirements

### Requirement: Task Manager Event Agnostic Design
The TaskManager SHALL operate as a simple subscribe/dispatch/unsubscribe system without knowledge of specific EventType structures.

#### Scenario: EventType agnostic operations
- **WHEN** TaskManager processes events
- **THEN** treat EventType as opaque bitflags for filtering
- **AND** do not interpret or validate EventType semantics

#### Scenario: Payload agnostic dispatch
- **WHEN** dispatching events
- **THEN** pass payload dictionaries without interpretation
- **AND** allow subscribers to define payload structure per EventType

## REMOVED Requirements

### Requirement: FSEventType Enumeration
**Reason**: Renamed to EventType for broader applicability
**Migration**: Replace FSEventType references with EventType

### Requirement: Ephemeral Interest Registration
**Reason**: Replaced by persistent pub/sub system with weak references
**Migration**: Convert register_interest() calls to subscribe() method calls
