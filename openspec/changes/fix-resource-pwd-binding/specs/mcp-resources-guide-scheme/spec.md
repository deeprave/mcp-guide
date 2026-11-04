# Spec Delta

## MODIFIED Requirements

### Requirement: Request-Scoped Guide URI Resolution

The server SHALL obtain the requested `guide://` URI through the framework-neutral
resource request context. Resource resolution SHALL NOT depend on the internal shape
of a FastMCP request-context object.

The advertised Guide resource templates SHALL include an optional RFC 6570
`session_id` query variable. A native `resources/read` request with
`?session_id=<id>` SHALL pass that value through the same validated Session resolver
used by the shared tool-argument contract before content rendering or command
execution. It SHALL use the value as an opaque FastMCP Session ID, not a
Guide-generated or separately mapped identifier.

Native content resource requests SHALL require the explicit `session_id` query
variable in both protocol eras. A request that omits it SHALL return the defined
unbound guidance even when a retained connection already has a bound Session, unless
that request has just completed the eligible inherited-PWD bootstrap. The bootstrap
exception SHALL return its resulting Session ID for later resource URI queries.

#### Scenario: Guide content resource request

- **WHEN** a client reads a `guide://{collection}/{document}{?session_id}` resource through a negotiated modern request
- **THEN** the resource handler SHALL obtain the URI from the application request context
- **AND** it SHALL resolve the validated query `session_id` through the same request
  Session resolver as a tool call
- **AND** it SHALL delegate content resolution using the resulting project identity

#### Scenario: Session-sensitive template is read natively

- **WHEN** a resource template whose rendering depends on Session data is read with a
  valid `session_id` query value
- **THEN** its rendering SHALL observe the same bound Session state as
  `guide.read_resource` given that Session ID
- **AND** it SHALL not render using ambient process, global, or unrelated connection
  state

#### Scenario: Guide command resource request

- **WHEN** a client reads an underscore-prefixed
  `guide://_{command_path*}{?session_id}` command URI
- **THEN** the command parser SHALL receive the URI and request context through the resource adapter
- **AND** embedded response instructions SHALL be preserved in the protocol result

#### Scenario: Resource session identifier is unsafe

- **WHEN** a resource URI supplies an empty, overlong, or control-character-bearing
  `session_id` query value
- **THEN** the shared resolver SHALL reject it before Session lookup
- **AND** it SHALL not create a runtime Session entry or include the raw value in a
  user-visible diagnostic

#### Scenario: First resource request uses inherited-PWD bootstrap

- **GIVEN** stdio inherited-PWD bootstrap is enabled and the shared filesystem conditions are satisfied
- **WHEN** a client first reads a native `guide://` resource without `session_id`
- **THEN** the response SHALL succeed using the PWD-bound project
- **AND** it SHALL return the resulting `session_id` for use unchanged in later resource URI queries
