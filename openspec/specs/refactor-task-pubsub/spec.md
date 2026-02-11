# refactor-task-pubsub Specification

## Purpose
TBD - created by archiving change project-status. Update Purpose after archive.
## Requirements
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

#### Scenario: Subscribe to events
- **WHEN** a task calls subscribe(subscriber, event_types)
- **THEN** register the subscriber for the specified event types
- **AND** return a subscription handle

#### Scenario: Unsubscribe from events
- **WHEN** a task calls unsubscribe(subscriber, event_types)
- **THEN** remove the subscriber from the specified event types
- **AND** clean up any associated resources

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

### Requirement: Instruction Acknowledgement Tracking
The TaskManager SHALL provide acknowledgement-based instruction tracking with automatic retry.

#### Scenario: Queue instruction with acknowledgement
- **WHEN** a task calls queue_instruction_with_ack(content, max_retries)
- **THEN** return a unique instruction ID for tracking
- **AND** add instruction to pending queue
- **AND** store instruction metadata for retry tracking

#### Scenario: Acknowledge instruction receipt
- **WHEN** a task calls acknowledge_instruction(instruction_id)
- **THEN** remove instruction from tracking
- **AND** prevent further retries of that instruction

#### Scenario: Deduplicate identical instructions
- **WHEN** queue_instruction_with_ack() is called with content already tracked
- **THEN** return existing instruction ID
- **AND** do not add duplicate to queue

### Requirement: Automatic Instruction Retry
The TaskManager SHALL automatically retry unacknowledged instructions during idle periods.

#### Scenario: Retry during idle state
- **WHEN** RetryTask timer fires and instruction queue is empty
- **THEN** requeue all unacknowledged instructions that have been waiting at least 30 seconds
- **AND** increment retry counter for each instruction

#### Scenario: Skip retry when queue active
- **WHEN** RetryTask timer fires and instruction queue is not empty
- **THEN** do not retry any instructions
- **AND** wait for next timer interval

#### Scenario: Skip retry when instruction too recent
- **WHEN** RetryTask checks unacknowledged instruction
- **AND** instruction was sent less than 30 seconds ago
- **THEN** do not retry that instruction
- **AND** wait for next timer interval

#### Scenario: Escalate instruction urgency
- **WHEN** retrying an instruction for the 2nd time
- **THEN** prefix content with "**IMPORTANT:** "
- **WHEN** retrying an instruction for the 3rd+ time
- **THEN** prefix content with "**URGENT:** "

#### Scenario: Give up after max retries
- **WHEN** an instruction reaches max_retries without acknowledgement
- **THEN** remove from tracking
- **AND** log warning with instruction content
- **AND** do not retry again

### Requirement: RetryTask Timer Monitoring
The TaskManager SHALL provide a RetryTask that monitors for unacknowledged instructions.

#### Scenario: RetryTask initialization
- **WHEN** TaskManager initializes
- **THEN** create RetryTask with 60-second timer interval
- **AND** subscribe to timer events

#### Scenario: RetryTask idle detection
- **WHEN** RetryTask receives timer event
- **THEN** check if instruction queue is empty
- **AND** trigger retry_unacknowledged() if idle

