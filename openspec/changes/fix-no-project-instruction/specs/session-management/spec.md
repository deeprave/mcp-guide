## MODIFIED Requirements

### Requirement: Session Non-Singleton
The system SHALL implement Session as a non-singleton class. One Session exists per
client connection. In HTTP transport, each concurrent client has its own Session via
ContextVar task isolation.

Each Session instance SHALL own its own listener list and manage listener registration
as instance methods (`add_listener`, `remove_listener`, `clear_listeners`).

Listeners SHALL NOT be shared across Session instances.

Each Session instance SHALL be allowed to exist before its real project is bound.
Before binding, the session SHALL still expose a concrete placeholder project object
rather than `None`.

The placeholder project SHALL be a wrapper around project behavior that mimics safe
real-project operations where appropriate and raises an explicit exception for
operations that require a real bound project.

When no project is bound, the session SHALL still provide sufficient context for
`_system/` template rendering: agent info, client info, and global feature flags
SHALL be accessible without a bound project.

#### Scenario: Session creation before project binding
- **WHEN** `get_session()` or equivalent startup logic creates a session before client project context is available
- **THEN** a Session instance is created and stored in the ContextVar
- **AND** the session contains a placeholder project object
- **AND** the session does not require a real `Project` constructor argument at creation time
- **AND** no persisted project config is loaded yet

#### Scenario: Unbound placeholder rejects bound-only operations
- **WHEN** code calls a project operation on the placeholder that requires a real persisted project
- **THEN** the placeholder SHALL raise `NoProjectError`, or allow an existing `NoProjectError` path to bubble
- **AND** it SHALL NOT silently invent or persist project data

#### Scenario: Session creation with immediate project context
- **WHEN** `get_session(ctx)` is called and project identity can be resolved immediately
- **THEN** a new Session is created
- **AND** the real project is bound during session creation
- **AND** subsequent `get_session()` calls return the same instance

#### Scenario: Unbound session exposes agent and client info for template rendering
- **WHEN** a session exists with no bound project
- **AND** agent bootstrap data has been received
- **THEN** `session.agent_info` SHALL be accessible
- **AND** `get_template_contexts()` SHALL return a context including `agent.*` and `client.*`
- **AND** template rendering of `_system/` templates SHALL succeed

---

## ADDED Requirements

### Requirement: Async factory for no-project result
The system SHALL provide an async factory `make_no_project_result(ctx)` in
`result_constants.py` that produces a `Result` with a rendered `_project-root`
instruction when possible, falling back to the static `RESULT_NO_PROJECT` when not.

The factory SHALL:
1. Attempt to obtain a session from `ctx` via `get_session(ctx)`
2. If a session is available and no project is bound, render `_system/_project-root`
   and construct `Result.failure(error_type=ERROR_NO_PROJECT, instruction=<rendered>)`
3. If no session is available (ValueError), return the static `RESULT_NO_PROJECT`
4. If rendering raises for any reason, log a warning and return `RESULT_NO_PROJECT`

`_check_project_bound()` in `core/tool_decorator.py` SHALL delegate to the factory
on the unbound-project path, replacing the direct `RESULT_NO_PROJECT.to_json_str()`
reference with `(await make_no_project_result(ctx)).to_json_str()`.

The static `INSTRUCTION_NO_PROJECT` and `RESULT_NO_PROJECT` constants SHALL be
retained as the factory's internal fallback and SHALL NOT be removed.

#### Scenario: Unbound session returns rendered instruction
- **WHEN** a tool with `requires_project=True` is called
- **AND** a session exists but no project is bound
- **THEN** `_check_project_bound()` renders `_system/_project-root`
- **AND** returns a `Result.failure` JSON string with the rendered template as instruction
- **AND** the instruction contains guidance on git worktree detection and CWD fallback

#### Scenario: No session falls back to static instruction
- **WHEN** a tool with `requires_project=True` is called
- **AND** `get_session(ctx)` raises ValueError (no session)
- **THEN** `_check_project_bound()` returns `RESULT_NO_PROJECT.to_json_str()`
- **AND** the static fallback instruction is used

#### Scenario: Rendering failure falls back to static instruction
- **WHEN** a tool with `requires_project=True` is called
- **AND** a session exists but no project is bound
- **AND** `render_content("_project-root", "_system")` raises an exception
- **THEN** `_check_project_bound()` catches the exception
- **AND** logs a warning
- **AND** returns `RESULT_NO_PROJECT.to_json_str()` as fallback

#### Scenario: Bound session is unaffected
- **WHEN** a tool with `requires_project=True` is called
- **AND** a project is bound to the session
- **THEN** `_check_project_bound()` returns `None`
- **AND** no template rendering occurs
- **AND** the tool proceeds normally
