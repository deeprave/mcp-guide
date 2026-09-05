# request-context Specification

## Purpose

Provide one framework-neutral application context for every Guide request, so
application code uses resolved Guide state without depending on FastMCP internals.

## Requirements

### Requirement: Resolved Application Request Context
The system SHALL construct a framework-neutral RequestContext for every tool,
prompt, and resource invocation before application handler execution. The context
SHALL contain the client `session_id`, resolved Guide Session, and response metadata
facilities. When bound it SHALL contain root and Project values. Protocol revision,
request identity, owner keys, and client metadata SHALL remain transport-boundary
details. Application handlers SHALL NOT require a raw FastMCP context to resolve or
select Guide state.

#### Scenario: Context-bearing application invocation
- **WHEN** a public MCP operation enters the Guide application boundary
- **THEN** the boundary SHALL validate and resolve its interaction before invoking application code
- **AND** the application handler SHALL receive the resolved RequestContext
- **AND** no nested application operation SHALL create or select another Session for that request

### Requirement: Bound Root and Active Project Access
When an interaction is bound, RequestContext SHALL expose the immutable bound-root
identity and the exact immutable Project object currently selected by its Session.
The Project reference SHALL include the selected configuration's categories,
collections, flags, permissions, exports, and configuration identity. The system
SHALL represent unbound interactions with absent root and project values.

#### Scenario: Bound request reads active project data
- **WHEN** a request is dispatched for an interaction bound to a project root
- **THEN** its RequestContext SHALL expose that root's path, name, and hash
- **AND** its Project reference SHALL be the Session's currently active Project
- **AND** an application handler SHALL read project configuration without a second Session lookup

#### Scenario: Project configuration changes during a request
- **WHEN** an operation updates the active Project configuration
- **THEN** it SHALL perform the update through the owning Session
- **AND** `RequestContext.project` SHALL return that Session's current Project
- **AND** it SHALL NOT snapshot a prior Project object onto the request context

#### Scenario: Bound root tracks in-request bind
- **WHEN** an operation binds the Session to a project root during a request
- **THEN** `RequestContext.root` SHALL expose that Session's current bound-root identity
- **AND** `RequestContext.is_bound` SHALL become true without reconstructing the context

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
