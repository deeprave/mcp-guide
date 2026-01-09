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

### Requirement: TaskSubscriber Protocol Interface
The TaskManager SHALL use a protocol-based interface for type-safe event handling.

#### Scenario: Protocol-based subscription
- **WHEN** a subscriber calls subscribe(subscriber, event_types)
- **THEN** register TaskSubscriber protocol implementer for specified EventType bitflags
- **AND** store subscription with weak reference to subscriber

#### Scenario: Protocol event handling
- **WHEN** dispatching events to subscribers
- **THEN** call subscriber.handle_event(event_type, data) method
- **AND** ensure type safety through protocol runtime checking

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

#### Scenario: Protocol-based event delivery
- **WHEN** dispatching an event with EventType
- **THEN** notify all subscribers whose registered EventTypes match using bitwise AND
- **AND** call subscriber.handle_event(event_type, payload) method

#### Scenario: Multi-EventType protocol handling
- **WHEN** a subscriber is registered for multiple EventTypes
- **THEN** receive events for any matching EventType
- **AND** handle_event receives the specific EventType that triggered the event

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

#### Scenario: Protocol-based payload handling
- **WHEN** dispatching events
- **THEN** provide payload as dictionary with event-specific data
- **AND** payload content is determined by EventType requirements

#### Scenario: TaskSubscriber protocol interface
- **WHEN** calling subscriber handle_event method
- **THEN** provide (event_type, payload) parameters via protocol
- **AND** allow subscribers to handle multiple EventTypes in single implementation

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

### Requirement: Callback Function Interface
**Reason**: Replaced by TaskSubscriber protocol for type safety
**Migration**: Convert callback functions to TaskSubscriber protocol implementations

### Requirement: Gradual Migration with Compatibility Layer
**Reason**: Chose complete migration for cleaner architecture
**Migration**: Direct replacement of register_interest() with subscribe() calls

## IMPLEMENTATION STATUS

### COMPLETED ✅
- EventType Bitflag System - Fully implemented with bitwise operations
- Subscribe/Unsubscribe Interface - Implemented with TaskSubscriber protocol (MODIFIED)
- Event Dispatch with Fan-out - Fully implemented with bitflag filtering
- Weak Reference Subscriber Management - Fully implemented with automatic cleanup
- Generic Event Payload System - Fully implemented with protocol-based callbacks
- Legacy Code Migration - register_interest() removed, WorkflowMonitorTask updated
- Timer Event Scheduling - Fully implemented with asyncio timer loop
- Timer subscription with intervals - Implemented with unique timer bits
- Timer event loop management - Implemented with asyncio sleep scheduling
- Timer event recalculation - Implemented with recurring timer updates

### NOT IMPLEMENTED ❌
- None - All planned functionality has been implemented

### IMPLEMENTATION VARIATIONS
- **TaskSubscriber Protocol**: Instead of callback functions, implemented protocol-based event handling with handle_event() method
- **Simplified Interface**: subscribe(subscriber: TaskSubscriber, event_types, timer_interval=None) instead of callback-based approach
- **Protocol Runtime Checking**: Added @runtime_checkable for isinstance() validation
- **Type Safety**: Full mypy compliance with strongly-typed interfaces
