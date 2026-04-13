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

### Requirement: Lazy Config Loading
The system SHALL load project config lazily via async method.

The system SHALL support deferred project binding, where a Session may begin with a
placeholder project and load the real persisted project only when a context-bearing
operation first requires it.

#### Scenario: First config access after deferred creation
- **WHEN** a session exists with a placeholder project and a project-dependent operation is invoked with sufficient context
- **THEN** the session resolves the real project identity
- **AND** loads the persisted project config
- **AND** replaces the placeholder with the real project
- **AND** subsequent accesses use the bound project

#### Scenario: Valid MCP context triggers binding
- **WHEN** a tool, prompt, or resource access provides valid MCP context
- **AND** the session is still using a placeholder project
- **AND** the cached roots are sufficient to resolve a project name
- **THEN** the session SHALL bind to the resolved real project during that access
- **AND** later accesses SHALL observe the bound project

#### Scenario: Explicit project selection binds unbound session
- **WHEN** a session exists with a placeholder project and `set_project(project_name)` is invoked
- **THEN** the session binds directly to the requested project name
- **AND** it SHALL NOT require prior auto-resolution from MCP roots or `PWD`
- **AND** the requested project config is loaded or created using the explicit project name

#### Scenario: Placeholder project is never persisted
- **WHEN** a session has not yet bound a real project
- **THEN** the placeholder project SHALL NOT be written to config storage
- **AND** no new persisted project SHALL be created from placeholder state alone

#### Scenario: Persistence boundary rejects unbound project
- **WHEN** a config-write or persistence path receives the placeholder project
- **THEN** that boundary SHALL either raise `NoProjectError` or intentionally no-op, according to the call site's defined behavior
- **AND** it SHALL NOT serialize, save, rename, or otherwise persist the placeholder as a real project

### Requirement: Session Lifecycle Management
The system SHALL maintain a single session for the lifetime of the client connection.

#### Scenario: Session persists from unbound to bound state
- **WHEN** a session is created before project context exists and later binds to a real project
- **THEN** the same Session instance is retained
- **AND** runtime listeners and state remain attached to that instance
- **AND** project-scoped data is initialized only after binding

#### Scenario: Unbound state suppresses project events
- **WHEN** the session is still using the placeholder project
- **THEN** project-related load or switch events SHALL NOT be fired
- **AND** the first real bind SHALL use the existing initial project-load notification semantics

### Requirement: Unified Session Access
The system SHALL provide a single `get_session()` async function that replaces both
`get_or_create_session` and `get_current_session`.

#### Scenario: Signature
- **WHEN** `get_session` is defined
- **THEN** its signature SHALL be `async def get_session(ctx=None, *, project_name=None, _config_dir_for_tests=None) -> Session`
- **AND** it SHALL never return None

#### Scenario: Startup access before context
- **WHEN** `get_session()` is called without `ctx` during server startup
- **THEN** it MAY return a session with a placeholder project
- **AND** it SHALL NOT require server cwd as a fallback for client project resolution
- **AND** project-bound operations SHALL require a later binding step
