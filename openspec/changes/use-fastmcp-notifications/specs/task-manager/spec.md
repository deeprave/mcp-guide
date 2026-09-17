## ADDED Requirements

### Requirement: Notification-aware instruction state
The task manager SHALL preserve each queued instruction's owner, project
identity, tracking state, and acknowledgement semantics until notification
delivery succeeds for the owning modern Session or legacy result delivery occurs.

#### Scenario: Modern notification delivery succeeds
- **WHEN** a queued instruction is delivered by a notification to its owning
  modern Session
- **THEN** the task manager SHALL mark the instruction as dispatched
- **AND** SHALL preserve its tracking and acknowledgement state where applicable

#### Scenario: Modern notification delivery is deferred
- **WHEN** the owning modern Session has no usable request stream
- **THEN** the task manager SHALL retain the instruction as pending
- **AND** SHALL not dequeue it for another Session or project

#### Scenario: Legacy result delivery succeeds
- **WHEN** a queued instruction is attached to a legacy response for its owning
  Session
- **THEN** the task manager SHALL preserve the existing result-delivery and
  tracking behaviour
