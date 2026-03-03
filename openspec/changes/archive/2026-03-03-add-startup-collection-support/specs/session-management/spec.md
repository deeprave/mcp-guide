# session-management Specification Delta

## MODIFIED Requirements

### Requirement: Session Listener Protocol
The system SHALL use a class-level listener pattern for session events.

#### Scenario: Protocol signature change
- **WHEN** implementing session listeners
- **THEN** `SessionListener` protocol methods SHALL receive `Session` instance
- **AND** `on_session_changed(self, session: Session) -> None`
- **AND** `on_config_changed(self, session: Session) -> None`
- **AND** listeners extract `project_name` from `session.project_name` if needed

#### Scenario: Class-level listener storage
- **WHEN** managing session listeners
- **THEN** `Session._listeners` SHALL be a class variable (ClassVar)
- **AND** all `Session` instances share the same listener list
- **AND** listeners are registered once at server startup
- **AND** listeners receive events from all session instances

#### Scenario: Listener notification with session
- **WHEN** notifying listeners of session changes
- **THEN** pass `self` (Session instance) to listener methods
- **AND** `listener.on_session_changed(self)` instead of `listener.on_session_changed(self.project_name)`
- **AND** `listener.on_config_changed(self)` instead of `listener.on_config_changed(self.project_name)`

#### Scenario: Existing listener refactoring
- **WHEN** updating existing listeners
- **THEN** `TemplateContextCache.on_session_changed()` SHALL accept `Session` parameter
- **AND** `TemplateContextCache.on_config_changed()` SHALL accept `Session` parameter
- **AND** extract `project_name` from session if needed for logging

## ADDED Requirements

### Requirement: Startup Instruction Listener
The system SHALL implement a class-level session listener to handle startup instruction rendering.

#### Scenario: Listener implementation
- **WHEN** implementing startup instruction support
- **THEN** create `StartupInstructionListener` class implementing `SessionListener` protocol
- **AND** listener SHALL respond to `on_session_changed()` events
- **AND** listener SHALL be registered once at server startup in `create_server()`
- **AND** listener receives events from all session instances

#### Scenario: Listener registration
- **WHEN** server starts
- **THEN** instantiate `StartupInstructionListener`
- **AND** register it via `Session.add_listener(startup_listener)` (class method)
- **AND** listener SHALL be notified for all session change events

### Requirement: Startup Instruction Template
The system SHALL render and queue a startup instruction template on session change.

#### Scenario: Template location and frontmatter
- **WHEN** checking for startup instructions
- **THEN** look for `_startup.md` in project templates directory
- **AND** template SHALL have `requires-startup-instruction: true` in frontmatter
- **AND** template SHALL have `type: agent/instruction` in frontmatter

#### Scenario: Template always rendered
- **WHEN** `on_session_changed()` event fires
- **THEN** listener SHALL **always** attempt to render `_startup.md`
- **AND** template filtering via `requires-startup-instruction: true` is automatic
- **AND** no conditional logic needed before rendering

#### Scenario: Priority parameter for queue_instruction
- **WHEN** queueing an instruction
- **THEN** `queue_instruction()` SHALL accept optional `priority: bool = False` parameter
- **AND** when `priority=True`, insert instruction at front of queue (index 0)
- **AND** when `priority=False`, append to end of queue (existing behavior)

#### Scenario: Template rendering with flag set
- **WHEN** listener renders `_startup.md`
- **AND** the `startup-instruction` flag is set and non-empty
- **THEN** template passes `requires-startup-instruction` check
- **AND** render with `{{feature_flags.startup-instruction}}` variable containing flag value
- **AND** if rendered content is non-blank, call `queue_instruction(content, priority=True)`
- **AND** instruction is **fire-and-forget** (queued for next dispatch, no agent acknowledgment expected)

#### Scenario: Template filtered when flag not set
- **WHEN** listener renders `_startup.md`
- **AND** the `startup-instruction` flag is not set or empty
- **THEN** template is filtered by `requires-startup-instruction: true` directive
- **AND** rendering returns None
- **AND** no instruction is queued

#### Scenario: Blank content not queued
- **WHEN** `_startup.md` renders to blank content
- **THEN** do not queue any instruction
- **AND** continue normal session operation

#### Scenario: Session change trigger
- **WHEN** `get_or_create_session()` creates a new session
- **OR** session switches to different project
- **THEN** session SHALL notify all class-level listeners
- **AND** `StartupInstructionListener` SHALL receive `Session` instance
- **AND** listener SHALL attempt to render `_startup.md` for that session
- **AND** if content is non-blank, call `queue_instruction(content, priority=True)`

#### Scenario: Fire-and-forget instruction
- **WHEN** startup instruction is queued
- **THEN** instruction is sent via Result in next tool response
- **AND** no agent acknowledgment is expected
- **AND** agent processes instruction upon receipt

#### Scenario: No duplicate instructions per session
- **WHEN** a session change event fires
- **THEN** startup instruction SHALL only be queued once per event
- **AND** listener SHALL track processed sessions to avoid duplicates
