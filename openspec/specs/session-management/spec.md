## Purpose

Define Guide Session lifecycle, configuration access, and interaction binding.

## Requirements

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
The system SHALL separate durable project configuration from request-scoped and
cross-request interaction state. Correct request handling SHALL NOT require one
mutable Session instance to exist for the lifetime of a client connection.

Project configuration and project-scoped services SHALL be resolved using an explicit
request context and owner key. Root binding and active configuration-project selection
are distinct state. A context-owned in-memory Guide Session SHALL be selected by a
validated FastMCP session ID for the lifetime of the running MCP server only after it
has successfully bound a project; it SHALL NOT be restored after an MCP server restart.
An unbound request MAY use one request-local Session for its complete handler, but that
Session SHALL be discarded when the handler completes.

The preferred owner key is a validated explicit FastMCP `session_id`. Retained legacy
connections that do not supply that argument SHALL use public `ctx.session_id` as a
compatibility owner key. This fallback SHALL NOT be used to create cross-request
modern state.

#### Scenario: Session persists from unbound to bound state
- **WHEN** a session is created before project context exists and later binds to a real project
- **THEN** the same Session instance is retained
- **AND** runtime listeners and state remain attached to that instance
- **AND** project-scoped data is initialized only after binding

#### Scenario: Unbound state suppresses project events
- **WHEN** the session is still using the placeholder project
- **THEN** project-related load or switch events SHALL NOT be fired
- **AND** the first real bind SHALL use the existing initial project-load notification semantics

#### Scenario: Modern request resumes a live interaction
- **WHEN** a valid modern request supplies the minted FastMCP `session_id` for a
  still-running MCP server
- **THEN** the system SHALL resolve the same in-memory root binding and active
  configuration selection without a live connection object
- **AND** project-bound behaviour SHALL be equivalent to a request after valid
  `set_project(path)` and configuration selection

#### Scenario: Request has no project context
- **WHEN** an interaction has neither valid selected-root state nor an explicit `set_project(path)` call
- **THEN** the system SHALL create no persisted project configuration as a side effect
- **AND** project-bound operations SHALL use the defined no-project behavior

#### Scenario: Unbound request completes
- **WHEN** a request uses a Session that has not bound a project
- **THEN** the Session SHALL be shared by nested work within that request only
- **AND** GuideRuntime SHALL clean it up when that request completes
- **AND** it SHALL not be available to a later request with the same owner ID

#### Scenario: Expiry does not interrupt an active request
- **WHEN** a Session has an in-flight request
- **THEN** idle expiry SHALL NOT clean it up
- **AND** its idle timestamp SHALL be recorded after the final in-flight request completes

#### Scenario: One Session cleanup fails during runtime shutdown
- **WHEN** Session cleanup raises while GuideRuntime is stopping
- **THEN** GuideRuntime SHALL still attempt cleanup for every remaining Session
- **AND** it SHALL clear its registries and stop shared runtime services before reporting the failure

#### Scenario: Concurrent contexts are isolated
- **WHEN** two requests carry different explicit owner or project identities
- **THEN** their transient state, listeners, and project-scoped data SHALL remain isolated
- **AND** one request SHALL NOT replace another request's active project context

#### Scenario: Subagent uses the same root
- **WHEN** a subagent binds the same root as a parent agent but has a different Session owner
- **THEN** it MAY resolve the same durable Guide configuration
- **AND** it SHALL receive a separate Guide Session and separate TaskManager state
- **AND** it SHALL NOT receive the parent's pending instructions, timers, caches, or active configuration selection

#### Scenario: Parent and subagent use different session IDs
- **WHEN** a parent and subagent use separate FastMCP session IDs
- **THEN** they SHALL resolve separate Guide Sessions
- **AND** the system SHALL not infer shared or delegated state from client name,
  root, or process ancestry

### Requirement: Explicit Immutable Root Binding
The system SHALL bind an interaction's client filesystem root only through
`set_project(path)` and validated selected-root state. The operation SHALL require an
absolute client filesystem argument named `path`, derive root identity from it, and
reject name-only selection. It SHALL not request roots from a client, process a roots
change, or mutate an already selected root. `set_project(path)` SHALL be rejected
when the interaction is already root-bound, including when `path` is unchanged.

`switch_project(name)` SHALL remain a separate active Guide configuration-project
operation. It may change that configuration selection without changing the bound root.
Configuration identity SHALL use `(name, bound_root_hash)`: `set_project(path)` uses
the path basename as its default name, and `switch_project(name)` uses the existing
bound root hash. It SHALL reject a full path argument rather than interpreting it as a
root change. Resolution SHALL require both the generated `<project-name>-<hash>` key
and stored configuration hash to match the bound root hash; name-only, malformed,
missing-hash, and mismatched-hash entries SHALL be ignored. The system SHALL provide
no legacy configuration migration; it SHALL select or create only the correct key for
the bound root. This is intentional: the `<project-name>-<hash>` format is
long-established, and creating a fresh configuration is an acceptable outcome when an
older entry is ignored.

#### Scenario: New interaction selects a different root
- **WHEN** an agent begins a new interaction and explicitly selects a different root path
- **THEN** the system SHALL bind the new interaction to that root
- **AND** it SHALL leave the prior interaction's root state unchanged

#### Scenario: Agent supplies a project name rather than a path
- **WHEN** an unbound interaction calls project selection with a name, relative path, or no path
- **THEN** the system SHALL reject the selection without creating or binding a project
- **AND** it SHALL direct the agent to provide the absolute client filesystem root as `path`

#### Scenario: Configuration selection does not change root binding
- **WHEN** a root-bound interaction calls `switch_project` with a configuration name
- **THEN** the system SHALL change the active configuration selection if valid
- **AND** it SHALL retain the interaction's bound root path unchanged
- **AND** it SHALL resolve the configuration using that root's hash and the supplied name

#### Scenario: Same configuration name at different roots
- **WHEN** interactions bound to different root paths each select the same configuration name
- **THEN** the system SHALL resolve configuration identities with different root hashes
- **AND** the configurations SHALL remain independent

#### Scenario: Same name has a different or missing hash
- **WHEN** an interaction selects a configuration name for which stored entries have a different or missing hash
- **THEN** the system SHALL NOT select any of those entries by name
- **AND** it SHALL ignore those entries and resolve or create only the correctly keyed
  configuration for the bound root hash

#### Scenario: Background work has no client request
- **WHEN** background work runs without a current request context
- **THEN** it SHALL NOT issue a server-to-client roots request or use root data
- **AND** it SHALL only operate on explicitly owned project state

### Requirement: Shared Durable Configuration Publication
`GuideRuntime` SHALL be the process-global Guide state and SHALL create one plainly
named `ConfigManager` at runtime startup for the shared configuration-file resource,
replacing the responsibility currently represented by the class-level
`Session._ConfigManager`. ConfigManager SHALL include persistence, a lock, one complete
validated configuration image, and one configuration-file watchdog. Every read, write,
watchdog refresh, diff, and publication SHALL have exclusive access to that image. The
existing cross-process file lock SHALL remain in use for disk access.
A Session SHALL consume
the runtime-owned manager or its configuration view; it SHALL NOT own, reconfigure, or
watch the shared configuration-file resource. Runtime application code SHALL perform
configuration operations through a Session and SHALL NOT create another ConfigManager
or access the runtime-owned manager as a general-purpose service. On a successful
in-process write, ConfigManager SHALL update its complete cached snapshot and publish
the resulting diff before returning success:
global feature-flag changes SHALL be published to every active Guide Session, and a
project-configuration change SHALL be published to every active Session whose active
configuration has the exact same `(name, root_hash)` identity. Detected external
configuration-file changes SHALL be published using the same scope when the watchdog
observes them. On a watchdog event, ConfigManager SHALL reload and compare the complete
configuration snapshot, atomically replace its cache before publication, and suppress
publication when the observed snapshot is unchanged.

#### Scenario: One session changes a global feature flag
- **WHEN** a Session successfully persists a global feature-flag change
- **THEN** ConfigManager SHALL publish it immediately to every
  active Guide Session in that runtime
- **AND** no Session SHALL require a new request or a separate configuration reload to
  observe the change

#### Scenario: One session changes a project configuration
- **WHEN** a Session successfully persists a project-configuration change for a
  particular `(name, root_hash)` identity
- **THEN** ConfigManager SHALL publish it immediately to every
  active Session using that exact configuration identity
- **AND** it SHALL not publish the project-specific change to Sessions using another
  name or root hash

#### Scenario: Configuration changes outside the runtime
- **WHEN** ConfigManager's watchdog observes a configuration-file change made by
  another runtime, Session, or external process
- **THEN** it SHALL reload and atomically replace its complete shared snapshot before
  publishing the relevant global and project diffs to active Sessions
- **AND** it SHALL not leave a per-Session configuration watcher to produce divergent
  state

#### Scenario: Change affects a configuration used by another project
- **WHEN** a configuration-file change modifies a project configuration that is not
  active in the Session that made or observed the change
- **THEN** ConfigManager SHALL still include that project configuration in its complete
  cached snapshot and diff
- **AND** it SHALL publish the change to every active Session using that exact
  `(name, root_hash)` identity

#### Scenario: Watchdog observes the runtime's already-published write
- **WHEN** the configuration-file watchdog observes a write whose complete snapshot
  already equals ConfigManager's cache
- **THEN** ConfigManager SHALL not publish a duplicate change notification

### Requirement: ConfigManager-Owned Immutable Docroot
ConfigManager SHALL resolve docroot once at startup and own the resulting effective
docroot for its full lifecycle. Docroot SHALL NOT be Session-owned and SHALL NOT be
changed by a Session operation, an in-process configuration update, or a configuration
watchdog publication. If ConfigManager observes a persisted docroot value different
from the running effective docroot, the running ConfigManager SHALL continue using its
startup-resolved docroot and a restart SHALL be required to adopt the new value.
GuideRuntime MAY expose this value, but SHALL NOT cache or duplicate it.

#### Scenario: Session attempts to change docroot
- **WHEN** a Session attempts an operation that would change docroot while ConfigManager
  is running
- **THEN** the operation SHALL be rejected without changing ConfigManager's effective
  docroot

#### Scenario: External configuration change includes a new docroot
- **WHEN** ConfigManager's watchdog observes a persisted configuration with a
  different docroot
- **THEN** the running ConfigManager SHALL retain its startup-resolved effective docroot
- **AND** a restart SHALL be required before that persisted value can become effective

### Requirement: Session Does Not Own Process Docroot Or Global Flags
A Session SHALL NOT own process document-root or global feature-flag state.
Callers that need those values SHALL obtain them from the process runtime.
A Session MAY keep project-scoped flag access for the bound project.

#### Scenario: Docroot is requested
- **WHEN** application code needs the process document root
- **THEN** it SHALL obtain it from the process runtime
- **AND** it SHALL NOT treat Session as the owner of that path

#### Scenario: Global flags are requested
- **WHEN** application code needs global feature flags
- **THEN** it SHALL obtain them from the process runtime
- **AND** Session SHALL NOT expose a global-flag ownership API

#### Scenario: Project flags remain interaction-scoped
- **WHEN** application code needs flags stored on the bound project
- **THEN** it SHALL continue to use the Session's bound project configuration

#### Scenario: Session configuration accessor
- **WHEN** Session code needs the process configuration service for project
  operations
- **THEN** it SHALL obtain that service from its process runtime
- **AND** it SHALL NOT import the configuration-service class
