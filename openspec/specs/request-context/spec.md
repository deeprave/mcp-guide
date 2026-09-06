# request-context Specification

## Purpose

Provide one framework-neutral application context for every Guide request, so
application code uses resolved Guide state without depending on FastMCP internals.

## Requirements

### Requirement: Resolved Application Request Context

The system SHALL construct a framework-neutral RequestContext for each tool,
prompt and resource invocation before application execution. It SHALL contain
the public session ID, the resolved concrete Guide Session and response metadata
facilities. Bound contexts SHALL expose their Session's root and Project.

Protocol revision, identity validation, owner keys and connection metadata SHALL
remain transport-boundary responsibilities. Application handlers SHALL NOT
require raw FastMCP context to select Guide state. The selected Session instance
SHALL remain owned by that request through completion, even if runtime replaces
the current instance for the same public ID.

Nested work SHALL use the explicitly supplied context or Session. A deliberate
project switch SHALL return its replacement explicitly for switch-result
processing; it SHALL NOT silently redirect other existing request contexts.

#### Scenario: Context-bearing application invocation
- **WHEN** a public MCP operation enters the application boundary
- **THEN** the boundary SHALL validate the interaction and resolve one concrete Session
- **AND** its request context and lifetime accounting SHALL refer to that same instance
- **AND** nested operations SHALL NOT independently resolve another Session by ID

#### Scenario: Existing request crosses a replacement
- **GIVEN** a request holds the outgoing Session
- **WHEN** a project switch publishes a replacement under the same public ID
- **THEN** the existing request SHALL retain its original Session reference
- **AND** a subsequently admitted request SHALL resolve the replacement

#### Scenario: Switch response uses the replacement explicitly
- **WHEN** a project switch publishes a new bound Session
- **THEN** its result SHALL describe the replacement's project and root
- **AND** any initial-bound instructions attached to that result SHALL come from the replacement
- **AND** completion SHALL still release the outgoing instance captured by the initiating request

### Requirement: Bound Root and Active Project Access

A bound RequestContext SHALL expose its Session's immutable root identity and
current Project configuration, including categories, collections, flags,
permissions, exports and configuration identity. Unbound contexts SHALL expose
absent root and project values.

Project configuration values may change through the owning Session, but a
bound Session's project/root identity SHALL NOT be redirected by a switch.
Replacing runtime's current instance SHALL NOT make an existing context read
the replacement's state.

#### Scenario: Bound request reads active project data
- **WHEN** an admitted request reads bound project data
- **THEN** its context SHALL expose its captured Session's root path, name and hash
- **AND** project access SHALL use that Session without another ID lookup

#### Scenario: Project configuration changes during a request
- **WHEN** an operation updates its Session's project configuration
- **THEN** it SHALL perform the update through that Session
- **AND** subsequent project access through its context SHALL see that Session's current configuration
- **AND** the context SHALL NOT keep a separate stale Project snapshot

#### Scenario: Bound root tracks in-request bind
- **GIVEN** the context holds an initially unbound Session
- **WHEN** that instance successfully receives its first binding
- **THEN** the existing context SHALL expose the root and become bound
- **AND** rebuilding the context SHALL NOT be necessary

#### Scenario: Old context remains attached to the original project
- **GIVEN** an admitted request's Session has become expiring
- **WHEN** that request reads or updates project configuration
- **THEN** it SHALL still use its original project's identity
- **AND** a replacement under the same public ID SHALL NOT redirect its access

### Requirement: Request Context Helper Boundary
RequestContext SHALL provide narrow application-facing helpers for contained state that
would otherwise require raw transport context or ambient Session lookup. Helpers
SHALL delegate to the resolved Session or GuideRuntime as appropriate and SHALL fail
clearly when the required state is absent.

#### Scenario: Helper needs interaction-owned state
- **WHEN** an application helper needs task processing, rendering state, root data, or a runtime-owned configuration operation
- **THEN** it SHALL obtain that state through RequestContext or its resolved Session
- **AND** it SHALL NOT infer ownership from a ContextVar or raw FastMCP object

#### Scenario: Document path resolution
- **WHEN** an application operation needs a document-root-relative path
- **THEN** it SHALL obtain a sync resolver from RequestContext.get_docroot_resolver
- **AND** that resolver SHALL be supplied by GuideRuntime.get_docroot_resolver after awaiting the configured root once
- **AND** callers SHALL reuse that sync function for further joins so a hot path does not await per path
- **AND** the resolver SHALL reject paths that escape the document root
- **AND** an already-absolute path SHALL still be checked for containment
- **AND** the resolver SHALL NOT follow symlinks when checking containment
- **AND** the returned path SHALL be host-absolute after expanduser, expandvars, and resolve
- **AND** RequestContext SHALL NOT expose the configured document root as a path or accessor
- **AND** content formatters SHALL receive that resolver function, not a document-root path
- **AND** application code SHALL NOT resolve or join against the document root directly
- **AND** Session SHALL NOT resolve document paths
- **AND** Session SHALL NOT publish GuideRuntime

#### Scenario: Process runtime is independent of Session
- **WHEN** application code needs GuideRuntime
- **THEN** it SHALL call get_runtime()
- **AND** it SHALL NOT retrieve the runtime through a Session accessor

#### Scenario: Process runtime is a singleton
- **WHEN** the process starts
- **THEN** create_runtime() SHALL be the only site that constructs GuideRuntime
- **AND** get_runtime() SHALL return that installed instance
- **AND** create_runtime() SHALL raise if a process runtime is already installed
- **AND** start() SHALL reinstall this instance when the process slot is empty
- **AND** start() SHALL raise if a different process runtime is already installed
- **AND** stop() SHALL release the process runtime so a later create_runtime() may install a successor

#### Scenario: Security-boundary check needs the configured root
- **WHEN** an operation must compare a path against the configured document root
- **THEN** it MAY obtain that root through get_runtime().get_docroot
- **AND** application path joins and formatters SHALL still use the request-context resolver
