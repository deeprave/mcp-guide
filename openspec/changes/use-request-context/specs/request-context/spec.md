## Purpose

Provide one framework-neutral application context for every Guide request, so
application code uses resolved Guide state without depending on FastMCP internals.

## ADDED Requirements

### Requirement: Resolved Application Request Context
The system SHALL construct a framework-neutral RequestContext for every tool,
prompt, and resource invocation before application handler execution. The context
SHALL contain the validated interaction owner, protocol and client metadata, the
resolved Guide Session, and response metadata facilities. Application handlers SHALL
NOT require a raw FastMCP context to resolve or select Guide state.

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
- **AND** it SHALL use the replacement immutable Project returned by that operation for later work in the request
- **AND** it SHALL NOT mutate the prior Project object or a root identity

### Requirement: Request Context Helper Boundary
RequestContext SHALL provide application-facing helpers for contained state that
would otherwise require raw transport context or ambient Session lookup. Helpers
SHALL delegate to the resolved Session or GuideRuntime as appropriate and SHALL fail
clearly when the required state is absent.

#### Scenario: Helper needs interaction-owned state
- **WHEN** an application helper needs task processing, rendering state, root data, or a runtime-owned configuration operation
- **THEN** it SHALL obtain that state through RequestContext or its resolved Session
- **AND** it SHALL NOT infer ownership from a ContextVar or raw FastMCP object

