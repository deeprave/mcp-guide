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

## REMOVED Requirements

### Requirement: Unified Session Access
**Reason**: Ambient `get_session(ctx=None, ...)` is deleted. Known ids are looked up through `GuideRuntime.get_current_session`; minting is `GuideRuntime.create_session` only from PWD bind or `set_project` when unbound.
**Migration**: Pass RequestContext or Session explicitly. Do not select a Session from a ContextVar.

## MODIFIED Requirements

### Requirement: Session Non-Singleton
The system SHALL implement Session as a non-singleton class. One Session exists per
client interaction owner. HTTP concurrent clients SHALL NOT share a Session.

Each Session instance SHALL own its own listener list and manage listener registration
as instance methods (`add_listener`, `remove_listener`, `clear_listeners`).

Listeners SHALL NOT be shared across Session instances.

Each Session instance SHALL be allowed to exist before its real project is bound.
Before binding, `Session.project` SHALL be `None` rather than a placeholder project
object.

When no project is bound, the session SHALL still provide sufficient context for
`_system/` template rendering: agent info, client info, and global feature flags
SHALL be accessible without a bound project.

#### Scenario: Session creation before project binding
- **WHEN** a Session is created before client project context is available
- **THEN** a Session instance is created without ambient ContextVar storage
- **AND** `Session.project` is `None`
- **AND** the session does not require a real `Project` constructor argument at creation time
- **AND** no persisted project config is loaded yet

#### Scenario: Unbound session rejects bound-only operations
- **WHEN** code calls a project operation that requires a real persisted project
- **THEN** the Session SHALL raise `NoProjectError`, or allow an existing `NoProjectError` path to bubble
- **AND** it SHALL NOT silently invent or persist project data

#### Scenario: Unbound placeholder rejects bound-only operations
- **WHEN** code calls a project operation that requires a real persisted project
- **THEN** the Session SHALL raise `NoProjectError`, or allow an existing `NoProjectError` path to bubble
- **AND** it SHALL NOT silently invent or persist project data
- **AND** there is no placeholder project object on `Session.project`

#### Scenario: Session creation with immediate project context
- **WHEN** a bind operation resolves project identity immediately
- **THEN** a Session is created or reused for that owner
- **AND** the real project is bound during that bind
- **AND** later requests with the same session_id receive the same retained Session

#### Scenario: Unbound session exposes agent and client info for template rendering
- **WHEN** a session exists with no bound project
- **AND** agent bootstrap data has been received
- **THEN** `session.agent_info` SHALL be accessible
- **AND** `get_template_contexts()` SHALL return a context including `agent.*` and `client.*`
- **AND** template rendering of `_system/` templates SHALL succeed

