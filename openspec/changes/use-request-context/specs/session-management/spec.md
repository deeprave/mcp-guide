## ADDED Requirements

### Requirement: Explicit Session and Project Propagation
The system SHALL pass the resolved RequestContext, Session, or Project explicitly
between application operations. Ambient ContextVar state SHALL NOT select a Session,
Project, TaskManager, root binding, or active configuration for a production request.

#### Scenario: Internal operation needs a Session
- **WHEN** an internal operation needs interaction-owned state
- **THEN** its caller SHALL supply the resolved RequestContext or Session explicitly
- **AND** the operation SHALL fail clearly if neither is supplied
- **AND** it SHALL NOT create an unbound replacement Session or use ambient fallback state

#### Scenario: Concurrent interactions invoke nested operations
- **WHEN** two interactions execute nested application operations concurrently
- **THEN** each operation SHALL retain the Session and Project supplied by its own RequestContext
- **AND** no operation SHALL obtain the other interaction's state through task-local ambient storage

