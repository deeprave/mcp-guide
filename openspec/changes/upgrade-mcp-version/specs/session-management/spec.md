## MODIFIED Requirements

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

## ADDED Requirements

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
