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

The system SHALL implement Session as a non-singleton class with at most one
current bound instance per validated client interaction owner. Different owners
SHALL NOT share a Session. A project switch SHALL replace that owner's bound
instance rather than change its existing instance's project/root identity.

Each Session SHALL own separate listeners, task state, instruction queues and
caches. These mutable resources SHALL NOT be copied or shared when an instance
is replaced. The outgoing instance SHALL be allowed to remain expiring while
its existing work completes.

A Session SHALL be allowed to exist before its project is bound. Its project
SHALL be absent rather than a placeholder. Unbound rendering SHALL still have
access to available agent/client information and global flags.

#### Scenario: Session creation before project binding
- **WHEN** a Session is created before project context is available
- **THEN** it SHALL have no bound Project and SHALL NOT load or persist a placeholder
- **AND** it SHALL NOT depend on ambient ContextVar ownership

#### Scenario: Unbound session rejects bound-only operations
- **GIVEN** a Session has no project binding
- **WHEN** an operation requires persisted project configuration
- **THEN** the defined no-project behaviour SHALL apply
- **AND** the operation SHALL NOT invent or persist project data

#### Scenario: Unbound placeholder rejects bound-only operations
- **GIVEN** no project has been bound
- **WHEN** a project-dependent operation is requested
- **THEN** there SHALL be no placeholder project to save
- **AND** the operation SHALL report the defined no-project condition

#### Scenario: Session creation with immediate project context
- **WHEN** an initial bind operation successfully resolves a project
- **THEN** its Session SHALL become the current bound instance for that owner
- **AND** later requests SHALL use that instance until replacement or expiry

#### Scenario: Unbound session exposes agent and client info for template rendering
- **GIVEN** an unbound Session has received agent/client bootstrap information
- **WHEN** a system template is rendered
- **THEN** the available agent information, client information and global flags SHALL be accessible
- **AND** rendering SHALL NOT require a placeholder or persisted Project

#### Scenario: Replacement owns fresh mutable state
- **GIVEN** an owner's current Session has caches, subscriptions and queued instructions
- **WHEN** a different project selection succeeds
- **THEN** the new bound Session SHALL own fresh mutable state
- **AND** the outgoing Session's mutable resources SHALL NOT become the replacement's resources

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

The system SHALL separate durable project configuration from ephemeral
interaction state. Session instances SHALL follow the lifecycle
`unbound -> bound -> expiring`, followed by disposal. An unbound instance that
never binds SHALL be disposed of when its request work completes.

Unbound request work SHALL be ephemeral. A bound instance SHALL be retained
under its validated public interaction ID only after successful project binding.
A switch SHALL publish a fresh bound instance under that same ID and move the
outgoing instance to expiring. An expiring instance SHALL never become current
again.

Modern interactions SHALL use a validated explicit FastMCP `session_id`.
Retained legacy connections that omit the argument SHALL continue using public
connection identity as their compatibility owner. Modern unbound requests
SHALL NOT gain cross-request state through that fallback.

There SHALL be at most one expiring instance per public ID. A switch received
while that ID has an expiring instance SHALL fail without replacing, queueing
or modifying either existing instance.

Every admitted request and listener/task execution SHALL retain its original
Session instance through completion. Existing work in an expiring Session SHALL
be permitted to finish, including configuration writes to its original project.
New requests and client replies SHALL resolve the current bound Session only.
Expiring instances SHALL receive no new project scheduling or configuration
notifications. Their owned resources SHALL be disposed of after admitted work
finishes, and their expiring entry SHALL then be removed.

Guide interaction state SHALL remain in memory and SHALL NOT be restored after
a server restart. Global configuration storage and its locking remain shared.

#### Scenario: Session persists from unbound to bound state
- **GIVEN** an ephemeral Session has no project
- **WHEN** its initial binding succeeds
- **THEN** that instance SHALL be promoted to the current bound Session
- **AND** its owned bootstrap state SHALL remain attached
- **AND** project-specific runtime work SHALL initialise for the bound project

#### Scenario: Unbound state suppresses project events
- **GIVEN** a Session has no project binding
- **WHEN** an unbound request is handled
- **THEN** project-load and project-switch events SHALL NOT run
- **AND** its first successful bind SHALL use normal initial-bound activation

#### Scenario: Modern request resumes a live interaction
- **GIVEN** the server is running and an interaction has a current bound Session
- **WHEN** a request supplies its valid public session ID
- **THEN** it SHALL resolve the current bound instance without requiring the original connection object
- **AND** it SHALL observe that instance's root and configuration

#### Scenario: Request has no project context
- **WHEN** an interaction has neither a valid root binding nor a successful initial bind
- **THEN** no project configuration SHALL be persisted merely to handle the request
- **AND** project-dependent operations SHALL use the defined no-project behaviour

#### Scenario: Unbound request completes
- **GIVEN** a request and its nested work use an unbound Session
- **WHEN** that work finishes without binding
- **THEN** the ephemeral instance SHALL be cleaned up
- **AND** it SHALL NOT be retained for a later request under the same owner ID

#### Scenario: Expiry does not interrupt an active request
- **GIVEN** a current bound Session has an in-flight request
- **WHEN** idle expiry is evaluated
- **THEN** idle expiry SHALL NOT dispose of that instance
- **AND** its last-used time SHALL reflect completion of its own final request

#### Scenario: Old request completes after replacement
- **GIVEN** a request began on an instance now expiring
- **WHEN** it completes after a replacement is current
- **THEN** completion SHALL release the old instance's request ownership only
- **AND** it SHALL NOT republish the old instance or change the replacement's request accounting

#### Scenario: Existing work saves its original project
- **GIVEN** an admitted operation belongs to an expiring Session
- **WHEN** it saves its original project's configuration
- **THEN** the save SHALL remain permitted through normal shared configuration locking
- **AND** it SHALL NOT be redirected to the replacement's project or rejected solely because the Session is expiring
- **AND** normal publication SHALL still reach active users of the saved configuration

#### Scenario: Follow-up client reply after a switch
- **GIVEN** a project switch has published a replacement under the same public ID
- **WHEN** the client submits another request, including a file or command reply
- **THEN** that request SHALL use the current bound Session and project
- **AND** the system SHALL NOT route it to an expiring Session or require a historical binding token

#### Scenario: Another switch while the ID is expiring
- **GIVEN** the public ID already has an expiring Session
- **WHEN** any further switch is requested for that ID
- **THEN** the switch request SHALL fail explicitly before changing either instance
- **AND** it SHALL NOT create another expiring instance or enqueue a switch
- **AND** the existing bound and expiring Sessions SHALL remain unchanged

#### Scenario: Expiring work finishes
- **GIVEN** an expiring Session has stopped admitting new work
- **WHEN** all its admitted work has completed
- **THEN** its listeners, tasks, timers, queues and caches SHALL be disposed of
- **AND** its expiring entry SHALL be removed
- **AND** a later valid switch for that public ID SHALL be permitted

#### Scenario: Cleanup is incomplete
- **GIVEN** disposal of an expiring Session fails
- **WHEN** cleanup reports that failure
- **THEN** it SHALL NOT silently restore the old instance as current
- **AND** the system SHALL NOT silently admit another expiring instance under that ID

#### Scenario: Outgoing cleanup does not control the switch response
- **GIVEN** a switch has successfully published its replacement
- **WHEN** the outgoing instance becomes eligible for disposal
- **THEN** runtime SHALL own and track disposal independently of request completion
- **AND** cleanup latency or failure SHALL NOT replace the successful switch response
- **AND** a failed disposal SHALL remain registered and be reported separately

#### Scenario: Idle disposal retains ownership
- **WHEN** idle expiry selects a bound instance
- **THEN** it SHALL use the same expiring lifecycle and retain failed disposal
- **AND** it SHALL skip an owner that already has an expiring instance
- **AND** a pending idle disposal SHALL prevent a new initial binding for that owner

#### Scenario: One Session cleanup fails during runtime shutdown
- **GIVEN** runtime owns unbound, bound or expiring Sessions
- **WHEN** one Session's cleanup raises during shutdown
- **THEN** cleanup SHALL still be attempted for every remaining instance
- **AND** runtime registries and shared services SHALL be shut down before reporting the failure

#### Scenario: Concurrent contexts are isolated
- **GIVEN** requests belong to different interaction owners or concrete Session instances
- **WHEN** their work overlaps
- **THEN** their listeners, transient state and project bindings SHALL remain instance-owned
- **AND** completing one request SHALL NOT replace another's active context

#### Scenario: Subagent uses the same root
- **WHEN** a subagent binds its own interaction to the same root as a parent
- **THEN** the interactions SHALL have separate Sessions and task state
- **AND** they SHALL be permitted to use the same durable project configuration
- **AND** their pending instructions, timers and caches SHALL NOT be shared

#### Scenario: Parent and subagent use different session IDs
- **WHEN** a parent and subagent use separate validated IDs
- **THEN** their current and expiring Sessions SHALL remain separate
- **AND** the system SHALL NOT infer shared ownership from names, roots or process ancestry

### Requirement: Explicit Root Binding and Switching

The system SHALL establish an interaction's initial client root through
`set_project(path)` and validated selected-root state. Initial binding SHALL
require an absolute client path and SHALL reject name-only input or a second
initial binding, including an unchanged path.

Each bound Session SHALL retain its root and configuration identity unchanged
for its lifetime. `switch_project(name | path)` SHALL select a fresh current
Session when the requested selection differs: name-only keeps the interaction's
current root; path-only uses the normalised path and its basename. The public
interaction owner and session ID SHALL remain unchanged.

Path normalisation SHALL be lexical and SHALL NOT require client paths to exist
on the server or resolve client filesystem links. Configuration identity SHALL
remain `(name, bound_root_hash)`; both the generated configuration key and stored
hash SHALL match. Name-only, malformed, missing-hash and mismatched-hash stored
entries SHALL be ignored without legacy configuration migration.

#### Scenario: New interaction selects its first root
- **WHEN** an unbound interaction successfully calls set_project with an absolute client path
- **THEN** its initial Session SHALL bind to that root
- **AND** other interactions SHALL remain unchanged

#### Scenario: New interaction selects a different root
- **GIVEN** another interaction already has a root binding
- **WHEN** a new interaction selects a different root
- **THEN** the new interaction SHALL receive its own binding
- **AND** the prior interaction SHALL remain unchanged

#### Scenario: Initial binding requires an absolute path
- **WHEN** an unbound interaction supplies a name, relative path or missing path
- **THEN** the selection SHALL be rejected without binding a project
- **AND** guidance SHALL request an absolute client root through set_project

#### Scenario: Agent supplies a project name rather than a path
- **WHEN** an unbound interaction supplies a project name instead of an initial path
- **THEN** the system SHALL reject the selection without creating a project
- **AND** it SHALL direct the agent to provide the absolute root as path

#### Scenario: Second initial binding is rejected
- **GIVEN** an interaction is already bound
- **WHEN** set_project is called again, including for its current path
- **THEN** it SHALL fail without replacing or rebinding the current Session

#### Scenario: Name-only selection retains the root
- **GIVEN** the interaction is bound and no instance for its ID is expiring
- **WHEN** a different configuration name is selected
- **THEN** a fresh current Session SHALL use that name with the existing root
- **AND** the outgoing instance SHALL retain its original name and root

#### Scenario: Configuration selection does not change root binding
- **GIVEN** a bound interaction selects a different configuration name
- **WHEN** the switch succeeds
- **THEN** the replacement SHALL use the prior root's hash with the supplied name
- **AND** the interaction's root path SHALL remain unchanged

#### Scenario: Path selection replaces the bound Session
- **GIVEN** the interaction is bound and no instance for its ID is expiring
- **WHEN** a different root is selected successfully
- **THEN** the replacement SHALL use the normalised root and its basename configuration
- **AND** the public session ID SHALL remain unchanged
- **AND** the outgoing Session SHALL retain its original binding while expiring

#### Scenario: Same selection without pending expiry
- **GIVEN** no Session for the public ID is expiring
- **WHEN** a valid switch resolves to the current name and root
- **THEN** the operation SHALL succeed without replacement or task restart

#### Scenario: Root changes initialise fresh project state
- **GIVEN** the old and new roots can have the same basename
- **WHEN** the interaction switches roots
- **THEN** the replacement SHALL initialise its own tasks, instructions and caches
- **AND** correctness SHALL NOT depend on clearing or resetting the outgoing Session before reuse

#### Scenario: Same configuration name at different roots
- **WHEN** interactions at different roots select the same name
- **THEN** the resulting configuration identities SHALL have their respective root hashes
- **AND** their configurations SHALL remain independent

#### Scenario: Same name has a different or missing hash
- **WHEN** a stored entry with the requested name has a missing or mismatched root hash
- **THEN** it SHALL NOT be selected by name alone
- **AND** only the correctly keyed configuration SHALL be selected or created

#### Scenario: Background work has no client request
- **WHEN** background work executes without a current client request
- **THEN** it SHALL NOT discover or select client roots
- **AND** it SHALL use only its explicitly owned project state

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
